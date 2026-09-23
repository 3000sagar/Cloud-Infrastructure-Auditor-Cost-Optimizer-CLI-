"""Unassociated Elastic IP scanner."""

from __future__ import annotations

from typing import List, Optional

from botocore.exceptions import BotoCoreError, ClientError

from cloud_auditor.auth.aws import get_client
from cloud_auditor.scanners.base import Finding, ScannerError


def scan_unassociated_addresses(
    session, region: str, endpoint_url: Optional[str] = None
) -> List[Finding]:
    """Return a Finding for every Elastic IP with no association.

    Unlike EBS volumes, AWS doesn't expose a server-side filter for
    "unassociated" -- there's no equivalent to the volume "status"
    field. So every address is fetched and checked client-side for a
    missing AssociationId.
    """
    try:
        ec2 = get_client(session, "ec2", region=region, endpoint_url=endpoint_url)
        response = ec2.describe_addresses()
    except (BotoCoreError, ClientError) as exc:
        raise ScannerError(f"Could not scan Elastic IPs in {region}: {exc}") from exc

    findings = []
    for address in response["Addresses"]:
        if "AssociationId" in address:
            continue
        resource_id = address.get("AllocationId", address.get("PublicIp"))
        findings.append(
            Finding(
                resource_id=resource_id,
                resource_type="Elastic IP",
                region=region,
                issue="Unassociated",
                recommendation="Release the address if it's genuinely unused",
            )
        )
    return findings