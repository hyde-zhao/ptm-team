# TGFW 卸载安装工具需求

我需要设计一个 CLI 工具，用于快捷的卸载和安装 TGFW（也叫ngfw）

## 卸载安装流程简述

因为你操作的目标实际上是一个工控机，而你无法直接操作它，而是要通过串口服务器来操作。所以整个流程首先是使用 telnet 协议连接到串口服务器，检查目标环境是否满足要求。

首先检测当前串口服务器连接的设备是不是目标设备，可以通过 IP 和 CPU 型号来判断，然后再检查当前设备是否满足安装条件，比如： 检查 /root/license/ 目录是否存在

再把 /opt 目录下的所有 *.tar.gz 其他多余的安装包删除掉，根据我提供的下载链接，把安装包下载到 /opt 目录下，再使用 md5sum 校验安装包的完整性。

使用 /opt/dbappsecurity/bin/ngfwuninstall 卸载当前版本的 TGFW 软件，然后再使用 tar 把安装包解压到 /otp 目录下去，再使用 /opt/dbappsecurity/bin/ngfwinstall -t <device_type> -i <ip> -m 22 --disable_backup 安装

整个安装过程比较久，可能需要 10 分钟以上，同时还会自动重启，所以过程中需要间隔一段时间再及时反馈状态。

再安装完毕之后，需要使用用户名 root 密码 ngfw123!@# 登录到 shell 中去，然后分别使用以下命令检查进程的运行状态

- /opt/dbappsecurity/bin/health-check/vpp-health-check.sh  执行了之后需要使用 echo $? 来判断是否成功，如果返回 0 则表示成功，否则表示失败。
- /opt/dbappsecurity/bin/health-check/agent-health-check.sh  执行了之后需要使用 echo $? 来判断是否成功，如果返回 0 则表示成功，否则表示失败。
- 然后再使用 curl 连续请求 10 次 https://127.0.0.1/api/v1/getAuthConfig 并判断返回状态码是否为 200，以及请求的总耗时是否在 0.1s 之内

这个之后就说明安装成功了

然后再执行安装之后的初始化操作

关闭验证码

/opt/dbappsecurity/bin/etcdctl --user="root:$(cat /appdata/etc/etcdpwd)" put /vnf-agent/vpp1/api/v1/auth/verifycode '{"verifycode":false}'


启用 ssh，并禁止 ssh 自动关闭
```shell
sed -i 's/^AllowUsers /#AllowUsers /g' /etc/ssh/sshd_config
service sshd restart
etcdctl put /vnf-agent/vpp1/config/sysconfig/v1/sshdconfig '{"sshdport":22,"start":true}'
sed -i '/sshcheck\.sh/s/^/#/' /etc/cron.d/0minly
FILE="/opt/dbappsecurity/bin/sshcheck.sh"; sed -n '2p' "$FILE" | grep -q "^exit 0$" || sed -i '2i\exit 0' "$FILE"
```

配置管理路由

ip route add <IP_ADDRESS>/23 via <IP_ADDRESS> metric 2

然后就可以关闭串口服务器的连接了。


然后再使用 Python 传统的 requests 并修改默认密码，并尝试登录看看能不能成功，这个逻辑可以参考以下脚本，如果能够成功的话，就说明安装好了

