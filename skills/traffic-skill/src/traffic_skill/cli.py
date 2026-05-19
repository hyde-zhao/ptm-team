from __future__ import annotations

import json
import re
import socket
from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from traffic_skill.config import TopologyError, load_topology
from traffic_skill.defaults import DEFAULT_COUNT, DEFAULT_FRAME_SIZE, DEFAULT_L3, DEFAULT_MAX_LOSS, DEFAULT_PPS
from traffic_skill.instrument import IxiaCInstrument
from traffic_skill.models import Traffic

app = typer.Typer(help="Traffic skill CLI agent.")

ERROR_INVALID_PARAM = "INVALID_PARAM"
ERROR_DEVICE_UNREACHABLE = "DEVICE_UNREACHABLE"
ERROR_TIMEOUT = "TIMEOUT"
ERROR_RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
ERROR_STATE_MISMATCH = "STATE_MISMATCH"
ERROR_INTERNAL = "INTERNAL_ERROR"

SENSITIVE_LINE_PATTERN = re.compile(
    r"(?im)^.*\b(?:authorization|header|password|passwd|pwd|secret|token)\b.*$"
)


class L3(str, Enum):
    ipv4 = "ipv4"
    ipv6 = "ipv6"
    arp = "arp"


class L4(str, Enum):
    tcp = "tcp"
    udp = "udp"
    icmp = "icmp"
    icmpv6 = "icmpv6"


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


@app.command()
def send(
    topology: Path = typer.Option(..., "--topology", help="Topology YAML path."),
    tx: str = typer.Option(..., "--tx", help="TX link name."),
    rx: str = typer.Option(..., "--rx", help="RX link name."),
    name: str = typer.Option(..., "--name", help="Flow name."),
    l3: L3 = typer.Option(L3.ipv4, "--l3", help="L3 protocol."),
    src_ip: Optional[str] = typer.Option(None, "--src-ip", help="Source IP without prefix."),
    dst_ip: Optional[str] = typer.Option(None, "--dst-ip", help="Destination IP without prefix."),
    l4: Optional[L4] = typer.Option(None, "--l4", help="L4 protocol."),
    src_port: Optional[int] = typer.Option(None, "--src-port", help="TCP/UDP source port."),
    dst_port: Optional[int] = typer.Option(None, "--dst-port", help="TCP/UDP destination port."),
    src_mac: Optional[str] = typer.Option(None, "--src-mac", help="Source MAC."),
    dst_mac: Optional[str] = typer.Option(None, "--dst-mac", help="Destination MAC."),
    vlan: Optional[str] = typer.Option(None, "--vlan", help="VLAN ID or comma-separated VLAN stack."),
    count: Optional[int] = typer.Option(DEFAULT_COUNT, "--count", help="Frame count."),
    continuous: bool = typer.Option(False, "--continuous", help="Send continuously."),
    pps: int = typer.Option(DEFAULT_PPS, "--pps", help="Packets per second."),
    frame_size: int = typer.Option(DEFAULT_FRAME_SIZE, "--frame-size", help="Frame size."),
    output_format: OutputFormat = typer.Option(OutputFormat.table, "--format", help="Output format."),
) -> None:
    """Define and start a named traffic flow."""
    if continuous and count != DEFAULT_COUNT:
        _fail_or_bad_parameter(output_format, "--count and --continuous are mutually exclusive")
    if not name:
        _fail_or_bad_parameter(output_format, "--name is required")

    try:
        topology_obj, tx_link, rx_link = _load_links(topology, tx, rx)
        traffic = _build_traffic(
            tx_link,
            rx_link,
            l3=l3.value,
            l4=l4.value if l4 else None,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            src_mac=src_mac,
            dst_mac=dst_mac,
            vlan=vlan,
            count=count,
            continuous=continuous,
            pps=pps,
            frame_size=frame_size,
        )
        instrument = _make_instrument(topology_obj, tx_link, rx_link)
        instrument.assign_ports()
        instrument.ensure_interface_addresses([tx_link.TG.port_name, rx_link.TG.port_name])
        instrument.warmup_neighbor(rx_link.TG.port_name, rx_link.DUT.ip.split("/")[0])
        instrument.add_traffic(traffic, name)
        instrument.start_traffic(name)
    except (TopologyError, ValueError) as exc:
        _raise_command_error(exc, output_format)
    except Exception as exc:
        _raise_command_error(exc, output_format)

    data = {
        "flow_name": name,
        "tx_link": tx,
        "rx_link": rx,
        "l3": l3.value,
        "l4": l4.value if l4 else "",
        "count": count,
        "continuous": continuous,
        "pps": pps,
        "frame_size": frame_size,
    }
    _write_success(output_format, data, f"Started flow {name}")


