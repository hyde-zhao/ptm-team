from __future__ import annotations

import json
import os
from typing import Any

import httpx
import typer

app = typer.Typer(
    help="TRex atomic operation CLI. Command names match ptm-atomic op_id values.",
    no_args_is_help=True,
)

DEFAULT_API_URL = "http://<IP_ADDRESS>:8000"


def _api_url() -> str:
    return os.environ.get("TREX_API_URL", DEFAULT_API_URL).rstrip("/")


def _print_result(result: dict[str, Any], output_format: str) -> None:
    if output_format != "json":
        raise typer.BadParameter("only json format is supported in the first version")
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


def _post_op(op_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{_api_url()}/api/v1/ops/{op_id}"
    with httpx.Client(timeout=30.0, trust_env=False) as client:
        response = client.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def _parse_ports(value: str) -> list[str]:
    ports = [item.strip() for item in value.split(",") if item.strip()]
    if not ports:
        raise typer.BadParameter("ports must contain at least one port")
    return ports


@app.command("tg_config_interface")
def tg_config_interface(
    interfaces: str = typer.Option(
        ...,
        "--interfaces",
        help="JSON array of interface objects: port, ip, gateway, and optional VLAN/MAC fields.",
    ),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    payload = {"interfaces": json.loads(interfaces)}
    _print_result(_post_op("tg_config_interface", payload), output_format)


@app.command("tg_apply_traffic_template")
def tg_apply_traffic_template(
    template: str = typer.Option(..., "--template"),
    tx_port: str = typer.Option(..., "--tx-port"),
    rx_port: str = typer.Option(..., "--rx-port"),
    ip_version: str = typer.Option("ipv4", "--ip-version"),
    l4_protocol: str = typer.Option(..., "--l4-protocol"),
    l4_sport: int = typer.Option(..., "--l4-sport"),
    l4_dport: int = typer.Option(..., "--l4-dport"),
    traffic_mode: str = typer.Option(..., "--traffic-mode"),
    rate: str = typer.Option(..., "--rate"),
    count: int | None = typer.Option(None, "--count"),
    frame_size: int | None = typer.Option(None, "--frame-size"),
    vlan: str | None = typer.Option(None, "--vlan"),
    src_ip: str | None = typer.Option(None, "--src-ip"),
    dst_ip: str | None = typer.Option(None, "--dst-ip"),
    src_mac: str | None = typer.Option(None, "--src-mac"),
    dst_mac: str | None = typer.Option(None, "--dst-mac"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    payload: dict[str, Any] = {
        "template": template,
        "tx_port": tx_port,
        "rx_port": rx_port,
        "ip_version": ip_version,
        "l4_protocol": l4_protocol,
        "l4_sport": l4_sport,
        "l4_dport": l4_dport,
        "traffic_mode": traffic_mode,
        "rate": rate,
    }
    if count is not None:
        payload["count"] = count
    if frame_size is not None:
        payload["frame_size"] = frame_size
    if vlan is not None:
        payload["vlan"] = vlan
    if src_ip is not None:
        payload["src_ip"] = src_ip
    if dst_ip is not None:
        payload["dst_ip"] = dst_ip
    if src_mac is not None:
        payload["src_mac"] = src_mac
    if dst_mac is not None:
        payload["dst_mac"] = dst_mac
    _print_result(_post_op("tg_apply_traffic_template", payload), output_format)


@app.command("tg_start_traffic_stream")
def tg_start_traffic_stream(
    ports: str = typer.Option(..., "--ports"),
    txport: str = typer.Option(..., "--txport"),
    rxport: str = typer.Option(..., "--rxport"),
    template: str = typer.Option(..., "--template"),
    name: str = typer.Option(..., "--name"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    payload = {
        "ports": _parse_ports(ports),
        "txport": txport,
        "rxport": rxport,
        "template": template,
        "name": name,
    }
    _print_result(_post_op("tg_start_traffic_stream", payload), output_format)


@app.command("tg_verify_traffic_loss")
def tg_verify_traffic_loss(
    ports: str = typer.Option(..., "--ports"),
    txport: str = typer.Option(..., "--txport"),
    rxport: str = typer.Option(..., "--rxport"),
    name: str = typer.Option(..., "--name"),
    max_loss: float = typer.Option(..., "--max-loss"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    payload = {
        "ports": _parse_ports(ports),
        "txport": txport,
        "rxport": rxport,
        "name": name,
        "max_loss": max_loss,
    }
    _print_result(_post_op("tg_verify_traffic_loss", payload), output_format)


@app.command("tg_stop_traffic_stream")
def tg_stop_traffic_stream(
    ports: str = typer.Option(..., "--ports"),
    txport: str = typer.Option(..., "--txport"),
    rxport: str = typer.Option(..., "--rxport"),
    name: str = typer.Option(..., "--name"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    payload = {
        "ports": _parse_ports(ports),
        "txport": txport,
        "rxport": rxport,
        "name": name,
    }
    _print_result(_post_op("tg_stop_traffic_stream", payload), output_format)


@app.command("tg_delete_traffic_template")
def tg_delete_traffic_template(
    template: str = typer.Option(..., "--template"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _print_result(_post_op("tg_delete_traffic_template", {"template": template}), output_format)


def main() -> None:
    app()
