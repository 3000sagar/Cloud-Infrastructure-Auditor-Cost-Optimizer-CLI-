"""Shared types used by every resource scanner."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Finding:
    """A single audit finding -- one flagged resource."""

    resource_id: str
    resource_type: str
    region: str
    issue: str
    recommendation: str
    # Raw, resource-specific data scanners already have on hand (e.g. an
    # EBS volume's size, an EC2 instance's type) -- used by the
    # recommendations layer to estimate cost, kept separate from the
    # human-readable fields above.
    metadata: dict = field(default_factory=dict)
    estimated_monthly_savings: Optional[float] = None
    risk_level: str = "Unknown"


class ScannerError(Exception):
    """Raised when a scanner can't complete its scan."""