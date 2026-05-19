from __future__ import annotations

from dataclasses import dataclass

import paramiko

from traffic_skill.instrument.types import IxiaCConfig


class SshCommandError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    command: str
    exit_status: int
    stdout: str
    stderr: str


class ParamikoSshRunner:
    def __init__(self, config: IxiaCConfig, *, timeout: int = 10):
        self.config = config
        self.timeout = timeout

    def run(self, command: str, *, check: bool = True) -> CommandResult:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.config.ssh_host,
                port=self.config.ssh_port,
                username=self.config.ssh_username,
                password=self.config.ssh_password,
                timeout=self.timeout,
                banner_timeout=self.timeout,
                auth_timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            _, stdout, stderr = client.exec_command(command, timeout=self.timeout)
            exit_status = stdout.channel.recv_exit_status()
            result = CommandResult(
                command=command,
                exit_status=exit_status,
                stdout=stdout.read().decode("utf-8", errors="replace"),
                stderr=stderr.read().decode("utf-8", errors="replace"),
            )
            if check and result.exit_status != 0:
                raise SshCommandError(
                    f"SSH command failed with exit {result.exit_status}: {command}; stderr={result.stderr.strip()}"
                )
            return result
        finally:
            client.close()
