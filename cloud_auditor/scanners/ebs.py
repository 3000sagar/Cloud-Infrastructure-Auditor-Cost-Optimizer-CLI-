"""Unattached EBS volume scanner."""

from __future__ import annotations

from typing import List, Optional

from botocore.exceptions import BotoCoreError, ClientError

from cloud_auditor.auth.aws import get_client
from cloud_auditor.scanners.base import Finding, ScannerError


def scan_unattached_volumes(
    session, region: str, endpoint_url: Optional[str] = None
) -> List[Finding]:
    """Return a Finding for every EBS volume with no attachments.

    AWS reports an unattached volume's status as "available" (as
    opposed to "in-use"), so that's the filter -- no need to fetch
    every volume and check its Attachments list client-side.
    """
    try:
        ec2 = get_client(session, "ec2", region=region, endpoint_url=endpoint_url)
        response = ec2.describe_volumes(
            Filters=[{"Name": "status", "Values": ["available"]}]
        )
    except (BotoCoreError, ClientError) as exc:
        raise ScannerError(f"Could not scan EBS volumes in {region}: {exc}") from exc

    return [
        Finding(
            resource_id=volume["VolumeId"],
            resource_type="EBS Volume",
            region=region,
            issue="Unattached",
            recommendation="Delete, or snapshot then delete, if genuinely unused",
        )
        for volume in response["Volumes"]
    ]