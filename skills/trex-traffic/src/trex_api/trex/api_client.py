from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path
from typing import Any, Protocol

from trex_api.schemas import InterfaceConfig, StartTrafficStreamRequest, StopTrafficStreamRequest
from trex_api.trex.template_renderer import read_template_yaml


class TrexClient(Protocol):
    def configure_interfaces(self, interfaces: list[InterfaceConfig]) -> list[dict[str, Any]]: ...

    def start_stream(self, request: StartTrafficStreamRequest, template_path: Path) -> dict[str, Any]: ...

    def get_port_stats(self, ports: list[str]) -> dict[str, Any]: ...

    def stop_stream(self, request: StopTrafficStreamRequest) -> dict[str, Any]: ...


class SimulatedTrexClient:
    def __init__(self) -> None:
        self.interfaces: dict[str, dict[str, Any]] = {}
        self.streams: dict[str, dict[str, Any]] = {}
        self.stats: dict[str, dict[str, int]] = {}

    def configure_interfaces(self, interfaces: list[InterfaceConfig]) -> list[dict[str, Any]]:
        result = []
        for item in interfaces:
            gateway_mac = item.peer_mac or _fake_gateway_mac(item.port)
            data = item.model_dump()
            version = ip_address(item.ip).version
            data.update(
                {
                    "ip_version": f"ipv{version}",
                    "gateway_mac": gateway_mac,
                    "neighbor_protocol": "arp" if version == 4 else "nd",
                    "neighbor_learned": True,
                    "arp_learned": version == 4,
                    "nd_learned": version == 6,
                    "neighbor_state": "REACHABLE",
                }
            )
            self.interfaces[item.port] = data
            self.stats.setdefault(item.port, {"opackets": 0, "ipackets": 0})
            result.append(data)
        return result

    def start_stream(self, request: StartTrafficStreamRequest, template_path: Path) -> dict[str, Any]:
        template = read_template_yaml(template_path)
        traffic = template.get("traffic", {})
        count = int(traffic.get("count") or 300)
        self.streams[request.name] = {
            "name": request.name,
            "template": request.template,
            "txport": request.txport,
            "rxport": request.rxport,
            "state": "running",
            "count": count,
        }
        self.stats.setdefault(request.txport, {"opackets": 0, "ipackets": 0})
        self.stats.setdefault(request.rxport, {"opackets": 0, "ipackets": 0})
        self.stats[request.txport]["opackets"] += count
        self.stats[request.rxport]["ipackets"] += count
        return dict(self.streams[request.name])

    def get_port_stats(self, ports: list[str]) -> dict[str, Any]:
        return {port: self.stats.get(port, {"opackets": 0, "ipackets": 0}) for port in ports}

    def stop_stream(self, request: StopTrafficStreamRequest) -> dict[str, Any]:
        stream = self.streams.pop(request.name, None)
        return {"name": request.name, "stopped": stream is not None, "cleaned": stream is not None}


class TrexPythonApiClient:
    def __init__(self, server: str = "127.0.0.1") -> None:
        self.server = server
        self._client: Any | None = None
        self.interfaces: dict[str, dict[str, Any]] = {}

    def _get_client(self) -> Any:
        if self._client is None:
            api = _load_trex_api()
            self._client = api.STLClient(server=self.server)
        if not self._client.is_connected():
            self._client.connect()
        return self._client

    def configure_interfaces(self, interfaces: list[InterfaceConfig]) -> list[dict[str, Any]]:
        client = self._get_client()
        ports = [int(item.port) for item in interfaces]
        try:
            client.acquire(ports=ports, force=True)
            client.set_service_mode(ports=ports, enabled=True)
            results = []
            for item in interfaces:
                port = int(item.port)
                version = ip_address(item.ip).version
                if version == 4:
                    client.set_l3_mode(
                        port=port,
                        src_ipv4=item.ip,
                        dst_ipv4=item.gateway,
                        vlan=_parse_vlan(item.vlan),
                    )
                    port_info = client.get_port_info(ports=[port])[0]
                    gateway_mac = port_info.get("arp")
                    neighbor_state = "REACHABLE" if gateway_mac else "UNREACHABLE"
                else:
                    service_class = _load_ipv6_nd_service()
                    context = client.create_service_ctx(port=port)
                    service = service_class(
                        context,
                        dst_ip=item.gateway,
                        src_ip=item.ip,
                        src_mac=item.mac,
                        vlan=_parse_vlan(item.vlan),
                        retries=2,
                        timeout=2,
                        verify_timeout=1,
                    )
                    context.run(service)
                    record = service.get_record()
                    gateway_mac = record.dst_mac
                    neighbor_state = record.state
                data = item.model_dump()
                data.update(
                    {
                        "ip_version": f"ipv{version}",
                        "gateway_mac": gateway_mac,
                        "neighbor_protocol": "arp" if version == 4 else "nd",
                        "neighbor_learned": gateway_mac is not None,
                        "arp_learned": version == 4 and gateway_mac is not None,
                        "nd_learned": version == 6 and gateway_mac is not None,
                        "neighbor_state": neighbor_state,
                    }
                )
                self.interfaces[item.port] = data
                results.append(data)
            return results
        finally:
            client.set_service_mode(ports=ports, enabled=False)
            client.release(ports=ports)

    def start_stream(self, request: StartTrafficStreamRequest, template_path: Path) -> dict[str, Any]:
        api = _load_trex_api()
        template = read_template_yaml(template_path)
        client = self._get_client()
        ports = [int(port) for port in request.ports]
        tx_port = int(request.txport)
        rx_port = int(request.rxport)
        client.acquire(ports=ports, force=True)
        client.stop(ports=[tx_port])
        client.remove_all_streams(ports=[tx_port])
        port_info = client.get_port_info(ports=[tx_port, rx_port])
        tx_info = dict(port_info[0])
        tx_info.update(self.interfaces.get(request.txport, {}))
        rx_info = dict(port_info[1])
        rx_info.update(self.interfaces.get(request.rxport, {}))
        packet = _build_packet(api, template, tx_info, rx_info)
        mode = _build_mode(api, template)
        stream = api.STLStream(
            name=request.name,
            packet=api.STLPktBuilder(pkt=packet),
            mode=mode,
        )
        client.add_streams(stream, ports=[tx_port])
        client.clear_stats(ports=ports)
        client.get_stats(ports=ports, sync_now=True)
        client.start(ports=[tx_port], force=True)
        if template.get("traffic", {}).get("mode") == "count":
            client.wait_on_traffic(ports=[tx_port], timeout=60)
        return {
            "name": request.name,
            "template": request.template,
            "txport": request.txport,
            "rxport": request.rxport,
            "state": "running",
        }

    def get_port_stats(self, ports: list[str]) -> dict[str, Any]:
        client = self._get_client()
        return client.get_stats(ports=[int(port) for port in ports])

    def stop_stream(self, request: StopTrafficStreamRequest) -> dict[str, Any]:
        client = self._get_client()
        ports = [int(port) for port in request.ports]
        try:
            client.acquire(ports=ports, force=True)
            client.stop(ports=[int(request.txport)])
            client.remove_all_streams(ports=[int(request.txport)])
            return {"name": request.name, "stopped": True, "cleaned": True}
        finally:
            client.release(ports=ports)