@app.command()
def result(
    topology: Path = typer.Option(..., "--topology"),
    tx: str = typer.Option(..., "--tx"),
    rx: str = typer.Option(..., "--rx"),
    name: Optional[str] = typer.Option(None, "--name"),
    output_format: OutputFormat = typer.Option(OutputFormat.table, "--format"),
) -> None:
    """Show traffic flow statistics."""
    try:
        topology_obj, tx_link, rx_link = _load_links(topology, tx, rx)
        instrument = _make_instrument(topology_obj, tx_link, rx_link)
        metrics = _effective_metrics(instrument, rx_link, name)
    except (TopologyError, ValueError) as exc:
        _raise_command_error(exc, output_format)
    except Exception as exc:
        _raise_command_error(exc, output_format)

    if output_format == OutputFormat.json and name and not metrics:
        _write_failure(output_format, ERROR_RESOURCE_NOT_FOUND, f"flow {name!r} statistics not found", code=1)
    if output_format == OutputFormat.json:
        _write_success(output_format, {"flows": _metrics_to_data(metrics)})
    else:
        _print_metrics(metrics)


@app.command()
def check(
    topology: Path = typer.Option(..., "--topology"),
    tx: str = typer.Option(..., "--tx"),
    rx: str = typer.Option(..., "--rx"),
    max_loss: float = typer.Option(DEFAULT_MAX_LOSS, "--max-loss"),
    name: Optional[str] = typer.Option(None, "--name"),
    output_format: OutputFormat = typer.Option(OutputFormat.table, "--format"),
) -> None:
    """Check traffic flow statistics against a loss threshold."""
    try:
        topology_obj, tx_link, rx_link = _load_links(topology, tx, rx)
        instrument = _make_instrument(topology_obj, tx_link, rx_link)
        metrics = _effective_metrics(instrument, rx_link, name)
    except (TopologyError, ValueError) as exc:
        _raise_command_error(exc, output_format)
    except Exception as exc:
        _raise_command_error(exc, output_format)

    if output_format == OutputFormat.json and name and not metrics:
        _write_failure(output_format, ERROR_RESOURCE_NOT_FOUND, f"flow {name!r} statistics not found", code=1)

    failures = _check_metrics(metrics, max_loss)
    if failures:
        if output_format == OutputFormat.json:
            _write_failure(
                output_format,
                ERROR_STATE_MISMATCH,
                "traffic loss verification failed",
                data={
                    "passed": False,
                    "max_loss": max_loss,
                    "failures": failures,
                    "flows": _metrics_to_data(metrics),
                },
                code=1,
            )
        for failure in failures:
            typer.echo(f"FAIL {failure}")
        raise typer.Exit(code=1)

    _write_success(
        output_format,
        {
            "passed": True,
            "max_loss": max_loss,
            "failures": [],
            "flows": _metrics_to_data(metrics),
        },
        "PASS",
    )


@app.command()
def stop(
    topology: Path = typer.Option(..., "--topology"),
    tx: str = typer.Option(..., "--tx"),
    rx: str = typer.Option(..., "--rx"),
    name: Optional[str] = typer.Option(None, "--name"),
    output_format: OutputFormat = typer.Option(OutputFormat.table, "--format"),
) -> None:
    """Stop traffic flows."""
    try:
        topology_obj, tx_link, rx_link = _load_links(topology, tx, rx)
        _make_instrument(topology_obj, tx_link, rx_link).stop_traffic(name)
    except (TopologyError, ValueError) as exc:
        _raise_command_error(exc, output_format)
    except Exception as exc:
        _raise_command_error(exc, output_format)

    stopped = name if name else "all"
    _write_success(output_format, {"stopped": stopped}, f"Stopped flow {name}" if name else "Stopped all flows")


