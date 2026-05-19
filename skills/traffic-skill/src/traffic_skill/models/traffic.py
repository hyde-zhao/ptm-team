from __future__ import annotations

from copy import copy
from dataclasses import dataclass

from traffic_skill.models.link import Link


@dataclass(frozen=True)
class IncrementItem:
    start: str | int
    step: str | int
    count: str | int

    def __str__(self) -> str:
        return f"start:{self.start}, step:{self.step}, count:{self.count}"


class Traffic:
    SINGLE = "single_value"
    INCREMENT = "increment"
    L3_HEADER_IPV4 = "ipv4"
    L3_HEADER_IPV6 = "ipv6"
    L3_HEADER_ARP = "arp"
    L4_HEADER_TCP = "tcp"
    L4_HEADER_UDP = "udp"
    L4_HEADER_ICMP = "icmp"
    L4_HEADER_ICMP_V6 = "icmp_v6"
    COUNT = "count"
    CONTINUOUS = "continuous"
    WAIT = "wait"

    def __init__(self, tx_link: Link, rx_link: Link, l3_header=None, l4_header=None, **kwargs):
        self.tx_link = tx_link
        self.rx_link = rx_link
        self.l3_header = l3_header
        self.l4_header = l4_header

        self.frame_size_mode = kwargs.get("frame_size_mode", "fixed")
        self.frame_size = kwargs.get("frame_size", "128")
        self.trans_mode = kwargs.get("trans_mode", self.COUNT)
        self.frame_count = kwargs.get("frame_count", 100)
        self.rate_mode = kwargs.get("rate_mode", "pps")
        self.line_rate = kwargs.get("line_rate", 10)
        self.pps = kwargs.get("pps", 10000)

        self.dst_mac_type = kwargs.get("dst_mac_type", self.SINGLE)
        self.dst_mac_value = kwargs.get("dst_mac_value", tx_link.DUT.mac)
        self.dst_mac_increment = kwargs.get(
            "dst_mac_increment",
            IncrementItem(start=tx_link.DUT.mac, step="00:00:00:00:00:01", count="100"),
        )
        self.src_mac_type = kwargs.get("src_mac_type", self.SINGLE)
        self.src_mac_value = kwargs.get("src_mac_value", tx_link.TG.mac)
        self.src_mac_increment = kwargs.get(
            "src_mac_increment",
            IncrementItem(start=tx_link.TG.mac, step="00:00:00:00:00:01", count="100"),
        )
        self.ethernet_type = kwargs.get("ethernet_type", None)
        self.crc = kwargs.get("crc", None)
        self.vlan_ids = kwargs.get("vlan_ids", None)
        self.vlan_priority = kwargs.get("vlan_priority", None)
        self.vlan_cfi = kwargs.get("vlan_cfi", None)
        self.vlan_protocol = kwargs.get("vlan_protocol", None)

        self.hardware_type = kwargs.get("hardware_type", "1")
        self.protocol_type = kwargs.get("protocol_type", "800")
        self.hardware_address_length = kwargs.get("hardware_address_length", "6")
        self.protocol_address_length = kwargs.get("protocol_address_length", "4")
        self.op_code = kwargs.get("op_code", "1")
        self.sender_hardware_address_type = kwargs.get("sender_hardware_address_type", self.SINGLE)
        self.sender_hardware_address_value = kwargs.get("sender_hardware_address_value", tx_link.TG.mac)
        self.sender_hardware_address_increment = kwargs.get(
            "sender_hardware_address_increment",
            IncrementItem(start=tx_link.TG.mac, step="00:00:00:00:00:01", count="100"),
        )
        self.sender_protocol_address_type = kwargs.get("sender_protocol_address_type", self.SINGLE)
        self.sender_protocol_address_value = kwargs.get(
            "sender_protocol_address_value", tx_link.TG.ip.split("/")[0]
        )
        self.sender_protocol_address_increment = kwargs.get(
            "sender_protocol_address_increment",
            IncrementItem(start=tx_link.TG.ip.split("/")[0], step="0.0.0.1", count="100"),
        )
        self.target_hardware_address_type = kwargs.get("target_hardware_address_type", self.SINGLE)
        self.target_hardware_address_value = kwargs.get("target_hardware_address_value", "00:00:00:00:00:00")
        self.target_hardware_address_increment = kwargs.get(
            "target_hardware_address_increment",
            IncrementItem(start="00:00:00:00:00:00", step="00:00:00:00:00:01", count="100"),
        )
        self.target_protocol_address_type = kwargs.get("target_protocol_address_type", self.SINGLE)
        self.target_protocol_address_value = kwargs.get(
            "target_protocol_address_value", rx_link.TG.ip.split("/")[0]
        )
        self.target_protocol_address_increment = kwargs.get(
            "target_protocol_address_increment",
            IncrementItem(start=rx_link.TG.ip.split("/")[0], step="0.0.0.1", count="100"),
        )

        self.header_length = kwargs.get("header_length", None)
        self.ttl = kwargs.get("ttl", "64")
        self.protocol = kwargs.get("protocol", None)
        self.header_checksum = kwargs.get("header_checksum", None)
        self.src_ipv4_type = kwargs.get("src_ipv4_type", self.SINGLE)
        self.src_ipv4_value = kwargs.get("src_ipv4_value", tx_link.TG.ip.split("/")[0])
        self.src_ipv4_increment = kwargs.get(
            "src_ipv4_increment", IncrementItem(start=tx_link.TG.ip.split("/")[0], step="0.0.0.1", count="100")
        )
        self.dst_ipv4_type = kwargs.get("dst_ipv4_type", self.SINGLE)
        self.dst_ipv4_value = kwargs.get("dst_ipv4_value", rx_link.TG.ip.split("/")[0])
        self.dst_ipv4_increment = kwargs.get(
            "dst_ipv4_increment", IncrementItem(start=rx_link.TG.ip.split("/")[0], step="0.0.0.1", count="100")
        )

        self.payload_length = kwargs.get("payload_length", None)
        self.next_header = kwargs.get("next_header", None)
        self.hop_limit = kwargs.get("hop_limit", 64)
        self.src_ipv6_type = kwargs.get("src_ipv6_type", self.SINGLE)
        self.src_ipv6_value = kwargs.get("src_ipv6_value", tx_link.TG.ipv6.split("/")[0])
        self.src_ipv6_increment = kwargs.get(
            "src_ipv6_increment", IncrementItem(start=tx_link.TG.ipv6.split("/")[0], step="::1", count="100")
        )
        self.dst_ipv6_type = kwargs.get("dst_ipv6_type", self.SINGLE)
        self.dst_ipv6_value = kwargs.get("dst_ipv6_value", rx_link.TG.ipv6.split("/")[0])
        self.dst_ipv6_increment = kwargs.get(
            "dst_ipv6_increment", IncrementItem(start=rx_link.TG.ipv6.split("/")[0], step="::1", count="100")
        )

        self.tcp_src_port_type = kwargs.get("tcp_src_port_type", self.SINGLE)
        self.tcp_src_port_value = kwargs.get("tcp_src_port_value", "60")
        self.tcp_src_port_increment = kwargs.get("tcp_src_port_increment", IncrementItem("60", "1", "100"))
        self.tcp_dst_port_type = kwargs.get("tcp_dst_port_type", self.SINGLE)
        self.tcp_dst_port_value = kwargs.get("tcp_dst_port_value", "60")
        self.tcp_dst_port_increment = kwargs.get("tcp_dst_port_increment", IncrementItem("60", "1", "100"))
        self.tcp_checksum = kwargs.get("tcp_checksum", None)
        self.tcp_control_bits_urg = kwargs.get("tcp_control_bits_urg", 0)
        self.tcp_control_bits_ack = kwargs.get("tcp_control_bits_ack", 0)
        self.tcp_control_bits_psh = kwargs.get("tcp_control_bits_psh", 0)
        self.tcp_control_bits_rst = kwargs.get("tcp_control_bits_rst", 0)
        self.tcp_control_bits_syn = kwargs.get("tcp_control_bits_syn", 0)
        self.tcp_control_bits_fin = kwargs.get("tcp_control_bits_fin", 0)
        self.tcp_acknowledgment_number = kwargs.get("tcp_acknowledgment_number", None)

        self.udp_src_port_type = kwargs.get("udp_src_port_type", self.SINGLE)
        self.udp_src_port_value = kwargs.get("udp_src_port_value", "63")
        self.udp_src_port_increment = kwargs.get("udp_src_port_increment", IncrementItem("63", "1", "100"))
        self.udp_dst_port_type = kwargs.get("udp_dst_port_type", self.SINGLE)
        self.udp_dst_port_value = kwargs.get("udp_dst_port_value", "63")
        self.udp_dst_port_increment = kwargs.get("udp_dst_port_increment", IncrementItem("63", "1", "100"))
        self.udp_length = kwargs.get("udp_length", None)
        self.udp_checksum = kwargs.get("udp_checksum", "0x0000")

        self.icmp_message_type = kwargs.get("icmp_message_type", 8)
        self.icmp_message_code_value = kwargs.get("icmp_message_code_value", 0)
        self.icmp_checksum = kwargs.get("icmp_checksum", None)
        self.icmp_identifier = kwargs.get("icmp_identifier", 0)
        self.icmp_sequence_number_type = kwargs.get("icmp_sequence_number_type", self.SINGLE)
        self.icmp_sequence_number_value = kwargs.get("icmp_sequence_number_value", 0)
        self.icmp_sequence_number_increment = kwargs.get("icmp_sequence_number_increment", IncrementItem("0", "1", "100"))
        self.icmp_next_fields = kwargs.get("icmp_next_fields", None)

        self.icmp_v6_message_type = kwargs.get("icmp_v6_message_type", 128)
        self.icmp_v6_code = kwargs.get("icmp_v6_code", None)
        self.icmp_v6_checksum = kwargs.get("icmp_v6_checksum", None)
        self.icmp_v6_identifier = kwargs.get("icmp_v6_identifier", None)
        self.icmp_v6_sequence_number_type = kwargs.get("icmp_v6_sequence_number_type", self.SINGLE)
        self.icmp_v6_sequence_number_value = kwargs.get("icmp_v6_sequence_number_value", "1")
        self.icmp_v6_sequence_number_increment = kwargs.get(
            "icmp_v6_sequence_number_increment", IncrementItem("0", "1", "100")
        )
        self.icmp_v6_source_link_layer_address_opt_type = kwargs.get(
            "icmp_v6_source_link_layer_address_opt_type", 1
        )
        self.icmp_v6_source_link_layer_address_opt_length = kwargs.get(
            "icmp_v6_source_link_layer_address_opt_length", 1
        )
        self.icmp_v6_source_link_layer_address_opt_link_layer_address = kwargs.get(
            "icmp_v6_source_link_layer_address_opt_link_layer_address", None
        )

        self.mpls_label = kwargs.get("mpls_label", None)
        self.mpls_exp = kwargs.get("mpls_exp", 0)
        self.mpls_bottom_of_stack = kwargs.get("mpls_bottom_of_stack", 1)
        self.mpls_ttl = kwargs.get("mpls_ttl", 64)
        self.tracking = kwargs.get("tracking", None)

    def __repr__(self) -> str:
        middle = ", ".join(f"{key}={value!r}" for key, value in self.__dict__.items() if not key.startswith("_"))
        return f"Traffic({middle})"

    def __str__(self) -> str:
        return "\n".join(f"{key} = {value}" for key, value in self.__dict__.items())

    def reversed(self, **kwargs):
        traffic = copy(self)
        traffic.tx_link, traffic.rx_link = self.rx_link, self.tx_link
        traffic.src_mac_value = traffic.tx_link.TG.mac
        traffic.dst_mac_value = traffic.tx_link.DUT.mac
        traffic.src_ipv4_value = traffic.tx_link.TG.ip.split("/")[0]
        traffic.dst_ipv4_value = traffic.rx_link.TG.ip.split("/")[0]
        traffic.src_ipv6_value = traffic.tx_link.TG.ipv6.split("/")[0]
        traffic.dst_ipv6_value = traffic.rx_link.TG.ipv6.split("/")[0]
        for key, value in kwargs.items():
            if not hasattr(traffic, key):
                raise AttributeError(f"Traffic has no attribute {key}")
            setattr(traffic, key, value)
        return traffic
