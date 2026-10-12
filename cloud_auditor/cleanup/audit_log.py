"""Persisted record of what cleanup --execute actually deleted.

Dry runs never reach this module -- only execute_cleanup's real
results do, and only after the CLI's explicit confirmation step.
Appends one JSON line per CleanupResult, so a growing history of
cleanup runs accumulates in a single file rather than overwriting
the previous run's record.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from cloud_auditor.cleanup.executor import CleanupResult

AUDIT_LOG_FILENAME = "cleanup-audit.jsonl"


def write_cleanup_audit_log(
    results: List[CleanupResult], output_dir: Path = Path("logs")
) -> Path:
    """Append one JSON line per result to <output_dir>/cleanup-audit.jsonl.

    Creates the directory and file if they don't exist yet. Existing
    entries from earlier runs are never touched -- this only appends.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / AUDIT_LOG_FILENAME

    timestamp = datetime.now(timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as f:
        for result in results:
            entry = {"timestamp": timestamp, **asdict(result)}
            f.write(json.dumps(entry) + "\n")

    return path