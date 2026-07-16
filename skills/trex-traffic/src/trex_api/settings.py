from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_TEMPLATE_DIR = Path("/opt/trex/v3.08/trex_template")


@dataclass(frozen=True)
class Settings:
    template_dir: Path
    backend: str = "simulated"
    verify_sample_seconds: float = 3.0


def load_settings() -> Settings:
    return Settings(
        template_dir=Path(os.environ.get("TREX_TEMPLATE_DIR", DEFAULT_TEMPLATE_DIR)),
        backend=os.environ.get("TREX_BACKEND", "simulated"),
        verify_sample_seconds=float(os.environ.get("TREX_VERIFY_SAMPLE_SECONDS", "3")),
    )