def _fake_gateway_mac(port: str) -> str:
    suffix = int(port) if port.isdigit() else sum(ord(ch) for ch in port) % 255
    return f"02:00:00:00:00:{suffix:02x}"


def _load_trex_api() -> Any:
    try:
        import trex_stl_lib.api as api  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError("TRex Python API is not available in this environment") from exc
    return api


def _load_ipv6_nd_service() -> Any:
    try:
        from trex.common.services.trex_service_IPv6ND import ServiceIPv6ND
    except ModuleNotFoundError as exc:
        raise RuntimeError("TRex IPv6 ND service is not available in this environment") from exc
    return ServiceIPv6ND


def _build_packet(
    api: Any,
    template: dict[str, Any],
    tx_info: dict[str, Any],
    rx_info: dict[str, Any],
) -> Any:
    packet = template.get("packet", {})
    ether = api.Ether(
        src=packet.get("src_mac") or tx_info.get("src_mac"),
        dst=packet.get("dst_mac") or tx_info.get("gateway_mac") or tx_info.get("arp"),
    )
    l2 = ether
    vlan = _parse_vlan(packet.get("vlan"))
    if vlan is not None:
        l2 = l2 / api.Dot1Q(vlan=vlan)
    ip = _build_ip_layer(
        api,
        packet.get("src_ip") or tx_info.get("src_ipv4"),
        packet.get("dst_ip") or rx_info.get("src_ipv4"),
        packet.get("ip_version", "ipv4"),
    )
    if packet.get("l4_protocol") == "udp":
        l4 = api.UDP(sport=packet.get("l4_sport", 1025), dport=packet.get("l4_dport", 12))
    else:
        l4 = api.TCP(sport=packet.get("l4_sport", 1025), dport=packet.get("l4_dport", 80))
    frame_size = packet.get("frame_size") or 128
    headers = l2 / ip / l4
    payload_size = max(frame_size - 4 - len(headers), 0)
    return headers / ("x" * payload_size)


def _build_mode(api: Any, template: dict[str, Any]) -> Any:
    traffic = template.get("traffic", {})
    rate = traffic.get("rate", "100pps")
    if traffic.get("mode") == "count":
        return api.STLTXSingleBurst(total_pkts=int(traffic.get("count", 1)), **_rate_kwargs(rate))
    return api.STLTXCont(**_rate_kwargs(rate))


def _rate_kwargs(rate: str) -> dict[str, int]:
    lowered = rate.lower()
    if lowered.endswith("pps"):
        return {"pps": int(lowered[:-3])}
    multipliers = {"kbps": 1_000, "mbps": 1_000_000, "gbps": 1_000_000_000}
    for suffix, multiplier in multipliers.items():
        if lowered.endswith(suffix):
            return {"bps_L1": int(lowered[: -len(suffix)]) * multiplier}
    raise ValueError(f"unsupported TRex rate: {rate}")


def _build_ip_layer(api: Any, src_ip: str, dst_ip: str, ip_version: str = "ipv4") -> Any:
    src_version = ip_address(src_ip).version
    dst_version = ip_address(dst_ip).version
    if src_version != dst_version:
        raise ValueError("source and destination IP versions must match")
    expected_version = 6 if ip_version == "ipv6" else 4
    if src_version != expected_version:
        raise ValueError("IP addresses do not match ip_version")
    if expected_version == 6:
        return api.IPv6(src=src_ip, dst=dst_ip)
    return api.IP(src=src_ip, dst=dst_ip)


def _parse_vlan(vlan: str | None) -> int | None:
    if vlan is None or vlan == "":
        return None
    return int(vlan.split(",", 1)[0])
