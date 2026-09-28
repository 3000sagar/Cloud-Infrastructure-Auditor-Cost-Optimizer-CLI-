"""JSON report exporter."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from cloud_auditor.scanners.base import Finding

REPORT_FILENAME = "audit-report.json"


def build_report(findings: List[Finding], regions: List[str]) -> dict:
    """Turn a list of findings into a JSON-serializable report dict."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "regions": list(regions),
        "summary": {
            "total_findings": len(findings),
            "by_type": dict(Counter(f.resource_type for f in findings)),
        },
        "findings": [asdict(f) for f in findings],
    }


def write_json_report(
    findings: List[Finding], regions: List[str], output_dir: Path
) -> Path:
    """Write the report to <output_dir>/audit-report.json and return the path.

    The directory is created if it doesn't exist yet.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / REPORT_FILENAME
    path.write_text(
        json.dumps(build_report(findings, regions), indent=2), encoding="utf-8"
    )
    return path