@app.command()
def clear(
    topology: Path = typer.Option(..., "--topology"),
    tx: str = typer.Option(..., "--tx"),
    rx: str = typer.Option(..., "--rx"),
    name: str = typer.Option(..., "--name"),
    output_format: OutputFormat = typer.Option(OutputFormat.table, "--format"),
) -> None:
    """Remove a named traffic flow."""
    if not name:
        _fail_or_bad_parameter(output_format, "--name is required")

    try:
        topology_obj, tx_link, rx_link = _load_links(topology, tx, rx)
        _make_instrument(topology_obj, tx_link, rx_link).remove_traffic(name)
    except (TopologyError, ValueError) as exc:
        _raise_command_error(exc, output_format)
    except Exception as exc:
        _raise_command_error(exc, output_format)

    _write_success(output_format, {"deleted": name}, f"Cleared flow {name}")


def _write_success(output_format: OutputFormat, data: dict, text: str | None = None) -> None:
    if output_format == OutputFormat.json:
        typer.echo(json.dumps(_envelope("success", data), ensure_ascii=False, sort_keys=True))
        return
    if text is not None:
        typer.echo(text)


def _write_failure(
    output_format: OutputFormat,
    error_type: str,
    message: str,
    *,
    data: dict | None = None,
    code: int = 2,
) -> None:
    if output_format == OutputFormat.json:
        typer.echo(
            json.dumps(
                _envelope("failed", data or {}, error_type=error_type, message=_redact(message)),
                ensure_ascii=False,
                sort_keys=True,
            ),
            err=True,
        )
        raise typer.Exit(code=code)
    raise typer.BadParameter(message)


def _raise_command_error(exc: Exception, output_format: OutputFormat) -> None:
    if output_format == OutputFormat.json:
        error_type = _error_type_for_exception(exc)
        code = 1 if error_type in {ERROR_RESOURCE_NOT_FOUND, ERROR_STATE_MISMATCH} else 2
        _write_failure(output_format, error_type, str(exc), code=code)
    if isinstance(exc, (TopologyError, ValueError)):
        raise typer.BadParameter(str(exc)) from exc
    raise exc


def _fail_or_bad_parameter(output_format: OutputFormat, message: str) -> None:
    _write_failure(output_format, ERROR_INVALID_PARAM, message, code=2)


def _envelope(status: str, data: dict, error_type: str = "", message: str | None = None) -> dict:
    payload = {
        "status": status,
        "data": data,
        "error_type": error_type,
        "diag_snapshot_ref": "",
    }
    if message is not None:
        payload["message"] = message
    return payload


def _error_type_for_exception(exc: Exception) -> str:
    message = str(exc).lower()
    class_name = exc.__class__.__name__.lower()
    if isinstance(exc, (TimeoutError, socket.timeout)) or "timeout" in class_name or "timed out" in message:
        return ERROR_TIMEOUT
    if "flow" in message and "not found" in message:
        return ERROR_RESOURCE_NOT_FOUND
    if isinstance(exc, (TopologyError, ValueError)):
        return ERROR_INVALID_PARAM
    unreachable_markers = (
        "connection refused",
        "connection reset",
        "connection aborted",
        "could not connect",
        "failed to connect",
        "no route to host",
        "network is unreachable",
        "ssh",
        "snappi",
        "api",
    )
    if any(marker in message or marker in class_name for marker in unreachable_markers):
        return ERROR_DEVICE_UNREACHABLE
    return ERROR_INTERNAL


def _redact(message: str) -> str:
    return SENSITIVE_LINE_PATTERN.sub("[REDACTED]", message)


def _load_links(topology_path: Path, tx: str, rx: str):
    topology = load_topology(topology_path)
    return topology, topology.require_link(tx), topology.require_link(rx)


def _make_instrument(topology, tx_link, rx_link):
    return IxiaCInstrument(
        topology.ixia_config_for_links(tx_link, rx_link),
        topology.ports_for_links(tx_link, rx_link),
    )


def _build_traffic(tx_link, rx_link, **options) -> Traffic:
    kwargs = {
        "frame_size": str(options["frame_size"]),
        "pps": options["pps"],
        "trans_mode": Traffic.CONTINUOUS if options["continuous"] else Traffic.COUNT,
        "frame_count": options["count"],
    }
    if options["src_mac"]:
        kwargs["src_mac_value"] = options["src_mac"]
    if options["dst_mac"]:
        kwargs["dst_mac_value"] = options["dst_mac"]
    if options["src_ip"]:
        kwargs["src_ipv4_value" if options["l3"] == Traffic.L3_HEADER_IPV4 else "src_ipv6_value"] = options["src_ip"]
    if options["dst_ip"]:
        kwargs["dst_ipv4_value" if options["l3"] == Traffic.L3_HEADER_IPV4 else "dst_ipv6_value"] = options["dst_ip"]
    if options["src_port"] is not None:
        kwargs["tcp_src_port_value" if options["l4"] == Traffic.L4_HEADER_TCP else "udp_src_port_value"] = options["src_port"]
    if options["dst_port"] is not None:
        kwargs["tcp_dst_port_value" if options["l4"] == Traffic.L4_HEADER_TCP else "udp_dst_port_value"] = options["dst_port"]
    if options["vlan"]:
        kwargs["vlan_ids"] = _parse_vlan(options["vlan"])
    l4_header = Traffic.L4_HEADER_ICMP_V6 if options["l4"] == "icmpv6" else options["l4"]
    return Traffic(tx_link, rx_link, l3_header=options["l3"] or DEFAULT_L3, l4_header=l4_header, **kwargs)


