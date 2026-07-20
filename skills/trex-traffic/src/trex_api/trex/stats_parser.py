from __future__ import annotations

from typing import Any

from trex_api.port_mapping import resolve_port


def _port_stats(stats: dict[str, Any], port: str) -> dict[str, Any]:
    """Look up a port's stats entry by resolving the logical name first.

    TRex ``get_stats`` keys port entries by the integer physical port index,
    so a logical name like ``"2_3"`` must be resolved (``resolve_port`` ->
    ``2``) before lookup. Resolving here instead of relying on ``int(port)``
    avoids the Python pitfall where ``int("2_3")`` returns ``23`` (underscore
    is accepted as a numeric separator), which would silently read a
    nonexistent port as zero packets.

    Both the resolved index and the original string are tried so simulated
    backends that key stats by the port name still work.
    """
    try:
        resolved = resolve_port(port)
    except ValueError:
        resolved = port
    return stats.get(resolved) or stats.get(port) or {}


def extract_port_packets(stats: dict[str, Any], txport: str, rxport: str) -> tuple[int, int]:
    tx_stats = _port_stats(stats, txport)
    rx_stats = _port_stats(stats, rxport)
    tx_packets = int(tx_stats.get("opackets", tx_stats.get("tx_pkts", 0)))
    rx_packets = int(rx_stats.get("ipackets", rx_stats.get("rx_pkts", 0)))
    return tx_packets, rx_packets


def compute_loss(tx_packets: int, rx_packets: int) -> tuple[int, float]:
    if tx_packets <= 0:
        return 0, 0.0
    loss = max(tx_packets - rx_packets, 0)
    return loss, loss / tx_packets
