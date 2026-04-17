# /// script
# requires-python = ">=3.9,<3.13"
# dependencies = [
#     "typer",
#     "requests",
#     "cryptography",
# ]
# ///

"""
TGFW 卸载安装工具

通过串口服务器（telnet）远程完成 TGFW 的卸载与安装流程。
此工具主要供自动化 Agent 调用，输出格式简洁明了。

使用示例：
    uv run ngfwinstall_tool.py \
        --serial-url telnet://<IP_ADDRESS>:10008 \
        --package-url ftp://<IP_ADDRESS>/ngfw/images/V6R01C02B006/TGFW-xxx.tar.gz \
        --device-type DAS-TGFW-290 \
        --device-ip <IP_ADDRESS> \
        --password "Ngfw123!@#"
"""

import os
import re
import sys
import time
import base64
import logging
import warnings
from urllib.parse import urlparse

# telnetlib 在 Python 3.11+ 中被标记为 deprecated，但在 3.12 中仍可用
warnings.filterwarnings("ignore", category=DeprecationWarning)
import telnetlib  # noqa: E402

# 禁用 Typer Rich 输出，节省 Token（必须在 import typer 之前设置）
os.environ["TYPER_USE_RICH"] = "0"

import typer  # noqa: E402
import requests  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import padding  # noqa: E402

# 禁用 SSL 不安全请求的告警
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

# ==================== 常量定义 ====================

# 自定义 Shell 提示符标记，用于可靠检测命令完成
PROMPT_MARKER = "NGFW_INSTALLING> "

POST_INSTALL_USER = "root"
POST_INSTALL_PASS = "ngfw123!@#"


# 管理路由（固定配置）
MGMT_ROUTE = "ip route add <IP_ADDRESS>/23 via <IP_ADDRESS> metric 2"

# 健康检查相关
HEALTH_CHECK_VPP = "/opt/dbappsecurity/bin/health-check/vpp-health-check.sh"
HEALTH_CHECK_AGENT = "/opt/dbappsecurity/bin/health-check/agent-health-check.sh"
HEALTH_CHECK_URL = "https://127.0.0.1/api/v1/getAuthConfig"
HEALTH_CHECK_CURL_COUNT = 10
HEALTH_CHECK_CURL_MAX_TIME = 0.2  # 每次请求最大耗时（秒）

# 默认 Web 管理凭据（出厂默认账号密码）
WEB_DEFAULT_USER = "admin"
WEB_DEFAULT_PASS = "admin"
WEB_NEW_PASS = "Ngfw123!@#"  # Web 管理密码

# 总步骤数
TOTAL_STEPS = 10

# 日志目录（固定），文件名由 main() 根据串口服务器地址动态生成
LOG_DIR = "logs"
LOG_FILE = ""  # 将在 main() 中赋值

# 全局标志：是否因设备无管理 IP 而使用了本地安装包
_used_local_package: str = ""  # 若非空则记录使用的本地包文件名

# 是否在 /root/license/ 目录不存在时中止脚本执行
# True：目录缺失则直接报错退出；False（默认）：仅打印警告，继续执行
REQUIRE_LICENSE_DIR: bool = False


# ==================== 日志初始化 ====================


def _setup_file_logger(log_path: str) -> logging.Logger:
    """
    初始化文件日志记录器。

    所有操作日志、串口 I/O 都会写入 log_path。
    若 log_path 所在目录不存在，则自动创建。
    """
    # 自动创建日志目录（如果不存在）
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("ngfwinstall")
    logger.setLevel(logging.DEBUG)

    # 避免重复添加 handler
    if not logger.handlers:
        fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


# 全局文件日志记录器（延迟初始化，由 main() 在解析参数后调用 _setup_file_logger() 赋值）
file_logger: logging.Logger = logging.getLogger("ngfwinstall")


# ==================== 工具函数 ====================


def _log(level: str, formatted_msg: str):
    """同时输出到终端和日志文件"""
    print(formatted_msg)
    # 写入日志文件（去掉前导空格让日志文件更整洁）
    clean_msg = formatted_msg.strip()
    if level == "DEBUG":
        file_logger.debug(clean_msg)
    elif level == "INFO":
        file_logger.info(clean_msg)
    elif level == "WARNING":
        file_logger.warning(clean_msg)
    elif level == "ERROR":
        file_logger.error(clean_msg)
    elif level == "CRITICAL":
        file_logger.critical(clean_msg)


def log_step(step: int, msg: str):
    """输出带步骤编号的日志"""
    _log("INFO", f"[步骤 {step}/{TOTAL_STEPS}] {msg}")


def log_info(msg: str):
    """输出信息日志"""
    _log("INFO", f"  [信息] {msg}")


def log_device(msg: str):
    """输出设备回显"""
    _log("DEBUG", f"  [设备] {msg}")


def log_ok(msg: str):
    """输出成功日志"""
    _log("INFO", f"  [成功] {msg}")


def log_warn(msg: str):
    """输出警告日志"""
    _log("WARNING", f"  [警告] {msg}")


def log_fail(msg: str):
    """输出失败日志"""
    _log("ERROR", f"  [失败] {msg}")


def fatal(msg: str):
    """输出致命错误并退出"""
    _log("CRITICAL", f"[致命错误] {msg}")
    sys.exit(1)


# ==================== TelnetShell 类 ====================

# PROMPT_MARKER 的预计算变体，仅供 TelnetShell 内部使用
# （串口有延迟，末尾空格可能单独到达，因此需要去空格的 BARE 版本）
PROMPT_MARKER_BYTES = PROMPT_MARKER.encode("utf-8")
PROMPT_MARKER_BARE = PROMPT_MARKER.strip()
PROMPT_MARKER_BARE_BYTES = PROMPT_MARKER_BARE.encode("utf-8")


