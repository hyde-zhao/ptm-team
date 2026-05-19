from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

import snappi

from traffic_skill.instrument.base import Instrument
from traffic_skill.instrument.ssh import ParamikoSshRunner
from traffic_skill.instrument.types import IxiaCConfig, IxCPort
from traffic_skill.models import IncrementItem, Traffic

logger = logging.getLogger(__name__)


class IxiaCInstrument(Instrument):
    def __init__(
        self,
        config: IxiaCConfig,
        ports: dict[str, IxCPort],
        *,
        verify: bool = False,
        config_file: str | Path = "traffic_config.json",
        api_factory: Callable[..., Any] = snappi.api,
        ssh_runner_factory: Callable[[IxiaCConfig], Any] = ParamikoSshRunner,
    ):
        self.config = config
        self.ports = ports
        self.config_file = Path(config_file)
        self._api = api_factory(location=f"https://{config.api_server}", verify=verify)
        self._ssh_runner_factory = ssh_runner_factory
        self._config = None

    def assign_ports(self) -> None:
        config = self._get_config()
        existing_names = {port.name for port in config.ports}
        for port in self.ports.values():
            if port.name not in existing_names:
                config.ports.add(name=port.name, location=f"{self.config.chassis_ip}:{port.socket_port}")
        self._set_config(config)

    def ensure_interface_addresses(self, port_names: list[str] | None = None) -> None:
        selected_ports = self._selected_ports(port_names)
        if not selected_ports:
            return
        runner = self._ssh_runner_factory(self.config)
        for port in selected_ports:
            if port.ip:
                self._configure_ip_address(runner, port.interface, port.ip, is_ipv6=False)
            if port.ipv6:
                self._configure_ip_address(runner, port.interface, port.ipv6, is_ipv6=True)

    def warmup_neighbor(self, port_name: str, target_ip: str) -> None:
        port = self._port_by_name(port_name)
        runner = self._ssh_runner_factory(self.config)
        command = (
            f"ip vrf exec {port.interface}_vrf ping -c 1 -W 1 -I {port.interface} {target_ip} "
            f"|| ping -c 1 -W 1 -I {port.interface} {target_ip} "
            f"|| true"
        )
        runner.run(command, check=False)

    def add_traffic(self, traffic: Traffic, name: str) -> None:
        if not name:
            raise ValueError("flow name is required")
        config = self._get_config()
        self._remove_flow_from_config(config, name, missing_ok=True)
        flow = config.flows.add(name=name)
        self._configure_flow(flow, traffic)
        flow.metrics.enable = True
        self._write_config_file(config)
        self._set_config(config)

    def start_traffic(self, names: str | list[str] | None = None) -> None:
        self.clear_statistics()
        self._set_flow_transmit_state(names, "START")

    def stop_traffic(self, names: str | list[str] | None = None) -> None:
        if len(self._get_config().flows) == 0:
            return
        self._set_flow_transmit_state(names, "STOP")

    def remove_traffic(self, name: str) -> None:
        if not name:
            raise ValueError("flow name is required")
        config = self._get_config()
        self._remove_flow_from_config(config, name, missing_ok=False)
        self._write_config_file(config)
        self._set_config(config)

    def get_flow_statistics(self, names: str | list[str] | None = None) -> list[Any]:
        req = self._api.metrics_request()
        req.flow.flow_names = self._normalize_names(names)
        return list(self._api.get_metrics(req).flow_metrics)

    def get_flow_state(self, name: str) -> str:
        metrics = self.get_flow_statistics(name)
        if not metrics:
            raise ValueError(f"flow {name!r} not found")
        return metrics[0].transmit

    def get_port_statistics(self, names: str | list[str] | None = None) -> list[Any]:
        req = self._api.metrics_request()
        req.port.port_names = self._normalize_names(names)
        return list(self._api.get_metrics(req).port_metrics)

    def clear_statistics(self) -> None:
        self._set_config(self._get_config())

    def _configure_flow(self, flow: Any, traffic: Traffic) -> None:
        flow.tx_rx.port.tx_name = traffic.tx_link.TG.port_name
        flow.tx_rx.port.rx_names = [traffic.rx_link.TG.port_name]

        if traffic.frame_size_mode == "fixed":
            flow.size.fixed = int(traffic.frame_size)
        elif traffic.frame_size_mode != "auto":
            raise ValueError("frame_size_mode must be fixed or auto")

        if traffic.trans_mode == Traffic.COUNT:
            flow.duration.choice = flow.duration.FIXED_PACKETS
            flow.duration.fixed_packets.packets = int(traffic.frame_count)
        elif traffic.trans_mode == Traffic.CONTINUOUS:
            flow.duration.choice = flow.duration.CONTINUOUS
        else:
            raise ValueError(f"Ixia-C does not support trans_mode {traffic.trans_mode!r}")

        if traffic.rate_mode == "pps":
            flow.rate.pps = int(traffic.pps)
        elif traffic.rate_mode == "line":
            flow.rate.choice = flow.rate.PERCENTAGE
            flow.rate.percentage = int(traffic.line_rate)
        else:
            raise ValueError("rate_mode must be pps or line")

        eth = flow.packet.ethernet()[-1]
        self._set_field(eth.dst, traffic.dst_mac_value if traffic.dst_mac_type == Traffic.SINGLE else traffic.dst_mac_increment)
        self._set_field(eth.src, traffic.src_mac_value if traffic.src_mac_type == Traffic.SINGLE else traffic.src_mac_increment)
        if traffic.ethernet_type:
            self._set_field(eth.ether_type, traffic.ethernet_type)
        if traffic.crc:
            raise ValueError("Ixia-C does not support invalid CRC configuration")

        self._configure_vlan(flow, traffic)
        self._configure_l3(flow, traffic)
        self._configure_l4(flow, traffic)

    def _configure_vlan(self, flow: Any, traffic: Traffic) -> None:
        if not traffic.vlan_ids:
            return
        vlan_ids = traffic.vlan_ids if isinstance(traffic.vlan_ids, list) else [traffic.vlan_ids]
        for index in range(len(vlan_ids) - 1, -1, -1):
            vlan = flow.packet.vlan()[-1]
            self._set_field(vlan.id, vlan_ids[index])
            self._set_optional_indexed(vlan.priority, traffic.vlan_priority, index)
            self._set_optional_indexed(vlan.cfi, traffic.vlan_cfi, index)
            self._set_optional_indexed(vlan.tpid, traffic.vlan_protocol, index)

    def _configure_l3(self, flow: Any, traffic: Traffic) -> None:
        if traffic.l3_header == Traffic.L3_HEADER_IPV4:
            ipv4 = flow.packet.ipv4()[-1]
            self._set_field(ipv4.src, traffic.src_ipv4_value if traffic.src_ipv4_type == Traffic.SINGLE else traffic.src_ipv4_increment)
            self._set_field(ipv4.dst, traffic.dst_ipv4_value if traffic.dst_ipv4_type == Traffic.SINGLE else traffic.dst_ipv4_increment)
            if traffic.ttl:
                self._set_field(ipv4.time_to_live, traffic.ttl)
            if traffic.protocol:
                self._set_field(ipv4.protocol, traffic.protocol)
        elif traffic.l3_header == Traffic.L3_HEADER_IPV6:
            ipv6 = flow.packet.ipv6()[-1]
            self._set_field(ipv6.src, traffic.src_ipv6_value if traffic.src_ipv6_type == Traffic.SINGLE else traffic.src_ipv6_increment)
            self._set_field(ipv6.dst, traffic.dst_ipv6_value if traffic.dst_ipv6_type == Traffic.SINGLE else traffic.dst_ipv6_increment)
            if traffic.hop_limit:
                self._set_field(ipv6.hop_limit, traffic.hop_limit)
        elif traffic.l3_header == Traffic.L3_HEADER_ARP:
            arp = flow.packet.arp()[-1]
            self._set_field(arp.sender_hardware_addr, traffic.sender_hardware_address_value)
            self._set_field(arp.sender_protocol_addr, traffic.sender_protocol_address_value)
            self._set_field(arp.target_hardware_addr, traffic.target_hardware_address_value)
            self._set_field(arp.target_protocol_addr, traffic.target_protocol_address_value)

    def _configure_l4(self, flow: Any, traffic: Traffic) -> None:
        if traffic.l4_header == Traffic.L4_HEADER_TCP:
            tcp = flow.packet.tcp()[-1]
            self._set_field(tcp.src_port, traffic.tcp_src_port_value if traffic.tcp_src_port_type == Traffic.SINGLE else traffic.tcp_src_port_increment)
            self._set_field(tcp.dst_port, traffic.tcp_dst_port_value if traffic.tcp_dst_port_type == Traffic.SINGLE else traffic.tcp_dst_port_increment)
        elif traffic.l4_header == Traffic.L4_HEADER_UDP:
            udp = flow.packet.udp()[-1]
            self._set_field(udp.src_port, traffic.udp_src_port_value if traffic.udp_src_port_type == Traffic.SINGLE else traffic.udp_src_port_increment)
            self._set_field(udp.dst_port, traffic.udp_dst_port_value if traffic.udp_dst_port_type == Traffic.SINGLE else traffic.udp_dst_port_increment)
        elif traffic.l4_header == Traffic.L4_HEADER_ICMP:
            icmp = flow.packet.icmp()[-1]
            self._set_field(icmp.echo.type, traffic.icmp_message_type)
            self._set_field(icmp.echo.code, traffic.icmp_message_code_value)
        elif traffic.l4_header == Traffic.L4_HEADER_ICMP_V6:
            icmpv6 = flow.packet.icmpv6()[-1]
            self._set_field(icmpv6.echo.type, traffic.icmp_v6_message_type)

    def _set_flow_transmit_state(self, names: str | list[str] | None, state_attr: str) -> None:
        cs = self._api.control_state()
        cs.choice = cs.TRAFFIC
        cs.traffic.flow_transmit.flow_names = self._normalize_names(names)
        cs.traffic.flow_transmit.state = getattr(cs.traffic.flow_transmit, state_attr)
        self._api.set_control_state(cs)

    def _selected_ports(self, port_names: list[str] | None):
        if port_names is None:
            return list(self.ports.values())
        wanted = set(port_names)
        return [port for port in self.ports.values() if port.name in wanted]

    def _port_by_name(self, port_name: str) -> IxCPort:
        for port in self.ports.values():
            if port.name == port_name:
                return port
        raise ValueError(f"port {port_name!r} not found")

    @staticmethod
    def _configure_ip_address(runner, interface: str, ip_addr: str, *, is_ipv6: bool) -> None:
        family = "-6 " if is_ipv6 else ""
        command = (
            f"ip {family}addr replace {ip_addr} dev {interface} "
            f"|| ip {family}addr replace {ip_addr} dev {interface}_vrf"
        )
        runner.run(command)

    def _get_config(self):
        if self._config is not None:
            return self._config
        try:
            self._config = self._api.get_config()
        except TypeError as exc:
            if "expected uint32" not in str(exc):
                raise
            raw_config = self._api._transport.send_recv("get", "/config", payload=None, return_object=None)
            normalized_config = self._normalize_numeric_strings(raw_config)
            self._config = self._api.config().deserialize(normalized_config)
        return self._config

    def _set_config(self, config) -> None:
        self._config = config
        self._api.set_config(config)

    def _write_config_file(self, config) -> None:
        self.config_file.write_text(config.serialize(encoding=config.JSON), encoding="utf-8")

    @staticmethod
    def _remove_flow_from_config(config, name: str, *, missing_ok: bool) -> None:
        for index, flow in enumerate(list(config.flows)):
            if flow.name == name:
                config.flows.remove(index)
                return
        if not missing_ok:
            raise ValueError(f"flow {name!r} not found")

    @staticmethod
    def _set_field(field, value) -> None:
        if isinstance(value, IncrementItem):
            field.increment.start = IxiaCInstrument._coerce_numeric(value.start)
            field.increment.step = IxiaCInstrument._coerce_numeric(value.step)
            field.increment.count = IxiaCInstrument._coerce_numeric(value.count)
        else:
            field.value = IxiaCInstrument._coerce_numeric(value)

    @staticmethod
    def _set_optional_indexed(field, value, index: int) -> None:
        if value is None:
            return
        if isinstance(value, list):
            if index < len(value):
                IxiaCInstrument._set_field(field, value[index])
        else:
            IxiaCInstrument._set_field(field, value)

    @staticmethod
    def _coerce_numeric(value):
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value

    @staticmethod
    def _normalize_names(names: str | list[str] | None) -> list[str] | None:
        if names is None:
            return None
        if isinstance(names, str):
            return [names]
        return names

    @staticmethod
    def _normalize_numeric_strings(value):
        if isinstance(value, dict):
            return {key: IxiaCInstrument._normalize_numeric_strings(item) for key, item in value.items()}
        if isinstance(value, list):
            return [IxiaCInstrument._normalize_numeric_strings(item) for item in value]
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value
