"""Criação de artifacts de execução (pasta run + summary)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunSummary:
    started_at: str
    input_file: str
    output_file: str
    rows: int
    cols: int
    num_errors: int
    num_warn: int
    notes: dict[str, Any]


def make_run_dir(base_output_dir: Path) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = base_output_dir / "runs" / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_summary(summary: RunSummary, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(summary), f, ensure_ascii=False, indent=2)