class TelnetShell:
    """
    封装通过串口服务器的 Telnet 交互。

    串口服务器将 telnet 连接转发到目标设备的串口，
    因此 telnet 连接在设备重启期间始终保持（不会断开）。
    """

    def __init__(self, host: str, port: int, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.tn: telnetlib.Telnet | None = None
        self._prompt_set = False
        self._original_ps1: bool = False  # 标记是否已将原始 PS1 保存到设备 shell 变量

    def connect(self):
        """建立 telnet 连接到串口服务器"""
        log_info(f"正在连接串口服务器 {self.host}:{self.port} ...")
        try:
            self.tn = telnetlib.Telnet(self.host, self.port, self.timeout)
        except Exception as e:
            fatal(f"无法连接串口服务器: {e}")
        log_ok("串口服务器连接成功")

    def close(self):
        """
        关闭 telnet 连接。

        必须先发 exit 退出 bash，再关 TCP：
        若直接关闭 TCP，串口服务器会向串口注入 break 信号，
        导致仍在运行的 bash tty 进入异常状态，串口卡死。
        """
        if self.tn:
            # 步骤 1：退出 bash Shell，让串口回到 login 登录提示符等待状态
            try:
                self._write("exit\n")
                time.sleep(1.0)  # 等待 bash 退出并回到 login 提示符
                self._read_available()
                log_info("Shell 已退出，串口回到登录提示符状态")
            except Exception:
                pass

            # 步骤 2：关闭 TCP 连接
            try:
                self.tn.close()
            except Exception:
                pass
            self.tn = None
            self._prompt_set = False
            self._original_ps1 = False
            log_info("串口服务器连接已关闭")

    def _read_available(self) -> str:
        """读取当前缓冲区中所有可用数据"""
        try:
            data = self.tn.read_very_eager()
            text = data.decode("utf-8", errors="replace")
            if text:
                file_logger.debug("[RECV] %s", repr(text))
            return text
        except EOFError:
            return ""

    def _write(self, text: str):
        """发送数据到串口"""
        file_logger.debug("[SEND] %s", repr(text))
        self.tn.write(text.encode("utf-8"))

    def _read_until(self, marker: bytes, timeout: int) -> str:
        """读取直到匹配到指定标记"""
        try:
            data = self.tn.read_until(marker, timeout)
            text = data.decode("utf-8", errors="replace")
            if text:
                file_logger.debug("[RECV] %s", repr(text))
            return text
        except EOFError:
            return ""

    def _normalize_output(self, text: str) -> str:
        """规范化输出文本（处理 \\r\\n 等）"""
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def activate_console(self) -> str:
        """
        激活串口控制台，检测当前状态。

        返回值：
            "login"  - 检测到登录提示符
            "shell"  - 检测到 Shell 提示符（已登录）
            "unknown" - 无法确定状态
        """
        # 先清空当前缓冲区
        self._read_available()

        # 发送回车，使用带超时的 read_until 等待响应（比 sleep+read_very_eager 更可靠）
        # 同时包含我们自定义的 PROMPT_MARKER，这样如果上次没有正确还原 PS1 也能被检测到
        self._write("\n")
        output = self._read_until_any(
            [b"login:", b"Login:", b"assword:", b"# ", b"$ ", PROMPT_MARKER_BARE_BYTES],
            timeout=4,
        )

        state = self._detect_state_from_output(output)
        if state != "unknown":
            return state

        # 第二次尝试：发送 Ctrl+C 后再回车（中断可能卡住的进程）
        self._write("\x03")  # Ctrl+C
        time.sleep(0.5)
        self._write("\n")
        output = self._read_until_any(
            [b"login:", b"Login:", b"# ", b"$ ", PROMPT_MARKER_BARE_BYTES],
            timeout=4,
        )

        state = self._detect_state_from_output(output)
        if state != "unknown":
            return state

        # 第三次尝试：多按几次回车
        for _ in range(3):
            self._write("\n")
            time.sleep(0.8)

        output = self._read_available()
        return self._detect_state_from_output(output)

    def _read_until_any(self, markers: list[bytes], timeout: int) -> str:
        """
        读取直到匹配到任意一个 marker，或者超时。
        用于需要同时检测多种提示符的场景。
        """
        buf = b""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                chunk = self.tn.read_very_eager()
                if chunk:
                    file_logger.debug(
                        "[RECV] %s", repr(chunk.decode("utf-8", errors="replace"))
                    )
                    buf += chunk
                    for m in markers:
                        if m in buf:
                            return buf.decode("utf-8", errors="replace")
            except EOFError:
                break
            time.sleep(0.1)
        return buf.decode("utf-8", errors="replace")

    def _detect_state_from_output(self, output: str) -> str:
        """从输出内容判断当前状态"""
        if not output:
            return "unknown"

        lower = output.lower()
        if "login:" in lower:
            return "login"
        # 检测常见 Shell 提示符模式
        if re.search(r"[#\$]\s*$", output.strip()):
            return "shell"
        if PROMPT_MARKER_BARE in output:
            return "shell"
        return "unknown"

    def login(self, username: str, password: str, timeout: int = 15) -> bool:
        """
        通过 Shell 登录。

        如果当前已在 Shell 中，直接返回 True。
        如果在登录提示，执行用户名/密码登录流程。

        判断逻辑说明：
          - 发送密码后，用 _read_until_any 主动等待明确信号，避免 sleep+read_available 的竞争问题
          - 判断顺序：优先判断「成功」，再判断「失败」
          - 原因："Last login:" 中包含 "login:"，若先判断 login: 会误判为失败
        """
        state = self.activate_console()

        if state == "shell":
            log_info("当前已在 Shell 中，无需登录")
            return True

        if state == "unknown":
            # 未知状态，尝试发送用户名试试
            log_warn("无法确定串口状态，尝试执行登录流程")
            self._write("\n")
            time.sleep(1)

        # 发送用户名
        log_info(f"正在使用用户 {username} 登录...")
        self._write(username + "\n")

        # 等待密码提示
        output = self._read_until(b"assword:", timeout)
        if "assword:" not in output:
            # 可能已经登录了？再检查一次
            log_warn("未收到密码提示，尝试检测状态")
            all_output = output + self._read_available()
            if re.search(r"[#\$]\s*$", all_output.strip()):
                log_ok("已在 Shell 中")
                return True
            log_fail(f"登录失败：未收到预期提示。收到: {all_output[:200]}")
            return False

        # 发送密码
        self._write(password + "\n")

        # 主动等待明确的终止信号，而不是 sleep 后读一次快照
        # 成功信号：shell 提示符（# 或 $），或 "Last login"
        # 失败信号："incorrect"（登录失败提示），或 "login:"（被踢回登录提示）
        output = self._read_until_any(
            [
                b"# ",  # root shell 提示符（成功）
                b"$ ",  # 普通用户 shell 提示符（成功）
                b"Last login",  # 登录成功后的欢迎信息（包含 login: 易误判，需优先匹配）
                b"incorrect",  # "Login incorrect"（错误密码）
                b"login:",  # 被踢回登录提示（登录失败，或新的登录提示）
            ],
            timeout=timeout,
        )
        file_logger.debug("[LOGIN_RESULT] %s", repr(output))

        output_lower = output.lower()

        # ===== 优先判断「成功」=====
        # 出现 shell 提示符（# 或 $）
        if re.search(r"[#\$]\s", output):
            log_ok(f"登录成功，检测到 Shell 提示符 (用户: {username})")
            return True
        # 出现 "Last login"：登录成功后系统给出的最后登录信息，其中包含 "login:" 但不代表失败
        if "last login" in output_lower:
            log_ok(f"登录成功，检测到 Last login 信息 (用户: {username})")
            return True

        # ===== 再判断「失败」=====
        # "incorrect" 明确表示密码错误
        if "incorrect" in output_lower:
            log_fail("登录失败：密码错误（收到 incorrect 提示）")
            return False
        # "login:"（且不含 "last login"，已在上面处理）表示被踢回登录提示
        if "login:" in output_lower:
            log_fail("登录失败：已返回登录提示符")
            return False

        # 超时后未收到任何明确信号，再等一下补读一次
        time.sleep(2)
        extra = self._read_available()
        all_output = output + extra
        if re.search(r"[#\$]\s", all_output) or "last login" in all_output.lower():
            log_ok(f"登录成功（补读确认）(用户: {username})")
            return True

        log_fail(f"登录失败：超时后仍无法确认状态。收到: {repr(all_output[:300])}")
        return False

    def try_login_with_passwords(self, username: str, passwords: list[str]) -> bool:
        """尝试使用多个密码登录，直到成功"""
        for pwd in passwords:
            log_info(f"尝试密码: {pwd}")
            state = self.activate_console()

            if state == "shell":
                log_ok("已在 Shell 中")
                return True

            if state == "login":
                if self.login(username, pwd):
                    return True
                # 登录失败，等待 login 提示重新出现
                time.sleep(2)
                continue

            # 未知状态
            if self.login(username, pwd):
                return True
            time.sleep(2)

        return False

    def setup_prompt(self):
        """
        设置自定义 Shell 提示符，确保可靠检测命令完成。
        同时关闭命令历史和设置终端参数。
        """
        # 先在设备 shell 侧用一个变量保存原始 PS1（只保存一次）
        # 用设备 shell 自身的变量，完全避免 Python 解析/转义问题
        if not self._original_ps1:
            # 保存当前 PS1；如果已经是我们自定义的 marker（上次未还原）则重置为默认值
            save_cmd = (
                '_NGFW_ORIG_PS1="$PS1"; '
                f'[ "$_NGFW_ORIG_PS1" = "{PROMPT_MARKER.strip()}" ] '
                r"&& _NGFW_ORIG_PS1='[\u@\h \W]\$ '"
            )
            self._write(save_cmd + "\n")
            time.sleep(0.5)
            self._read_available()  # 清空回显
            self._original_ps1 = True  # 标记已保存
            file_logger.debug("[PS1] 已将原始 PS1 保存到设备 shell 变量 _NGFW_ORIG_PS1")

        # 设置自定义提示符
        self._write(f"export PS1='{PROMPT_MARKER}'\n")
        time.sleep(1)
        self._read_available()  # 清空回显

        # 再发一个回车验证
        self._write("\n")
        output = self._read_until(PROMPT_MARKER_BYTES, 5)

        if PROMPT_MARKER in output:
            self._prompt_set = True
            log_ok("自定义提示符设置成功")
        else:
            # 自定义提示符未设置成功，说明可能登录失败或 Shell 状态异常
            # 继续执行毫无意义，直接终止并提示用户
            fatal(
                "自定义提示符设置失败，可能原因：\n"
                "  1. 登录失败（密码错误或账号锁定）\n"
                "  2. 串口状态异常（Shell 未就绪）\n"
                "请检查设备登录密码及串口连接状态后重试。"
            )

        # 关闭命令历史，减少干扰
        self._write("export HISTSIZE=0\n")
        time.sleep(0.5)
        self._read_available()

        # 设置终端宽度，避免输出换行
        self._write("export COLUMNS=200\n")
        time.sleep(0.5)
        self._read_available()

    def exec_command(self, cmd: str, timeout: int = 30) -> str:
        """
        执行命令并返回输出。

        会等待自定义提示符出现以确认命令执行完毕。
        """
        if not self._prompt_set:
            self.setup_prompt()

        # 清空缓冲区
        self._read_available()

        # 发送命令
        self._write(cmd + "\n")

        # 等待提示符
        raw = self._read_until(PROMPT_MARKER_BYTES, timeout)
        raw = self._normalize_output(raw)

        # 解析输出：去掉命令回显和提示符
        # 说明：串口终端会对超长命令回显自动折行（在约第 80 列插入 \r），
        # 导致命令回显跨越多行。因此不能仅检查 i==0，而是要把「包含 cmd
        # 片段」的那些行（从第 0 行起连续出现的）全部跳过。
        lines = raw.split("\n")
        output_lines = []
        cmd_stripped = cmd.strip()
        skip_echo = True  # 在回显结束前持续跳过
        for i, line in enumerate(lines):
            stripped = line.strip()
            # 跳过提示符行
            if PROMPT_MARKER.strip() in stripped:
                continue
            # 跳过命令回显：只要还处于「回显跳过」模式，
            # 且该行内容属于 cmd 的一部分（子串），则继续跳过。
            # 一旦遇到第一个「不属于 cmd」的非空行，关闭跳过模式。
            if skip_echo:
                if not stripped:
                    # 空行可能是回显和输出之间的分隔，保持跳过模式继续
                    continue
                if stripped in cmd_stripped or cmd_stripped.startswith(stripped) or stripped.startswith(cmd_stripped[:20]):
                    # 该行是命令回显的一部分（完整或折行片段），跳过
                    continue
                else:
                    # 遇到第一个真正的输出行，关闭回显跳过模式
                    skip_echo = False
            output_lines.append(line)

        return "\n".join(output_lines).strip()

    def exec_command_checked(self, cmd: str, timeout: int = 30) -> tuple:
        """
        执行命令并返回 (退出码, 输出)。

        通过 echo $? 获取退出码。
        """
        output = self.exec_command(cmd, timeout)
        exit_code_str = self.exec_command("echo $?", 5)

        try:
            exit_code = int(exit_code_str.strip().splitlines()[-1].strip())
        except (ValueError, IndexError):
            exit_code = -1

        return exit_code, output

    def exec_long_command(
        self,
        cmd: str,
        timeout: int = 900,
        print_output: bool = True,
        stop_patterns: list | None = None,
    ) -> str:
        """
        执行长时间运行的命令，实时读取和打印输出。

        适用于卸载、安装等耗时操作。

        stop_patterns:
            额外的终止模式列表（字符串）。当累积输出中出现任意一个字符串时，
            立即退出读取循环，不再等待 PROMPT_MARKER。

            适用场景：安装命令执行后设备自动重启，此时 PROMPT_MARKER 不会
            再出现（shell 已随系统重启消失），必须通过特征字符串判断命令
            已触发后续动作（如重启），否则会一直等到超时。

            典型特征字符串示例：
              - "rebooting..."         - TGFW 安装完成后的重启提示
              - "Restarting system"    - 内核 reboot 消息（最终保障）
        """
        if not self._prompt_set:
            self.setup_prompt()

        # 清空缓冲区
        self._read_available()

        # 发送命令
        self._write(cmd + "\n")

        output_parts = []
        accumulated = ""  # 用于 stop_patterns 匹配的累积文本
        start = time.time()
        first_chunk = True  # 第一个数据块可能包含命令回显
        stop_hit = False

        while time.time() - start < timeout:
            try:
                data = self.tn.read_until(PROMPT_MARKER_BYTES, 10)
                text = data.decode("utf-8", errors="replace")
                if text:
                    file_logger.debug("[RECV] %s", repr(text))
                text = self._normalize_output(text)

                if text.strip():
                    lines = text.strip().split("\n")
                    for i, line in enumerate(lines):
                        line_stripped = line.rstrip()
                        # 跳过提示符行
                        if PROMPT_MARKER.strip() in line_stripped:
                            continue
                        # 跳过第一个块中的命令回显行
                        if first_chunk and i == 0 and cmd.strip() in line_stripped:
                            continue
                        if line_stripped and print_output:
                            log_device(line_stripped)
                    first_chunk = False
                    output_parts.append(text)
                    accumulated += text

                # 优先检测自定义提示符（普通命令完成时）
                if PROMPT_MARKER in text:
                    break

                # 检测 stop_patterns（用于安装等会触发重启的命令）
                if stop_patterns:
                    for pat in stop_patterns:
                        if pat in accumulated:
                            log_info(f"检测到终止标志: {repr(pat)}，命令已完成")
                            stop_hit = True
                            break
                    if stop_hit:
                        break

            except EOFError:
                log_warn("连接中断")
                break

        if stop_hit:
            # 命令触发重启后继续读取约 2 秒，把最后的输出也打印出来
            time.sleep(2)
            try:
                tail = self._read_available()
                if tail and print_output:
                    for line in self._normalize_output(tail).split("\n"):
                        if line.strip():
                            log_device(line.strip())
                accumulated += tail
                output_parts.append(tail)
            except Exception:
                pass

        return "".join(output_parts)

    def wait_for_reboot_login(self, timeout: int = 900) -> bool:
        """
        等待设备重启完成并出现登录提示符。

        在等待期间实时打印设备的启动日志。
        """
        log_info(f"等待设备重启完成（最长 {timeout} 秒）...")
        start = time.time()
        last_report = start

        while time.time() - start < timeout:
            try:
                data = self.tn.read_very_eager()
                if data:
                    text = data.decode("utf-8", errors="replace")
                    file_logger.debug("[RECV] %s", repr(text))
                    text = self._normalize_output(text)

                    # 打印重启过程中的关键信息
                    for line in text.split("\n"):
                        line_s = line.strip()
                        if line_s:
                            log_device(line_s)

                    if "login:" in text.lower():
                        elapsed = int(time.time() - start)
                        log_ok(f"检测到登录提示符，设备已重启完成（耗时 {elapsed} 秒）")
                        return True
            except EOFError:
                log_warn("连接断开，尝试重新连接...")
                time.sleep(10)
                try:
                    self.tn = telnetlib.Telnet(self.host, self.port, self.timeout)
                    log_ok("重新连接成功")
                except Exception:
                    pass

            # 定期报告等待状态
            now = time.time()
            if now - last_report >= 60:
                elapsed = int(now - start)
                log_info(f"已等待 {elapsed} 秒...")
                last_report = now
                # 发送空行探测
                try:
                    self._write("\n")
                except Exception:
                    pass

            time.sleep(3)

        elapsed = int(time.time() - start)
        log_fail(f"等待设备重启超时（{elapsed} 秒）")
        return False


# ==================== RSA 密码加密/登录函数 ====================
# 以下函数从 encrypt_password.py 移植而来


def get_rsa_pub_key(base_url: str) -> str:
    """
    从防火墙 Web 页面获取 RSA 公钥（PEM 格式字符串）

    :param base_url: 防火墙的基础 URL，例如 https://<IP_ADDRESS>
    :return: PEM 格式的公钥字符串
    """
    base_url = base_url.rstrip("/")

    # 访问 index.html 获取公钥 JS 文件的路径
    index_url = base_url + "/index.html"
    response = requests.get(index_url, timeout=10, verify=False)
    if response.status_code != 200:
        raise RuntimeError(f"无法访问 {index_url}，HTTP 状态码: {response.status_code}")

    # 用正则表达式从 HTML 中匹配公钥 JS 文件路径
    pattern = re.compile(r'src="(/js/ras_public_key.\d+.js)"')
    matches = pattern.findall(response.text)
    if not matches:
        raise RuntimeError("在 index.html 中未找到公钥 JS 文件引用")

    # 请求公钥 JS 文件并解析出 PEM 公钥
    js_url = base_url + matches[0]
    js_response = requests.get(js_url, timeout=10, verify=False)
    if js_response.status_code != 200:
        raise RuntimeError(
            f"获取公钥 JS 文件失败，HTTP 状态码: {js_response.status_code}"
        )

    # 解析 JS 内容，提取 PEM 公钥
    pub_key = (
        js_response.text.replace("\\n' +", "")
        .replace("var __PUBLIC_KEY__ =  ", "")
        .replace("'", "")
        .replace("  ", "")
        .strip()
    )

    return pub_key


def encrypt_password_rsa(base_url: str, plaintext: str) -> str:
    """
    使用防火墙的 RSA 公钥对明文密码进行加密

    :param base_url: 防火墙的基础 URL
    :param plaintext: 明文密码
    :return: Base64 编码的加密密文字符串
    """
    pub_key_pem = get_rsa_pub_key(base_url)
    public_key = serialization.load_pem_public_key(pub_key_pem.encode("utf-8"))
    encrypted_bytes = public_key.encrypt(
        plaintext.encode("utf-8"),
        padding.PKCS1v15(),
    )
    return base64.b64encode(encrypted_bytes).decode("utf-8")


def web_login(base_url: str, username: str, password_plain: str) -> dict:
    """
    使用加密后的密码登录防火墙 Web 管理接口

    :return: 登录接口返回的 JSON 响应
    """
    encrypted_passwd = encrypt_password_rsa(base_url, password_plain)

    payload = {
        "id": username,
        "val": {
            "username": username,
            "passwd": encrypted_passwd,
            "action": "login",
            "autht": 0,
            "code": "",
        },
    }

    login_url = base_url.rstrip("/") + "/api/v1/auth"
    log_info(f"正在登录 Web 管理: PUT {login_url}")
    response = requests.put(login_url, json=payload, timeout=10, verify=False)
    return response.json()


def web_change_default_password(
    base_url: str, username: str, old_password: str, new_password: str
) -> dict:
    """
    修改防火墙的默认密码

    :return: 修改密码接口返回的 JSON 响应
    """
    encrypted_old = encrypt_password_rsa(base_url, old_password)
    encrypted_new = encrypt_password_rsa(base_url, new_password)

    payload = {
        "id": username,
        "val": {
            "username": username,
            "passwd": encrypted_new,
            "oldpasswd": encrypted_old,
        },
    }

    url = base_url.rstrip("/") + "/api/v1/changeDefPwd"
    log_info(f"正在修改默认密码: PUT {url}")
    response = requests.put(url, json=payload, timeout=10, verify=False)
    return response.json()


def web_login_with_auto_change_password(
    base_url: str,
    username: str = "admin",
    default_password: str = "admin",
    new_password: str = WEB_NEW_PASS,  # Web 管理密码（大写 N），与 root 串口密码不同
) -> dict:
    """
    自动处理默认密码修改的登录流程：
      1. 先用默认密码尝试登录
      2. 如果需要修改默认密码，则自动修改
      3. 最后用新密码完成登录
    """
    # 尝试使用默认密码登录
    log_info("尝试使用默认密码登录 Web 管理...")
    result = web_login(base_url, username, default_password)

    if result.get("errCode") == "eChangDeafPwd":
        log_info(f"检测到需要修改默认密码: {result.get('errMsg', '')}")
        change_result = web_change_default_password(
            base_url, username, default_password, new_password
        )
        if change_result.get("errCode"):
            raise RuntimeError(f"修改默认密码失败: {change_result}")
        log_ok("默认密码修改成功")

        # 使用新密码登录
        log_info("使用新密码登录...")
        result = web_login(base_url, username, new_password)

    elif "token" in result:
        log_info("使用默认密码直接登录成功，无需修改密码")

    else:
        # 默认密码登录失败，尝试用新密码
        log_info(f"默认密码登录失败: {result.get('errMsg', '未知错误')}，尝试新密码")
        result = web_login(base_url, username, new_password)

    return result


def web_set_systime(base_url: str, token: str) -> dict:
    """
    配置 NTP 时间同步服务器

    :param base_url: 防火墙的基础 URL，例如 https://<IP_ADDRESS>
    :param token: 登录后获取的 Bearer Token
    :return: 接口返回的 JSON 响应
    """
    payload = {
        "id": "systime",
        "val": {
            "name": "systime",
            "enable": True,
            "ntp": {
                "mainserver": "<IP_ADDRESS>",
                "secondserver": "",
                "interval": 10,
                "key_id": 0,
                "crypto_method": 0,
                "is_enable_auth": False,
            },
        },
    }

    url = base_url.rstrip("/") + "/api/v1/systime"
    headers = {"Authorization": f"Bearer {token}"}
    log_info(f"正在配置 NTP 时间同步: PUT {url}")
    response = requests.put(url, json=payload, headers=headers, timeout=10, verify=False)
    return response.json()


def web_logout(base_url: str, token: str) -> bool:
    """
    退出 Web 管理登录

    :param base_url: 防火墙的基础 URL
    :param token: 登录后获取的 Bearer Token
    :return: 是否成功退出（HTTP 200 视为成功）
    """
    url = base_url.rstrip("/") + "/api/v1/logout"
    headers = {"Authorization": f"Bearer {token}"}
    log_info(f"正在退出 Web 管理登录: GET {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            log_ok("Web 管理已成功退出登录")
            return True
        else:
            log_warn(f"退出登录返回非 200 状态码: {response.status_code}")
            return False
    except Exception as e:
        log_warn(f"退出登录请求失败: {e}")
        return False


# ==================== 安装流程各步骤 ====================


def step_connect(serial_url: str) -> TelnetShell:
    """步骤 1：连接串口服务器并获取 Shell"""
    log_step(1, "连接串口服务器")

    parsed = urlparse(serial_url)
    host = parsed.hostname
    port = parsed.port or 23

    if not host:
        fatal(f"无法解析串口服务器地址: {serial_url}")

    shell = TelnetShell(host, port)
    shell.connect()

    # 尝试获取 Shell（可能需要登录）
    log_info("激活串口控制台...")
    state = shell.activate_console()
    log_info(f"检测到串口状态: {state}")

    if state == "login":
        # 直接使用 POST_INSTALL_PASS 登录，不尝试其他密码
        log_info(f"使用密码 {POST_INSTALL_PASS} 登录 {POST_INSTALL_USER} ...")
        if not shell.login(POST_INSTALL_USER, POST_INSTALL_PASS):
            fatal(f"无法登录目标设备 Shell，请检查密码是否为 {POST_INSTALL_PASS}")
    elif state == "shell":
        log_ok("已在 Shell 中")
    else:
        # 未知状态：也直接尝试 POST_INSTALL_PASS
        log_warn("无法确定串口状态，尝试登录")
        if not shell.login(POST_INSTALL_USER, POST_INSTALL_PASS):
            fatal(f"无法获取 Shell 访问权限，请检查密码是否为 {POST_INSTALL_PASS}")

    # 设置自定义提示符
    shell.setup_prompt()

    log_ok("已成功获取 Shell 访问权限")
    return shell


def step_check_environment(shell: TelnetShell, device_ip: str) -> bool:
    """
    步骤 2：检查设备环境。

    返回 True 表示设备具有管理 IP，可以正常下载安装包；
    返回 False 表示设备当前无该管理 IP（可能尚未配置），需使用 /opt 本地包。
    """
    log_step(2, "检查设备环境")

    # 检查设备 IP 是否匹配
    log_info(f"检查设备 IP ({device_ip}) ...")
    ip_output = shell.exec_command("ip addr show", timeout=10)

    has_ip = device_ip in ip_output
    if not has_ip:
        log_warn(
            f"[注意] 设备当前不存在管理 IP {device_ip}，"
            f"将跳过下载步骤，直接使用 /opt 目录下的本地安装包。"
        )
    else:
        log_ok(f"设备 IP 匹配: {device_ip}")

    # 查询 CPU 信息
    log_info("查询 CPU 信息...")
    cpu_output = shell.exec_command(
        "lscpu",
        timeout=10,
    )
    cpu_model = cpu_output.strip() if cpu_output.strip() else "未知"
    log_info(f"CPU 型号: {cpu_model}")

    # 查询系统架构
    arch_output = shell.exec_command("uname -m", timeout=10)
    log_info(f"系统架构: {arch_output.strip()}")

    # 检查 /root/license/ 目录
    log_info("检查 /root/license/ 目录...")
    _, output = shell.exec_command_checked(
        "test -d /root/license/ && echo 'EXISTS' || echo 'NOT_EXISTS'",
        timeout=10,
    )
    if "NOT_EXISTS" in output:
        if REQUIRE_LICENSE_DIR:
            fatal("/root/license/ 目录不存在，设备不满足安装条件")
        else:
            log_warn(
                "/root/license/ 目录不存在，将跳过 license 恢复步骤（REQUIRE_LICENSE_DIR=False）"
            )
    else:
        log_ok("/root/license/ 目录存在")

    log_ok("设备环境检查通过")
    return has_ip


def step_download_package(
    shell: TelnetShell,
    package_url: str,
    expected_md5: str = "",
    ftp_user: str = "",
    ftp_password: str = "",
) -> str:
    """
    步骤 3：下载安装包并校验（不解压）。

    返回安装包文件名（不含路径），供后续卸载完成后调用 _extract_package 使用。

    注意：解压操作必须在卸载完成之后执行，否则卸载过程会清空
    /opt/dbappsecurity 目录，导致解压出的安装程序被删除。
    """
    log_step(3, "下载安装包")

    # 提取安装包文件名
    parsed = urlparse(package_url)
    filename = os.path.basename(parsed.path)
    if not filename:
        fatal(f"无法从 URL 中提取文件名: {package_url}")
    log_info(f"安装包文件名: {filename}")

    # 清理旧的安装包
    log_info("清理 /opt 目录下的旧安装包...")
    shell.exec_command("rm -f /opt/*.tar.gz", timeout=10)
    log_ok("旧安装包已清理")

    # 下载安装包
    log_info(f"正在下载安装包: {package_url}")
    log_info("下载可能需要几分钟，请耐心等待...")

    # 拼接 wget 命令：如有 FTP 认证则加入 --user/--password
    # --progress=dot -e dotbytes=30M：每 30MB 打印一个进度点，大幅减少输出行数
    auth_args = ""
    if ftp_user:
        auth_args = f"--user={ftp_user} --password='{ftp_password}' "
        log_info(f"FTP 认证用户: {ftp_user}")
    download_cmd = (
        f"wget --progress=dot -e dotbytes=30M "
        f"{auth_args}'{package_url}' -O '/opt/{filename}' 2>&1"
    )
    shell.exec_long_command(download_cmd, timeout=600, print_output=True)

    # 验证下载成功：文件必须存在且大小 > 0
    exit_code, _ = shell.exec_command_checked(f"test -s '/opt/{filename}'", timeout=10)
    if exit_code != 0:
        fatal(f"安装包下载失败（文件不存在或大小为 0）: /opt/{filename}")

    # 获取文件大小
    size_output = shell.exec_command(
        f"ls -lh '/opt/{filename}' | awk '{{print $5}}'", timeout=10
    )
    log_ok(f"安装包下载完成，大小: {size_output}")

    # MD5 校验
    log_info("计算安装包 MD5 ...")
    md5_output = shell.exec_command(f"md5sum '/opt/{filename}'", timeout=60)
    # 注意：串口终端折行可能导致命令回显跨行，直接用 split()[0] 不可靠。
    # 改用正则精确提取 32 位十六进制 MD5 值，彻底绕开回显解析问题。
    md5_match = re.search(r'\b([0-9a-fA-F]{32})\b', md5_output)
    local_md5 = md5_match.group(1) if md5_match else "unknown"
    log_info(f"本地 MD5: {local_md5}")

    if expected_md5:
        # 用户提供了 MD5 校验值
        if local_md5 == expected_md5:
            log_ok(f"MD5 校验通过: {local_md5}")
        else:
            fatal(f"MD5 校验失败！\n  期望: {expected_md5}\n  实际: {local_md5}")
    else:
        log_warn(f"未提供 MD5 校验值，跳过校验（当前 MD5: {local_md5}）")

    # 注意：此处不解压！解压必须在卸载完成之后进行。
    log_ok("安装包下载并校验完成（等待卸载完成后再解压）")
    return filename


def _extract_package(shell: TelnetShell, filename: str):
    """
    将 /opt/{filename} 解压到 /opt 目录。

    解压完成后，/opt 下会出现安装程序目录（如 dbappsecurity/），
    后续安装步骤直接使用解压出来的文件。
    """
    log_info(f"正在解压安装包 /opt/{filename} 到 /opt 目录...")
    exit_code, output = shell.exec_command_checked(
        f"tar -xzf '/opt/{filename}' -C /opt",
        timeout=300,
    )
    if exit_code != 0:
        fatal(f"安装包解压失败（退出码: {exit_code}）: {output}")
    log_ok("安装包解压完成")


def step_use_local_package(shell: TelnetShell) -> str:
    """
    步骤 3（备用）：设备无管理 IP 时，查找并使用 /opt 目录下现有的安装包。

    执行顺序：
      1. 扫描 /opt/*.tar.gz 找到安装包（不先解压）
      2. 检查 /opt/dbappsecurity/bin/ngfwuninstall 是否存在（判断是否有已装系统）
      3. 若已装系统 → 先执行卸载（使用现有二进制，而非新包中的）
      4. 将新包解压到 /opt 目录

    返回找到的安装包文件名（不含路径）；若不存在则 fatal 退出。
    """
    global _used_local_package
    log_step(3, "查找本地安装包（设备无管理 IP，跳过下载）")

    # 1. 扫描 /opt 下的 tar.gz 文件（按名称排序取第一个），此阶段不解压
    find_output = shell.exec_command(
        "ls /opt/*.tar.gz 2>/dev/null | head -1",
        timeout=10,
    ).strip()

    if not find_output:
        fatal(
            "设备当前无管理 IP，且 /opt 目录下未找到任何 .tar.gz 安装包，"
            "无法继续安装。请手动将安装包上传至 /opt 目录后重试。"
        )

    filename = os.path.basename(find_output)
    log_warn(
        f"[重要] 当前设备管理 IP 不可达，直接使用 /opt 目录下的 {filename} 安装包进行安装。"
    )
    log_info(f"本地安装包路径: {find_output}")

    # 验证文件大小
    size_output = shell.exec_command(
        f"ls -lh '{find_output}' | awk '{{print $5}}'", timeout=10
    )
    log_info(f"安装包大小: {size_output}")

    # 2. 在解压新包之前，先检查是否存在已安装的系统
    #    必须在此处检查，因为解压后新包会覆盖 /opt/dbappsecurity，无法区分新旧二进制
    log_info("检查是否存在已安装的 TGFW 系统...")
    exit_code, _ = shell.exec_command_checked(
        "test -f /opt/dbappsecurity/bin/ngfwuninstall", timeout=10
    )
    if exit_code == 0:
        # 3. 已装系统 → 先卸载
        log_info("检测到已安装的 TGFW 系统，执行卸载...")
        log_info("正在执行卸载，这可能需要几分钟...")
        shell.exec_long_command(
            "yes | /opt/dbappsecurity/bin/ngfwuninstall",
            timeout=300,
            print_output=True,
        )
        log_ok("卸载命令执行完成")
    else:
        log_info("未检测到已安装的 TGFW 系统，跳过卸载步骤")

    # 4. 解压新安装包到 /opt 目录
    _extract_package(shell, filename)

    # 记录全局标志，供结尾摘要使用
    _used_local_package = filename
    log_ok("本地安装包处理完成，继续安装流程")
    return filename


def step_uninstall(shell: TelnetShell):
    """步骤 4：卸载当前版本"""
    log_step(4, "卸载当前版本")

    # 检查卸载程序是否存在
    exit_code, _ = shell.exec_command_checked(
        "test -f /opt/dbappsecurity/bin/ngfwuninstall", timeout=10
    )
    if exit_code != 0:
        log_warn("卸载程序不存在，可能是首次安装，跳过卸载步骤")
        return

    log_info("正在执行卸载，这可能需要几分钟...")
    # 使用 yes 管道自动确认可能的交互提示
    shell.exec_long_command(
        "yes | /opt/dbappsecurity/bin/ngfwuninstall",
        timeout=300,
        print_output=True,
    )

    log_ok("卸载命令执行完成")


def step_install(shell: TelnetShell, device_type: str, device_ip: str):
    """步骤 5：安装新版本"""
    log_step(5, "安装新版本")

    install_cmd = (
        f"/opt/dbappsecurity/bin/ngfwinstall "
        f"-t {device_type} "
        f"-i {device_ip} "
        f"-m 22 "
        f"--disable_backup"
    )
    log_info(f"执行安装命令: {install_cmd}")
    log_info("安装过程可能需要 10 分钟以上，设备将自动重启...")

    # 安装命令执行完毕后设备会自动重启，PROMPT_MARKER 不会再出现。
    # 通过 stop_patterns 监测安装完成 / 重启启动的特征字符串来判断命令完成，
    # 避免一直等到 timeout（15 分钟）才退出。
    #
    # 依据日志观察到的实际输出顺序：
    #   1. "Install ... success."          —— 安装成功消息
    #   2. "rebooting..."                  —— TGFW 安装脚本触发重启的打印
    #   3. systemd 关闭服务的 Stopping 消息
    #   4. "reboot: Restarting system"     —— 内核最终 reboot 消息
    # 任意一条出现即可认定安装阶段已结束，后续交由 step_wait_reboot 处理。
    shell.exec_long_command(
        install_cmd,
        timeout=900,
        print_output=True,
        stop_patterns=[
            "rebooting...",  # TGFW 安装脚本结束时的重启提示
            "Restarting system",  # 内核 reboot 消息（最终保障）
        ],
    )

    log_ok("安装命令已触发，设备开始重启")


def step_wait_reboot(shell: TelnetShell) -> bool:
    """步骤 6：等待设备重启完成"""
    log_step(6, "等待设备重启完成")

    # 重置提示符状态（重启后需要重新设置）
    shell._prompt_set = False

    if not shell.wait_for_reboot_login(timeout=900):
        fatal("等待设备重启超时（15 分钟），请手动检查设备状态")

    return True


def step_post_reboot_login(shell: TelnetShell):
    """步骤 7：重启后登录并设置环境"""
    log_step(7, "重启后登录设备")

    # 使用安装后的凭据登录
    if not shell.login(POST_INSTALL_USER, POST_INSTALL_PASS):
        fatal(f"重启后无法登录，用户: {POST_INSTALL_USER}")

    # 重新设置自定义提示符
    shell.setup_prompt()

    log_ok("重启后登录成功")


def step_health_check(shell: TelnetShell):
    """步骤 8：执行健康检查"""
    log_step(8, "执行健康检查")

    # 等待一段时间让服务完全启动
    log_info("等待 120 秒让服务完全启动...")
    time.sleep(120)

    # VPP 健康检查（间隔 10s，最多重试 30 次）
    log_info("执行 VPP 健康检查...")
    _MAX_RETRY = 30
    _RETRY_INTERVAL = 10
    for _attempt in range(1, _MAX_RETRY + 1):
        exit_code, output = shell.exec_command_checked(HEALTH_CHECK_VPP, timeout=60)
        if exit_code == 0:
            break
        log_warn(
            f"VPP 健康检查未通过 (退出码: {exit_code})，"
            f"第 {_attempt}/{_MAX_RETRY} 次，{_RETRY_INTERVAL}s 后重试..."
        )
        if _attempt == _MAX_RETRY:
            fatal(
                f"VPP 健康检查失败：已重试 {_MAX_RETRY} 次仍未通过 (退出码: {exit_code})"
            )
        time.sleep(_RETRY_INTERVAL)
    log_ok("VPP 健康检查通过")

    # Agent 健康检查（间隔 10s，最多重试 30 次）
    log_info("执行 Agent 健康检查...")
    for _attempt in range(1, _MAX_RETRY + 1):
        exit_code, output = shell.exec_command_checked(HEALTH_CHECK_AGENT, timeout=60)
        if exit_code == 0:
            break
        log_warn(
            f"Agent 健康检查未通过 (退出码: {exit_code})，"
            f"第 {_attempt}/{_MAX_RETRY} 次，{_RETRY_INTERVAL}s 后重试..."
        )
        if _attempt == _MAX_RETRY:
            fatal(
                f"Agent 健康检查失败：已重试 {_MAX_RETRY} 次仍未通过 (退出码: {exit_code})"
            )
        time.sleep(_RETRY_INTERVAL)
    log_ok("Agent 健康检查通过")

    # Curl 健康检查
    # 规则：
    #   - 每轮逐条发起请求（每次间隔 10s），遇到任意一次耗时 > HEALTH_CHECK_CURL_MAX_TIME
    #     或非 200，立即中断本轮，sleep 10s 后从第 1 次重新开始新一轮
    #   - 一轮内所有请求全部通过才算成功
    #   - 整个过程最多进行 10 轮；超过 10 轮仍不稳定则 fatal
    _CURL_MAX_ROUNDS = 10  # 最大轮次
    _CURL_REQ_INTERVAL = 10  # 每次请求之间的间隔（秒）
    _CURL_ROUND_WAIT = 10  # 本轮失败后等待下一轮的间隔（秒）

    for _round in range(1, _CURL_MAX_ROUNDS + 1):
        log_info(
            f"执行 Curl 健康检查（第 {_round}/{_CURL_MAX_ROUNDS} 轮，"
            f"共 {HEALTH_CHECK_CURL_COUNT} 次请求，每次间隔 {_CURL_REQ_INTERVAL}s）..."
        )
        round_passed = True  # 假设本轮通过，遇到失败立即置 False 并 break

        for _req_idx in range(1, HEALTH_CHECK_CURL_COUNT + 1):
            # 逐条发请求，方便记录每次结果
            single_curl = (
                f"curl -sk -o /dev/null "
                f"-w 'CURL_CHECK:%{{http_code}},%{{time_total}}\n' "
                f"'{HEALTH_CHECK_URL}' 2>/dev/null"
            )
            curl_output = shell.exec_command(single_curl, timeout=30)

            # 解析单次结果
            status_code, time_total = 0, 999.0
            for line in curl_output.split("\n"):
                if "CURL_CHECK:" not in line:
                    continue
                parts = line.strip().split("CURL_CHECK:")[-1].split(",")
                if len(parts) != 2:
                    continue
                try:
                    status_code = int(parts[0].strip())
                    time_total = float(parts[1].strip())
                except ValueError:
                    pass

            is_ok = status_code == 200
            is_fast = time_total <= HEALTH_CHECK_CURL_MAX_TIME

            log_info(
                f"  [{_req_idx}/{HEALTH_CHECK_CURL_COUNT}] "
                f"HTTP {status_code}, {time_total:.3f}s "
                f"{'✓' if is_ok and is_fast else '✗'}"
            )

            # 遇到慢响应或非 200，立即中断本轮，不再继续后续请求
            if not is_ok or not is_fast:
                round_passed = False
                log_warn(
                    f"  第 {_req_idx} 次请求不满足条件，中断本轮，"
                    f"{'响应码' if not is_ok else '耗时'} 异常"
                )
                break

            # 最后一次请求后不再等待
            if _req_idx < HEALTH_CHECK_CURL_COUNT:
                time.sleep(_CURL_REQ_INTERVAL)

        # 全部通过 → 退出大循环
        if round_passed:
            break

        # 本轮未通过
        if _round == _CURL_MAX_ROUNDS:
            fatal(
                f"Curl 健康检查失败：已进行 {_CURL_MAX_ROUNDS} 轮仍存在慢响应或非 200，"
                "设备响应不稳定，请检查 Agent 状态"
            )

        log_warn(
            f"本轮存在慢响应或非 200，{_CURL_ROUND_WAIT}s 后开始第 {_round + 1} 轮..."
        )
        time.sleep(_CURL_ROUND_WAIT)

    log_ok("所有健康检查通过")


def step_initialize(shell: TelnetShell, device_ip: str):
    """步骤 9：执行安装后初始化配置"""
    log_step(9, "执行初始化配置")

    # 公共重试辅助 ──────────────────────────────────────────────────────────

    def _exec_must_succeed(cmd: str, desc: str, timeout: int = 15, max_retry: int = 10):
        """执行命令，间隔 1s 最多重试 max_retry 次，始终失败则 fatal。"""
        for _i in range(max_retry):
            rc, out = shell.exec_command_checked(cmd, timeout=timeout)
            if rc == 0:
                log_ok(f"{desc} 成功")
                return
            log_warn(
                f"{desc} 失败 (退出码: {rc})，第 {_i + 1}/{max_retry} 次，1s 后重试..."
            )
            time.sleep(1)
        fatal(f"{desc} 经过 {max_retry} 次重试仍未成功，请检查设备状态")

    def _exec_with_backoff(cmd: str, desc: str, timeout: int = 15, max_retry: int = 5):
        """执行命令，指数退避重试，耗尽次数后仅警告继续（非关键命令）。"""
        for _i in range(max_retry):
            rc, out = shell.exec_command_checked(cmd, timeout=timeout)
            if rc == 0:
                log_ok(f"{desc} 成功")
                return
            wait = 2**_i  # 指数退避：1s, 2s, 4s, 8s, 16s
            log_warn(
                f"{desc} 失败 (退出码: {rc})，"
                f"第 {_i + 1}/{max_retry} 次，{wait}s 后重试..."
            )
            time.sleep(wait)
        log_warn(f"{desc} 经过 {max_retry} 次重试仍未成功，继续执行后续步骤")

    # ────────────────────────────────────────────────────────────────────────

    # 1. 关闭验证码（etcd 关键命令，失败则 fatal）
    log_info("关闭验证码...")
    verifycode_cmd = (
        "/opt/dbappsecurity/bin/etcdctl "
        '--user="root:$(cat /appdata/etc/etcdpwd)" '
        "put /vnf-agent/vpp1/api/v1/auth/verifycode "
        "'{\"verifycode\":false}'"
    )
    _exec_must_succeed(verifycode_cmd, "关闭验证码", timeout=15)

    # 2. 启用 SSH 并禁止自动关闭
    log_info("启用 SSH...")

    # 允许所有用户 SSH 访问
    _exec_with_backoff(
        "sed -i 's/^AllowUsers /#AllowUsers /g' /etc/ssh/sshd_config",
        "注释 AllowUsers",
        timeout=10,
    )
    time.sleep(1)

    # 重启 sshd
    _exec_with_backoff("service sshd restart", "重启 sshd", timeout=15)
    time.sleep(1)

    # 通过 etcdctl 启用 SSH（关键命令，失败则 fatal）
    _exec_must_succeed(
        "etcdctl put /vnf-agent/vpp1/config/sysconfig/v1/sshdconfig "
        '\'{"sshdport":22,"start":true}\'',
        "etcdctl 启用 SSH",
        timeout=10,
    )
    time.sleep(1)

    # 禁止 SSH 自动关闭定时任务
    _exec_with_backoff(
        "sed -i '/sshcheck\\.sh/s/^/#/' /etc/cron.d/0minly",
        "注释 sshcheck cron",
        timeout=10,
    )
    time.sleep(1)

    # 修改 sshcheck.sh，在第 2 行插入 exit 0
    sshcheck_cmd = (
        'FILE="/opt/dbappsecurity/bin/sshcheck.sh"; '
        'sed -n \'2p\' "$FILE" | grep -q "^exit 0$" || '
        "sed -i '2i\\exit 0' \"$FILE\""
    )
    _exec_with_backoff(sshcheck_cmd, "修改 sshcheck.sh", timeout=10)

    log_ok("SSH 已启用并禁止自动关闭")

    # 3. 配置管理路由
    log_info("配置管理路由...")
    shell.exec_command(MGMT_ROUTE, timeout=10)
    log_ok("管理路由已配置")

    # 4. 恢复 license 目录
    log_info("恢复 /root/license/ 目录到 /appdata/etc ...")
    exit_code, output = shell.exec_command_checked(
        r"\cp -r /root/license/ /appdata/etc",
        timeout=30,
    )
    if exit_code != 0:
        if REQUIRE_LICENSE_DIR:
            fatal(f"恢复 license 目录失败 (退出码: {exit_code}): {output}")
        else:
            log_warn(
                f"恢复 license 目录失败 (退出码: {exit_code}): {output}，"
                "REQUIRE_LICENSE_DIR=False，跳过并继续"
            )
    else:
        log_ok("license 目录已恢复至 /appdata/etc")

    log_ok("初始化配置完成")


def step_change_password(device_ip: str, new_password: str):
    """步骤 10：修改默认密码并验证登录（含重试机制）"""
    log_step(10, "修改默认密码并验证登录")

    base_url = f"https://{device_ip}"

    max_retries = 10
    retry_interval = 3  # 秒

    for attempt in range(1, max_retries + 1):
        try:
            log_info(f"尝试修改密码并验证登录（第 {attempt}/{max_retries} 次）...")
            result = web_login_with_auto_change_password(
                base_url=base_url,
                username=WEB_DEFAULT_USER,
                default_password=WEB_DEFAULT_PASS,
                new_password=new_password,
            )

            if "token" in result:
                token = result["token"]
                log_ok(f"Web 管理登录成功！Token: {token[:20]}...")

                # 配置 NTP 时间同步
                log_info("配置 NTP 时间同步服务器...")
                try:
                    systime_result = web_set_systime(base_url, token)
                    if systime_result.get("errCode", "") in ("", None, 0):
                        log_ok(f"NTP 时间同步配置成功: {systime_result}")
                    else:
                        log_warn(f"NTP 时间同步配置返回异常: {systime_result}")
                except Exception as e:
                    log_warn(f"NTP 时间同步配置请求失败: {e}")

                # 退出 Web 管理登录
                web_logout(base_url, token)

                log_ok("密码修改并验证完成")
                return
            else:
                log_fail(f"Web 管理登录失败: {result}")
                if attempt < max_retries:
                    log_info(f"将在 {retry_interval} 秒后重试...")
                    time.sleep(retry_interval)
                    continue
                else:
                    fatal("密码修改或登录验证失败，已达到最大重试次数")

        except Exception as e:
            log_warn(f"第 {attempt}/{max_retries} 次尝试出错: {e}")
            if attempt < max_retries:
                log_info(f"将在 {retry_interval} 秒后重试...")
                time.sleep(retry_interval)
            else:
                fatal(f"密码修改/登录验证过程出错，已重试 {max_retries} 次: {e}")


# ==================== 主流程 ====================


def main(
    serial_url: str = typer.Option(
        ...,
        "--serial-url",
        help="设备的串口地址，例如：telnet://<IP_ADDRESS>:10008",
    ),
    package_url: str = typer.Option(
        ...,
        "--package-url",
        help="安装包下载 URL，例如：ftp://<IP_ADDRESS>/.../TGFW-xxx.tar.gz",
    ),
    device_type: str = typer.Option(
        ...,
        "--device-type",
        help="目标设备型号，例如：DAS-TGFW-290",
    ),
    device_ip: str = typer.Option(
        ...,
        "--device-ip",
        help="目标设备的管理 IP（不带掩码），例如：<IP_ADDRESS>",
    ),
    password: str = typer.Option(
        WEB_NEW_PASS,
        "--password",
        help="修改后的 Web 管理密码",
    ),
    md5: str = typer.Option(
        "",
        "--md5",
        help="安装包的 MD5 校验值(可选)",
    ),
    ftp_user: str = typer.Option(
        "ngfw",
        "--ftp-user",
        help="FTP 下载认证用户名",
    ),
    ftp_password: str = typer.Option(
        "tgfw!@#@dbApp2022",
        "--ftp-password",
        help="FTP 下载认证密码",
    ),
):
    """
    TGFW 卸载安装工具。

    通过串口服务器远程完成 TGFW 的卸载、安装、健康检查和初始化配置。
    """
    # ── 根据串口服务器地址动态生成日志文件路径 ──────────────────────────────
    # 将 serial_url 中所有非字母/数字/点/连字符的字符替换为 _，得到合法文件名
    safe_serial = re.sub(r"[^A-Za-z0-9.\-]", "_", serial_url)
    # 去掉首尾多余的下划线，同时合并连续的下划线
    safe_serial = re.sub(r"_+", "_", safe_serial).strip("_")
    log_path = os.path.join(LOG_DIR, f"{safe_serial}.log")

    # 全局 file_logger 正式初始化（会自动创建 logs/ 目录）
    global file_logger, LOG_FILE
    LOG_FILE = log_path
    file_logger = _setup_file_logger(log_path)
    # ──────────────────────────────────────────────────────────────────────────

    print("=" * 60)
    print("TGFW 卸载安装工具")
    print("=" * 60)
    print(f"  串口服务器: {serial_url}")
    print(f"  安装包 URL: {package_url}")
    print(f"  设备类型:   {device_type}")
    print(f"  设备 IP:    {device_ip}")
    print(f"  目标密码:   {password}")
    print(f"  MD5 校验:   {md5 if md5 else '未提供'}")
    print(f"  FTP 用户:   {ftp_user}")
    print(f"  日志文件:   {log_path}")
    print("=" * 60)
    print()

    start_time = time.time()
    shell = None

    try:
        # 步骤 1：连接串口服务器
        shell = step_connect(serial_url)

        # 步骤 2：检查设备环境（返回值表示设备是否有管理 IP）
        has_ip = step_check_environment(shell, device_ip)

        # 步骤 3/4/5 流程因是否有管理 IP 而分叉：
        #
        # 有管理 IP（正常路径）：
        #   步骤 3：下载安装包 + MD5 校验（暂不解压）
        #   步骤 4：卸载旧版本
        #   步骤 3.5：将新包解压到 /opt（卸载后再解压，防止被卸载清除）
        #   步骤 5：安装新版本
        #
        # 无管理 IP（本地包路径）：
        #   step_use_local_package 内部已按顺序处理：卸载 → 解压
        #   步骤 5：安装新版本
        if has_ip:
            # 步骤 3：下载安装包并校验（不解压）
            pkg_filename = step_download_package(
                shell,
                package_url,
                expected_md5=md5,
                ftp_user=ftp_user,
                ftp_password=ftp_password,
            )

            # 步骤 4：卸载旧版本（在解压新包之前，防止卸载清除解压文件）
            step_uninstall(shell)

            # 步骤 3.5（卸载后）：将新安装包解压到 /opt 目录
            log_info("卸载完成，开始解压新安装包...")
            _extract_package(shell, pkg_filename)
        else:
            # 无管理 IP：step_use_local_package 内部已处理卸载+解压，此处跳过外层卸载步骤
            step_use_local_package(shell)

        # 步骤 5：安装新版本
        step_install(shell, device_type, device_ip)

        # 步骤 6：等待设备重启
        step_wait_reboot(shell)

        # 步骤 7：重启后登录
        step_post_reboot_login(shell)

        # 步骤 8：健康检查
        step_health_check(shell)

        # 步骤 9：初始化配置
        step_initialize(shell, device_ip)

        # 关闭串口连接
        shell.close()
        shell = None

        # 步骤 10：修改密码并验证
        step_change_password(device_ip, password)

        # 完成摘要
        elapsed = int(time.time() - start_time)
        print()
        print("=" * 60)
        print(f"[完成] TGFW 安装成功！总耗时: {elapsed} 秒")
        # 若使用了本地包，在结尾重点提示
        if _used_local_package:
            print()
            print("!" * 60)
            print("[重要提示] 本次安装检测到设备管理 IP 不可达！")
            print(f"           已直接使用 /opt/{_used_local_package} 进行安装。")
            print("           请在安装完成后，确认设备管理 IP 已正确配置。")
            print("!" * 60)
        print("=" * 60)

    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\n[中断] 用户取消操作")
        sys.exit(130)
    except Exception as e:
        print(f"\n[异常] 未预期的错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        if shell:
            try:
                shell.close()
            except Exception:
                pass


if __name__ == "__main__":
    typer.run(main)
