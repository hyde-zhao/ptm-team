from __future__ import annotations

from typing import Any


def extract_port_packets(stats: dict[str, Any], txport: str, rxport: str) -> tuple[int, int]:
    tx_stats = stats.get(txport) or stats.get(int(txport)) or {}
    rx_stats = stats.get(rxport) or stats.get(int(rxport)) or {}
    tx_packets = int(tx_stats.get("opackets", tx_stats.get("tx_pkts", 0)))
    rx_packets = int(rx_stats.get("ipackets", rx_stats.get("rx_pkts", 0)))
    return tx_packets, rx_packets


def compute_loss(tx_packets: int, rx_packets: int) -> tuple[int, float]:
    if tx_packets <= 0:
        return 0, 0.0
    loss = max(tx_packets - rx_packets, 0)
    return loss, loss / tx_packets
