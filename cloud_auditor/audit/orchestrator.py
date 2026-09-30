"""Audit orchestration across AWS regions."""

from __future__ import annotations

from typing import List, Optional, Sequence

from cloud_auditor.scanners.aggregator import run_all_scanners
from cloud_auditor.scanners.base import Finding


def run_audit(
    session,
    regions: Sequence[str],
    endpoint_url: Optional[str] = None,
) -> List[Finding]:
    """Run every enabled scanner across the supplied AWS regions.

    Which scanners run, and their thresholds, come from config/config.yaml
    (via run_all_scanners). A scanner that fails in one region is reported
    as a finding instead of aborting the whole audit.
    """

    findings: List[Finding] = []

    for region in regions:
        findings.extend(run_all_scanners(session, region, endpoint_url))

    return findings