from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from trex_api.schemas import ApplyTrafficTemplateRequest


def render_template_payload(request: ApplyTrafficTemplateRequest) -> dict[str, Any]:
    packet = {
        "ip_version": request.ip_version,
        "l4_protocol": request.l4_protocol,
        "l4_sport": request.l4_sport,
        "l4_dport": request.l4_dport,
        "frame_size": request.frame_size,
        "vlan": request.vlan,
        "src_ip": request.src_ip,
        "dst_ip": request.dst_ip,
        "src_mac": request.src_mac,
        "dst_mac": request.dst_mac,
    }
    traffic = {
        "mode": request.traffic_mode,
        "count": request.count,
        "rate": request.rate,
    }
    return {
        "template": request.template,
        "template_type": "stl",
        "ports": {
            "tx_port": request.tx_port,
            "rx_port": request.rx_port,
        },
        "packet": {key: value for key, value in packet.items() if value is not None},
        "traffic": {key: value for key, value in traffic.items() if value is not None},
    }


def write_template_yaml(template_dir: Path, request: ApplyTrafficTemplateRequest) -> Path:
    template_dir.mkdir(parents=True, exist_ok=True)
    path = template_dir / f"{request.template}.yaml"
    payload = render_template_payload(request)
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def read_template_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"template file is not a mapping: {path}")
    return data
