"""Region discovery."""

from typing import List, Optional

from botocore.exceptions import BotoCoreError, ClientError

from cloud_auditor.auth.aws import get_client


class RegionDiscoveryError(Exception):
    """Raised when the region list can't be fetched."""


def get_enabled_regions(session, endpoint_url: Optional[str] = None) -> List[str]:
    """Return the sorted list of regions enabled for this account."""
    try:
        ec2 = get_client(session, "ec2", endpoint_url=endpoint_url)
        response = ec2.describe_regions()
    except (BotoCoreError, ClientError) as exc:
        raise RegionDiscoveryError(f"Could not list regions: {exc}") from exc
    return sorted(r["RegionName"] for r in response["Regions"])