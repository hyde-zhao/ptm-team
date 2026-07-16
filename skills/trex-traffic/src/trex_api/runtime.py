from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RuntimeStore:
    templates: dict[str, Path] = field(default_factory=dict)
    streams: dict[str, dict[str, Any]] = field(default_factory=dict)

    def template_in_use(self, template: str) -> bool:
        return any(stream.get("template") == template for stream in self.streams.values())
