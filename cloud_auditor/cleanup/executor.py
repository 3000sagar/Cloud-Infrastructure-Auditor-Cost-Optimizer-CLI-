"""Dry-run and execute cleanup of flagged, cleanable resources.

Only EBS volumes and Elastic IPs are ever deleted here. EC2 instances
are never touched by this module -- stopping or resizing a running
instance carries more operational risk than deleting an orphaned
volume or releasing an idle IP (see recommendations.py's RISK_LEVELS
comment), and the project's roadmap never scoped automated EC2
cleanup.

plan_cleanup() never deletes anything -- it's the dry-run view.
execute_cleanup() deletes unconditionally and must only be called
after the caller has already gotten explicit user confirmation; it
re-filters to CLEANABLE_TYPES internally regardless of what's passed
in, so even a caller mistake can't make it touch an EC2 finding.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from botocore.exceptions import ClientError

from cloud_auditor.auth.aws import get_client
from cloud_auditor.scanners.base import Finding

# The only resource types this module will ever delete.
CLEANABLE_TYPES = ("EBS Volume", "Elastic IP")


@dataclass
class CleanupResult:
    """The outcome of attempting to clean up a single finding."""

    resource_id: str
    resource_type: str
    region: str
    status: str  # "deleted" or "error"
    error: Optional[str] = None


def plan_cleanup(findings: List[Finding]) -> List[Finding]:
    """Return the subset of findings eligible for automated cleanup.

    This never deletes anything -- it's the dry-run view, and it's
    also what execute_cleanup uses internally to decide what it's
    allowed to touch.
    """
    return [f for f in findings if f.resource_type in CLEANABLE_TYPES]


def _delete_one(session, finding: Finding, endpoint_url: Optional[str]) -> CleanupResult:
    ec2 = get_client(session, "ec2", region=finding.region, endpoint_url=endpoint_url)
    try:
        if finding.resource_type == "EBS Volume":
            ec2.delete_volume(VolumeId=finding.resource_id)
        else:  # "Elastic IP" -- the only other CLEANABLE_TYPES member
            ec2.release_address(AllocationId=finding.resource_id)
    except ClientError as exc:
        return CleanupResult(
            finding.resource_id, finding.resource_type, finding.region, "error", str(exc)
        )
    return CleanupResult(finding.resource_id, finding.resource_type, finding.region, "deleted")


def execute_cleanup(
    session, findings: List[Finding], endpoint_url: Optional[str] = None
) -> List[CleanupResult]:
    """Delete every cleanable finding in `findings`, unconditionally.

    The caller is responsible for obtaining explicit user confirmation
    before calling this -- it performs no confirmation itself. Findings
    that aren't EBS Volume or Elastic IP (e.g. EC2 Instance, or a
    scanner-failure finding) are silently excluded here regardless of
    what the caller passes in; they produce no CleanupResult and no
    AWS call is ever made for them.
    """
    return [_delete_one(session, finding, endpoint_url) for finding in plan_cleanup(findings)]