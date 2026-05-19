from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from traffic_skill.models import Traffic


class Instrument(ABC):
    @abstractmethod
    def assign_ports(self) -> None:
        pass

    @abstractmethod
    def ensure_interface_addresses(self, port_names: list[str] | None = None) -> None:
        pass

    @abstractmethod
    def warmup_neighbor(self, port_name: str, target_ip: str) -> None:
        pass

    @abstractmethod
    def add_traffic(self, traffic: Traffic, name: str) -> None:
        pass

    @abstractmethod
    def start_traffic(self, names: str | list[str] | None = None) -> None:
        pass

    @abstractmethod
    def stop_traffic(self, names: str | list[str] | None = None) -> None:
        pass

    @abstractmethod
    def remove_traffic(self, name: str) -> None:
        pass

    @abstractmethod
    def get_flow_statistics(self, names: str | list[str] | None = None) -> list[Any]:
        pass

    @abstractmethod
    def get_flow_state(self, name: str) -> str:
        pass

    @abstractmethod
    def get_port_statistics(self, names: str | list[str] | None = None) -> list[Any]:
        pass

    @abstractmethod
    def clear_statistics(self) -> None:
        pass