```python
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "requests",
#     "cryptography",
# ]
# ///

"""
防火墙密码加密工具（纯 Python 实现）

功能说明：
  1. 从防火墙 Web 页面自动获取 RSA 公钥
  2. 使用 RSA 公钥对明文密码进行加密
  3. 将加密后的密文转换为 Base64 编码字符串

加密流程：
  - 访问防火墙的 index.html 页面
  - 从 HTML 中用正则匹配找到 ras_public_key.*.js 的 JS 文件路径
  - 请求该 JS 文件，解析出 PEM 格式的 RSA 公钥
  - 使用 RSA 公钥 + PKCS1v15 填充 对明文进行加密
  - 对加密后的二进制数据进行 Base64 编码，返回密文字符串

依赖：
  pip install requests cryptography

用法：
  from encrypt_password import encrypt_password
  ciphertext = encrypt_password("https://<IP_ADDRESS>:443", "your_password")
"""

import re
import base64

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

# 禁用 SSL 不安全请求的告警
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


def get_rsa_pub_key(base_url: str) -> str:
    """
    从防火墙 Web 页面获取 RSA 公钥（PEM 格式字符串）

    :param base_url: 防火墙的基础 URL，例如 https://<IP_ADDRESS>:443
    :return: PEM 格式的公钥字符串
    :raises RuntimeError: 无法访问页面或获取公钥失败时抛出
    """
    # 去除末尾斜杠，确保 URL 格式统一
    base_url = base_url.rstrip("/")

    # 第一步：访问 index.html 获取公钥 JS 文件的路径
    index_url = base_url + "/index.html"
    response = requests.get(index_url, timeout=10, verify=False)
    if response.status_code != 200:
        raise RuntimeError(
            f"无法访问 {index_url}，HTTP 状态码: {response.status_code}，"
            f"请检查防火墙 IP 和端口是否正确"
        )

    html_content = response.text

    # 第二步：用正则表达式从 HTML 中匹配公钥 JS 文件路径
    pattern = re.compile(r'src="(/js/ras_public_key.\d+.js)"')
    matches = pattern.findall(html_content)

    if not matches:
        raise RuntimeError(
            "在 index.html 中未找到公钥 JS 文件引用，"
            "请确认防火墙已启用非对称加密功能"
        )

    # 第三步：请求公钥 JS 文件并解析出 PEM 公钥
    js_path = matches[0]
    js_url = base_url + js_path
    js_response = requests.get(js_url, timeout=10, verify=False)
    if js_response.status_code != 200:
        raise RuntimeError(
            f"获取公钥 JS 文件失败，HTTP 状态码: {js_response.status_code}，"
            f"请在 TGFW Linux 后台使用 "
            f"/opt/dbappsecurity/bin/bash-cli/app/auth/pubkey-encrypt enable "
            f"启用非对称加密后重试"
        )

    js_content = js_response.text

    # 解析 JS 内容，提取 PEM 公钥
    # JS 文件内容类似：var __PUBLIC_KEY__ =  '-----BEGIN PUBLIC KEY-----\n' + 'xxxx\n' + ...
    pub_key = (
        js_content
        .replace("\\n' +", "")
        .replace("var __PUBLIC_KEY__ =  ", "")
        .replace("'", "")
        .replace("  ", "")
        .strip()
    )

    return pub_key


def encrypt_password(base_url: str, plaintext: str) -> str:
    """
    使用防火墙的 RSA 公钥对明文密码进行加密，返回 Base64 编码的密文

    加密方式与原始代码中 openssl pkeyutl -encrypt 命令等价，
    使用 PKCS1v15 填充方式进行 RSA 加密。

    :param base_url: 防火墙的基础 URL，例如 https://<IP_ADDRESS>:443
    :param plaintext: 明文密码
    :return: Base64 编码的加密密文字符串
    """
    # 获取 PEM 格式的公钥字符串
    pub_key_pem = get_rsa_pub_key(base_url)

    # 将 PEM 字符串加载为公钥对象
    public_key = serialization.load_pem_public_key(pub_key_pem.encode("utf-8"))

    # 使用 RSA 公钥 + PKCS1v15 填充方式加密明文
    # 注意：openssl pkeyutl -encrypt 默认使用 PKCS1v15 填充
    encrypted_bytes = public_key.encrypt(
        plaintext.encode("utf-8"),
        padding.PKCS1v15()
    )

    # 将加密后的二进制数据转为 Base64 编码字符串（不换行）
    base64_output = base64.b64encode(encrypted_bytes).decode("utf-8")

    return base64_output


def login(base_url: str, username: str, password_plain: str) -> dict:
    """
    使用加密后的密码登录防火墙，返回登录响应

    :param base_url: 防火墙的基础 URL，例如 https://<IP_ADDRESS>
    :param username: 登录用户名
    :param password_plain: 明文密码
    :return: 登录接口返回的 JSON 响应（包含 token 等信息）
    """
    # 第一步：加密密码
    encrypted_passwd = encrypt_password(base_url, password_plain)
    print(f"密码加密完成，密文长度: {len(encrypted_passwd)}")

    # 第二步：构造登录请求体
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

    # 第三步：发送登录请求
    login_url = base_url.rstrip("/") + "/api/v1/auth"
    print(f"正在登录: PUT {login_url}")
    response = requests.put(login_url, json=payload, timeout=10, verify=False)

    print(f"响应状态码: {response.status_code}")
    resp_json = response.json()
    print(f"响应内容: {resp_json}")

    return resp_json


def change_default_password(base_url: str, username: str, old_password_plain: str, new_password_plain: str) -> dict:
    """
    修改防火墙的默认密码

    :param base_url: 防火墙的基础 URL，例如 https://<IP_ADDRESS>
    :param username: 用户名
    :param old_password_plain: 旧密码明文
    :param new_password_plain: 新密码明文
    :return: 修改密码接口返回的 JSON 响应
    """
    # 分别加密新旧密码
    encrypted_old_passwd = encrypt_password(base_url, old_password_plain)
    encrypted_new_passwd = encrypt_password(base_url, new_password_plain)

    # 构造修改密码的请求体
    payload = {
        "id": username,
        "val": {
            "username": username,
            "passwd": encrypted_new_passwd,
            "oldpasswd": encrypted_old_passwd,
        },
    }

    # 发送修改密码请求
    change_pwd_url = base_url.rstrip("/") + "/api/v1/changeDefPwd"
    print(f"正在修改默认密码: PUT {change_pwd_url}")
    response = requests.put(change_pwd_url, json=payload, timeout=10, verify=False)

    print(f"响应状态码: {response.status_code}")
    resp_json = response.json()
    print(f"响应内容: {resp_json}")

    return resp_json


def login_with_auto_change_password(
    base_url: str,
    username: str = "admin",
    default_password: str = "admin",
    new_password: str = "Ngfw123!@#",
) -> dict:
    """
    自动处理默认密码修改的登录流程：
      1. 先用默认密码尝试登录
      2. 如果返回 eChangDeafPwd（需要修改默认密码），则自动修改密码
      3. 最后用新密码完成登录

    :param base_url: 防火墙的基础 URL
    :param username: 用户名，默认 admin
    :param default_password: 默认密码明文，默认 admin
    :param new_password: 新密码明文，默认 Ngfw123!@#
    :return: 最终登录成功的 JSON 响应（包含 token）
    """
    # 第一步：尝试使用默认密码登录
    print("=" * 50)
    print("第一步：尝试使用默认密码登录")
    print("=" * 50)
    result = login(base_url, username, default_password)

    # 第二步：检查是否需要修改默认密码
    if result.get("errCode") == "eChangDeafPwd":
        print(f"\n检测到需要修改默认密码: {result.get('errMsg')}")

        print("\n" + "=" * 50)
        print("第二步：修改默认密码")
        print("=" * 50)
        change_result = change_default_password(base_url, username, default_password, new_password)

        # 检查修改密码是否成功
        if change_result.get("errCode"):
            raise RuntimeError(f"修改默认密码失败: {change_result}")
        print("默认密码修改成功!")

        # 第三步：使用新密码登录
        print("\n" + "=" * 50)
        print("第三步：使用新密码登录")
        print("=" * 50)
        result = login(base_url, username, new_password)

    elif "token" in result:
        print("\n使用默认密码直接登录成功，无需修改密码")
    else:
        # 默认密码登录失败但不是需要改密码的错误，尝试用新密码登录
        print(f"\n默认密码登录失败: {result.get('errMsg', '未知错误')}")
        print("\n" + "=" * 50)
        print("尝试使用新密码登录")
        print("=" * 50)
        result = login(base_url, username, new_password)

    return result


if __name__ == "__main__":
    # ===== 配置区域 =====
    BASE_URL = "https://<IP_ADDRESS>"
    USERNAME = "admin"
    DEFAULT_PASSWORD = "admin"
    NEW_PASSWORD = "Ngfw123!@#"
    # ====================

    try:
        result = login_with_auto_change_password(
            base_url=BASE_URL,
            username=USERNAME,
            default_password=DEFAULT_PASSWORD,
            new_password=NEW_PASSWORD,
        )
        if "token" in result:
            print(f"\n✅ 登录成功! Token: {result['token']}")
        else:
            print(f"\n❌ 登录失败: {result}")
    except Exception as e:
        print(f"\n❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
```

## 技术要求

你开发的是一个单 Python 脚本文件，使用 uv add script 来管理依赖，使用 uv run 来执行脚本。

然后使用的 CLI 框架是 Typer，同时建议你设置 TYPER_USE_RICH 为 False，因为这个工具主要是给 Agent 调用的，不希望有花里胡哨的输出，节省 Token

要求这个 CLI 接受以下参数
- 串口服务器地址，必填：例如：telnet://<IP_ADDRESS>:10008
- 安装包URL，必填：例如：ftp://<IP_ADDRESS>/ngfw/images/V6R01C02B006/TGFW-V6R01C02B006-arm-install-release-20260327154239.tar.gz
- 目标设备类型，必填：例如：DAS-TGFW-290
- 目标设备IP，必填：例如：<IP_ADDRESS>
- 修改之后的密码，可选，默认是：Ngfw123!@#