def _parse_vlan(value: str) -> int | list[int]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        raise ValueError("vlan must not be empty")
    vlan_ids = [int(part) for part in parts]
    for vlan_id in vlan_ids:
        if vlan_id < 0 or vlan_id > 4095:
            raise ValueError("vlan must be in range 0-4095")
    return vlan_ids[0] if len(vlan_ids) == 1 else vlan_ids


def _print_metrics(metrics) -> None:
    if not metrics:
        typer.echo("No flow statistics found")
        return
    typer.echo("Name\tTx Frames\tRx Frames\tLoss %\tTx Rate\tRx Rate\tState")
    for metric in metrics:
        tx = int(getattr(metric, "frames_tx", 0) or 0)
        rx = int(getattr(metric, "frames_rx", 0) or 0)
        loss = _loss_ratio(tx, rx) * 100
        typer.echo(
            f"{getattr(metric, 'name', '')}\t{tx}\t{rx}\t{loss:.2f}\t"
            f"{getattr(metric, 'frames_tx_rate', 0)}\t{getattr(metric, 'frames_rx_rate', 0)}\t"
            f"{getattr(metric, 'transmit', '')}"
        )


def _metrics_to_data(metrics) -> list[dict]:
    flows = []
    for metric in metrics:
        tx = int(getattr(metric, "frames_tx", 0) or 0)
        rx = int(getattr(metric, "frames_rx", 0) or 0)
        flows.append(
            {
                "name": getattr(metric, "name", ""),
                "frames_tx": tx,
                "frames_rx": rx,
                "loss": _loss_ratio(tx, rx),
                "frames_tx_rate": getattr(metric, "frames_tx_rate", 0) or 0,
                "frames_rx_rate": getattr(metric, "frames_rx_rate", 0) or 0,
                "state": getattr(metric, "transmit", ""),
            }
        )
    return flows


def _effective_metrics(instrument, rx_link, name):
    metrics = instrument.get_flow_statistics(name)
    if _needs_port_rx_fallback(metrics):
        port_metrics = instrument.get_port_statistics(rx_link.TG.port_name)
        if port_metrics:
            rx_frames = int(getattr(port_metrics[0], "frames_rx", 0) or 0)
            for metric in metrics:
                if int(getattr(metric, "frames_rx", 0) or 0) == 0 and rx_frames > 0:
                    setattr(metric, "frames_rx", rx_frames)
                    if hasattr(port_metrics[0], "frames_rx_rate"):
                        setattr(metric, "frames_rx_rate", getattr(port_metrics[0], "frames_rx_rate"))
    return metrics


def _needs_port_rx_fallback(metrics) -> bool:
    if len(metrics) != 1:
        return False
    metric = metrics[0]
    return int(getattr(metric, "frames_tx", 0) or 0) > 0 and int(getattr(metric, "frames_rx", 0) or 0) == 0


def _check_metrics(metrics, max_loss: float) -> list[str]:
    if not metrics:
        return ["no flow statistics found"]
    failures = []
    for metric in metrics:
        name = getattr(metric, "name", "<unknown>")
        tx = int(getattr(metric, "frames_tx", 0) or 0)
        rx = int(getattr(metric, "frames_rx", 0) or 0)
        loss = _loss_ratio(tx, rx)
        if rx <= 0:
            failures.append(f"{name}: Rx Frames is 0")
        if loss > max_loss:
            failures.append(f"{name}: loss {loss:.4f} exceeds max_loss {max_loss:.4f}")
    return failures


def _loss_ratio(tx: int, rx: int) -> float:
    if tx <= 0:
        return 1.0 if rx <= 0 else 0.0
    return max(tx - rx, 0) / tx


if __name__ == "__main__":
    app()
