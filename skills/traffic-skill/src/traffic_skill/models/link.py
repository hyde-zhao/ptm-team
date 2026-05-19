from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LinkNode:
    NODE_TYPE_TG = "TG"
    NODE_TYPE_DUT = "DUT"
    PORT_TYPE_GE_COPPER = "GE_Copper"
    PORT_TYPE_GE_FIBER = "GE_Fiber"
    PORT_TYPE_XGE = "XGE"
    PORT_TYPE_XGE_FIBER = "XGE_Fiber"

    node_name: str
    node_type: str
    ip: str
    ipv6: str
    mac: str
    port_id: str
    port_name: str
    port_type: str
    node_key: str | None = None


class Link:
    def __init__(self, name: str, nodes: list[LinkNode]):
        self.name = name
        self.nodes = nodes
        try:
            self.TG = next(node for node in nodes if node.node_type == LinkNode.NODE_TYPE_TG)
            self.DUT = next(node for node in nodes if node.node_type == LinkNode.NODE_TYPE_DUT)
        except StopIteration as exc:
            raise ValueError(f"link {name!r} must contain one TG node and one DUT node") from exc

    def __repr__(self) -> str:
        return f"Link(name={self.name!r}, nodes={self.nodes!r})"
