from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from traffic_skill.instrument.types import IxiaCConfig, IxCPort
from traffic_skill.models import Link, LinkNode


class TopologyError(ValueError):
    pass


@dataclass(frozen=True)
class Topology:
    links: dict[str, Link]
    ports: dict[str, IxCPort]
    ixia_configs: dict[str, IxiaCConfig]

    def require_link(self, name: str) -> Link:
        try:
            return self.links[name]
        except KeyError as exc:
            available = ", ".join(sorted(self.links)) or "<none>"
            raise TopologyError(f"link {name!r} not found; available links: {available}") from exc

    def ports_for_links(self, tx_link: Link, rx_link: Link) -> dict[str, IxCPort]:
        tg_keys = {tx_link.TG.node_key, rx_link.TG.node_key}
        if len(tg_keys) != 1:
            raise TopologyError(
                "tx and rx links must belong to the same TG node; "
                f"got {tx_link.TG.node_key!r} and {rx_link.TG.node_key!r}"
            )
        tg_key = next(iter(tg_keys))
        selected_names = {tx_link.TG.port_name, rx_link.TG.port_name}
        return {
            name: port
            for name, port in self.ports.items()
            if port.tg_node_key == tg_key and port.name in selected_names
        }

    def ixia_config_for_links(self, tx_link: Link, rx_link: Link) -> IxiaCConfig:
        tg_keys = {tx_link.TG.node_key, rx_link.TG.node_key}
        if len(tg_keys) != 1:
            raise TopologyError(
                "tx and rx links must belong to the same TG node; "
                f"got {tx_link.TG.node_key!r} and {rx_link.TG.node_key!r}"
            )
        tg_key = next(iter(tg_keys))
        if tg_key is None or tg_key not in self.ixia_configs:
            raise TopologyError(f"no Ixia-C config found for TG node {tg_key!r}")
        return self.ixia_configs[tg_key]


def load_topology(yaml_path: str | Path) -> Topology:
    path = Path(yaml_path)
    if not path.exists():
        raise TopologyError(f"topology file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    nodes = data.get("nodes")
    if not isinstance(nodes, dict):
        raise TopologyError("topology must contain a 'nodes' mapping")

    grouped: dict[str, list[LinkNode]] = {}
    ports: dict[str, IxCPort] = {}
    ixia_configs: dict[str, IxiaCConfig] = {}

    for node_key, node in nodes.items():
        node_type = node.get("type")
        node_name = str(node.get("name") or node_key)
        if node_type == LinkNode.NODE_TYPE_TG:
            ixia_configs[node_key] = IxiaCConfig(
                node_key=node_key,
                node_name=node_name,
                chassis_ip=str(_required(node, "host", f"TG {node_key} host")),
                api_server=str(_required(node, "api_server", f"TG {node_key} api_server")),
                ssh_host=str(node.get("ssh_host") or node.get("host")),
                ssh_port=int(node.get("port", 22)),
                ssh_username=str(_required(node, "username", f"TG {node_key} username")),
                ssh_password=str(_required(node, "password", f"TG {node_key} password")),
            )
            for iface_key, iface in _interfaces(node).items():
                link_name = str(_required(iface, "link", f"TG {node_key} interface {iface_key} link"))
                port_name = str(iface.get("name") or iface_key)
                port_key = f"{node_key}.{port_name}"
                ports[port_key] = IxCPort(
                    socket_port=int(_required(iface, "socket_port", f"TG {node_key} interface {iface_key} socket_port")),
                    name=port_name,
                    interface=str(iface.get("port_id") or port_name),
                    type=str(_required(iface, "type", f"TG {node_key} interface {iface_key} type")),
                    tg_node_key=node_key,
                    ip=str(_required(iface, "default_ip", f"TG {node_key} interface {iface_key} default_ip")),
                    ipv6=str(iface.get("default_ipv6") or ""),
                )
                grouped.setdefault(link_name, []).append(
                    LinkNode(
                        node_name=node_name,
                        node_type=LinkNode.NODE_TYPE_TG,
                        ip=str(_required(iface, "default_ip", f"TG {node_key} interface {iface_key} default_ip")),
                        ipv6=str(iface.get("default_ipv6") or ""),
                        mac=str(_required(iface, "mac_address", f"TG {node_key} interface {iface_key} mac_address")),
                        port_id=str(iface.get("port_id") or port_name),
                        port_name=port_name,
                        port_type=str(iface.get("type") or ""),
                        node_key=node_key,
                    )
                )
        elif node_type == LinkNode.NODE_TYPE_DUT:
            for iface_key, iface in _interfaces(node).items():
                link_name = str(_required(iface, "link", f"DUT {node_key} interface {iface_key} link"))
                grouped.setdefault(link_name, []).append(
                    LinkNode(
                        node_name=node_name,
                        node_type=LinkNode.NODE_TYPE_DUT,
                        ip=str(_required(iface, "default_ip", f"DUT {node_key} interface {iface_key} default_ip")),
                        ipv6=str(iface.get("default_ipv6") or ""),
                        mac=str(_required(iface, "mac_address", f"DUT {node_key} interface {iface_key} mac_address")),
                        port_id=str(iface.get("port_id") or iface.get("name") or iface_key),
                        port_name=str(iface.get("name") or iface_key),
                        port_type=str(iface.get("type") or ""),
                        node_key=node_key,
                    )
                )

    if not ixia_configs:
        raise TopologyError("topology must contain at least one TG node")

    links = {}
    for link_name, link_nodes in grouped.items():
        tg_nodes = [node for node in link_nodes if node.node_type == LinkNode.NODE_TYPE_TG]
        dut_nodes = [node for node in link_nodes if node.node_type == LinkNode.NODE_TYPE_DUT]
        if len(tg_nodes) != 1 or len(dut_nodes) != 1:
            raise TopologyError(
                f"link {link_name!r} must contain exactly one TG node and one DUT node; "
                f"found {len(tg_nodes)} TG and {len(dut_nodes)} DUT"
            )
        links[link_name] = Link(link_name, link_nodes)

    return Topology(links=links, ports=ports, ixia_configs=ixia_configs)


def _interfaces(node: dict[str, Any]) -> dict[str, Any]:
    interfaces = node.get("interfaces")
    if not isinstance(interfaces, dict):
        raise TopologyError(f"node {node.get('name', '<unknown>')} must contain an interfaces mapping")
    return interfaces


def _required(mapping: dict[str, Any], key: str, label: str):
    value = mapping.get(key)
    if value is None or value == "":
        raise TopologyError(f"missing required topology field: {label}")
    return value
