from __future__ import annotations

import re
from ipaddress import ip_address
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

TEMPLATE_RE = re.compile(r"^[a-z0-9_-]+$")
RATE_RE = re.compile(r"^[1-9][0-9]*(pps|kbps|mbps|gbps)$", re.IGNORECASE)


class InterfaceConfig(BaseModel):
    port: str
    ip: str
    gateway: str
    mac: str | None = None
    peer_mac: str | None = None
    vlan: str | None = None

    @model_validator(mode="after")
    def validate_ip_pair(self) -> "InterfaceConfig":
        ip_version = ip_address(self.ip).version
        gateway_version = ip_address(self.gateway).version
        if ip_version != gateway_version:
            raise ValueError("interface ip and gateway must use the same IP version")
        return self


class ConfigInterfaceRequest(BaseModel):
    interfaces: list[InterfaceConfig] = Field(min_length=1)


class ApplyTrafficTemplateRequest(BaseModel):
    template: str
    tx_port: str
    rx_port: str
    ip_version: Literal["ipv4", "ipv6"] = "ipv4"
    l4_protocol: Literal["tcp", "udp"]
    l4_sport: int = Field(ge=0, le=65535)
    l4_dport: int = Field(ge=0, le=65535)
    traffic_mode: Literal["count", "continuous"]
    rate: str
    count: int | None = Field(default=None, gt=0)
    frame_size: int | None = Field(default=None, ge=64)
    vlan: str | None = None
    src_ip: str | None = None
    dst_ip: str | None = None
    src_mac: str | None = None
    dst_mac: str | None = None

    @field_validator("template")
    @classmethod
    def validate_template(cls, value: str) -> str:
        if not TEMPLATE_RE.fullmatch(value):
            raise ValueError("template must match ^[a-z0-9_-]+$")
        return value

    @field_validator("rate")
    @classmethod
    def validate_rate(cls, value: str) -> str:
        if not RATE_RE.fullmatch(value):
            raise ValueError("rate must use TRex-style units such as 100pps or 10mbps")
        return value

    @model_validator(mode="after")
    def validate_mode_fields(self) -> "ApplyTrafficTemplateRequest":
        if self.traffic_mode == "count" and self.count is None:
            raise ValueError("count is required when traffic_mode=count")
        expected_version = 6 if self.ip_version == "ipv6" else 4
        if self.src_ip is not None and self.dst_ip is not None:
            src_version = ip_address(self.src_ip).version
            dst_version = ip_address(self.dst_ip).version
            if src_version != dst_version:
                raise ValueError("src_ip and dst_ip must use the same IP version")
            if src_version != expected_version:
                raise ValueError("IP addresses do not match ip_version")
        elif self.ip_version == "ipv6":
            raise ValueError("IPv6 traffic requires both src_ip and dst_ip")
        elif any(
            value is not None and ip_address(value).version != expected_version
            for value in (self.src_ip, self.dst_ip)
        ):
            raise ValueError("IP addresses do not match ip_version")
        return self


class StartTrafficStreamRequest(BaseModel):
    ports: list[str] = Field(min_length=1)
    txport: str
    rxport: str
    template: str
    name: str

    @field_validator("template")
    @classmethod
    def validate_template(cls, value: str) -> str:
        if not TEMPLATE_RE.fullmatch(value):
            raise ValueError("template must match ^[a-z0-9_-]+$")
        return value

    @model_validator(mode="after")
    def validate_ports(self) -> "StartTrafficStreamRequest":
        if self.txport == self.rxport:
            raise ValueError("txport and rxport must be different")
        if self.txport not in self.ports or self.rxport not in self.ports:
            raise ValueError("txport and rxport must both be included in ports")
        return self


class VerifyTrafficLossRequest(BaseModel):
    ports: list[str] = Field(min_length=1)
    txport: str
    rxport: str
    name: str
    max_loss: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_ports(self) -> "VerifyTrafficLossRequest":
        if self.txport == self.rxport:
            raise ValueError("txport and rxport must be different")
        if self.txport not in self.ports or self.rxport not in self.ports:
            raise ValueError("txport and rxport must both be included in ports")
        return self


class StopTrafficStreamRequest(BaseModel):
    ports: list[str] = Field(min_length=1)
    txport: str
    rxport: str
    name: str

    @model_validator(mode="after")
    def validate_ports(self) -> "StopTrafficStreamRequest":
        if self.txport == self.rxport:
            raise ValueError("txport and rxport must be different")
        if self.txport not in self.ports or self.rxport not in self.ports:
            raise ValueError("txport and rxport must both be included in ports")
        return self


class DeleteTrafficTemplateRequest(BaseModel):
    template: str

    @field_validator("template")
    @classmethod
    def validate_template(cls, value: str) -> str:
        if not TEMPLATE_RE.fullmatch(value):
            raise ValueError("template must match ^[a-z0-9_-]+$")
        return value
