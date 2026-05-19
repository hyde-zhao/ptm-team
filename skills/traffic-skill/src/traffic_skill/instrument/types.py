from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IxCPort:
    socket_port: int
    name: str
    interface: str
    type: str
    tg_node_key: str
    ip: str = ""
    ipv6: str = ""


@dataclass(frozen=True)
class IxiaCConfig:
    node_key: str
    node_name: str
    chassis_ip: str
    api_server: str
    ssh_host: str
    ssh_port: int
    ssh_username: str
    ssh_password: str
