"""Runs every enabled scanner and returns the combined findings."""

from __future__ import annotations

from typing import List, Optional

from cloud_auditor.scanners.base import Finding, ScannerError
from cloud_auditor.scanners.ebs import scan_unattached_volumes
from cloud_auditor.scanners.ec2 import scan_underutilized_instances
from cloud_auditor.scanners.elastic_ip import scan_unassociated_addresses
from cloud_auditor.utils.config import load_audit_config


def run_all_scanners(
    session, region: str, endpoint_url: Optional[str] = None
) -> List[Finding]:
    """Run every scanner enabled in config/config.yaml and return all
    findings combined, in a fixed order (EBS, Elastic IP, EC2).

    A scanner that fails (e.g. missing IAM permission for that
    resource type) doesn't take the whole audit down -- its error is
    recorded as a Finding of its own so it's visible in the report,
    and the remaining scanners still run.
    """
    audit_config = load_audit_config()
    findings: List[Finding] = []
    scanners = []

    if audit_config.get("ebs", {}).get("enabled", True):
        scanners.append(
            ("EBS", lambda: scan_unattached_volumes(session, region, endpoint_url))
        )

    if audit_config.get("elastic_ip", {}).get("enabled", True):
        scanners.append(
            ("Elastic IP", lambda: scan_unassociated_addresses(session, region, endpoint_url))
        )

    ec2_config = audit_config.get("ec2", {})
    if ec2_config.get("enabled", True):
        scanners.append(
            (
                "EC2",
                lambda: scan_underutilized_instances(
                    session,
                    region,
                    endpoint_url,
                    cpu_threshold=ec2_config.get("cpu_threshold", 5),
                    period_days=ec2_config.get("period_days", 14),
                ),
            )
        )

    for name, run in scanners:
        try:
            findings.extend(run())
        except ScannerError as exc:
            findings.append(
                Finding(
                    resource_id="-",
                    resource_type=f"{name} Scanner",
                    region=region,
                    issue=f"Scan failed: {exc}",
                    recommendation="Check IAM permissions for this resource type",
                )
            )

    return findings