"""CSV report exporter."""

from __future__ import annotations

import csv
from dataclasses import asdict, fields
from pathlib import Path
from typing import List

from cloud_auditor.scanners.base import Finding

REPORT_FILENAME = "audit-report.csv"
FIELDNAMES = [f.name for f in fields(Finding)]


def write_csv_report(findings: List[Finding], output_dir: Path) -> Path:
    """Write findings to <output_dir>/audit-report.csv and return the path.

    Unlike the JSON report, CSV has no natural place for the "regions
    scanned" list or the by-type summary -- a CSV is one row per
    finding and nothing else, which is exactly what a spreadsheet
    import expects. The directory is created if it doesn't exist yet.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / REPORT_FILENAME

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for finding in findings:
            writer.writerow(asdict(finding))

    return path