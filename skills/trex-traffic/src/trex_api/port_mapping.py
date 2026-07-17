from __future__ import annotations

import os
from functools import lru_cache

# Default logical-name -> physical TRex port index mapping.
#
# The logical name follows the "<slot>_<index>" convention where the slot
# groups physical NICs and the index is a 1-based running number across all
# ports in the group. The validated lab mapping (2_3 -> port 2, 2_5 -> port 4)
# anchors the rule:
#
#   2_1 -> 0  (05:00.0, board A)
#   2_2 -> 1  (05:00.1, board A)
#   2_3 -> 2  (05:00.2, board A)   [verified]
#   2_4 -> 3  (05:00.3, board A)   [inferred, confirmed]
#   2_5 -> 4  (04:00.0, board B)   [verified]
#   2_6 -> 5  (04:00.1, board B)
#   2_7 -> 6  (04:00.2, board B)
#   2_8 -> 7  (04:00.3, board B)
#
# Override at runtime with the TREX_PORT_MAP environment variable, formatted as
# a semicolon-separated list of "name=index" pairs, e.g.
#   TREX_PORT_MAP="2_1=0;2_2=1;2_3=2;2_4=3;2_5=4;2_6=5;2_7=6;2_8=7"
DEFAULT_PORT_MAP: dict[str, int] = {
    "2_1": 0,
    "2_2": 1,
    "2_3": 2,
    "2_4": 3,
    "2_5": 4,
    "2_6": 5,
    "2_7": 6,
    "2_8": 7,
}


@lru_cache(maxsize=1)
def port_map() -> dict[str, int]:
    """Return the active logical-name -> physical port index mapping.

    The default mapping can be overridden via the TREX_PORT_MAP environment
    variable. The result is cached for the process lifetime.
    """
    env_value = os.environ.get("TREX_PORT_MAP", "").strip()
    if not env_value:
        return dict(DEFAULT_PORT_MAP)

    mapping: dict[str, int] = {}
    for pair in env_value.split(";"):
        pair = pair.strip()
        if not pair or "=" not in pair:
            continue
        name, _, value = pair.partition("=")
        name = name.strip()
        value = value.strip()
        if not name or not value:
            continue
        try:
            mapping[name] = int(value)
        except ValueError:
            continue
    return mapping


def resolve_port(port: str | int) -> int:
    """Resolve a logical port name or numeric port into a TRex port index.

    Accepts either a logical name (e.g. "2_3") defined in the port map, or a
    plain numeric string / int (e.g. "0" or 0) used directly as the port
    index. This keeps the CLI backward compatible with raw numeric ports while
    allowing the friendly "<slot>_<index>" names.
    """
    if isinstance(port, int):
        return port
    key = port.strip()
    mapping = port_map()
    if key in mapping:
        return mapping[key]
    # Allow plain numeric passthrough so existing numeric usage keeps working.
    # NOTE: only accept pure-digit strings; Python's int() would otherwise
    # treat "9_9" as a numeric literal (99), swallowing unknown "<slot>_<idx>"
    # names as bogus port indices.
    if key.isdigit():
        return int(key)
    raise ValueError(
        f"unknown port '{port}': not a logical name in the port map and "
        f"not a numeric port index"
    )


def resolve_ports(ports: list[str]) -> list[int]:
    """Resolve a list of port names / numbers into TRex port indices."""
    return [resolve_port(p) for p in ports]
