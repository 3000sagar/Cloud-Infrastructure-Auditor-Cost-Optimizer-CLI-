"""Audit orchestration across AWS regions."""

from __future__ import annotations

from typing import List, Optional, Sequence

from cloud_auditor.scanners.base import Finding
from cloud_auditor.scanners.ebs import scan_unattached_volumes
from cloud_auditor.scanners.ec2 import scan_underutilized_instances
from cloud_auditor.scanners.elastic_ip import scan_unassociated_addresses


def run_audit(
    session,
    regions: Sequence[str],
    endpoint_url: Optional[str] = None,
) -> List[Finding]:
    """Run all resource scanners across the supplied AWS regions."""

    findings: List[Finding] = []

    for region in regions:
        findings.extend(
            scan_unattached_volumes(
                session,
                region,
                endpoint_url=endpoint_url,
            )
        )

        findings.extend(
            scan_unassociated_addresses(
                session,
                region,
                endpoint_url=endpoint_url,
            )
        )

        findings.extend(
            scan_underutilized_instances(
                session,
                region,
                endpoint_url=endpoint_url,
            )
        )

    return findings