"""Shared types used by every resource scanner."""

from dataclasses import dataclass


@dataclass
class Finding:
    """A single audit finding -- one flagged resource."""

    resource_id: str
    resource_type: str
    region: str
    issue: str
    recommendation: str


class ScannerError(Exception):
    """Raised when a scanner can't complete its scan."""