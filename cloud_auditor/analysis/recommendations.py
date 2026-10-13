"""Turns scanner findings into cost-saving recommendations.

Attaches an estimated monthly savings figure and a risk level to each
finding, based on approximate AWS on-demand pricing.

These are estimates, not quotes. Actual prices vary by region and time.
Verify estimates against AWS Cost Explorer before taking action.
"""

from __future__ import annotations

import dataclasses
import math
from typing import List, Optional

from cloud_auditor.scanners.base import Finding


# Approximate us-east-1 pricing in USD.
EBS_GP3_PER_GB_MONTH = 0.08
ELASTIC_IP_PER_MONTH = 3.60

# Approximate EC2 hourly rates in USD.
EC2_HOURLY_RATES = {
    "t2.micro": 0.0116,
    "t2.small": 0.023,
    "t2.medium": 0.0464,
    "t3.micro": 0.0104,
    "t3.small": 0.0208,
    "t3.medium": 0.0416,
    "m5.large": 0.096,
    "m5.xlarge": 0.192,
}

DEFAULT_EC2_HOURLY_RATE = 0.10
HOURS_PER_MONTH = 730

# Operational risk associated with each resource type.
RISK_LEVELS = {
    "EBS Volume": "Low",
    "Elastic IP": "Low",
    "EC2 Instance": "Medium",
}

# Points deducted from the initial optimization score of 100.
RISK_WEIGHTS = {
    "High": 5,
    "Medium": 2,
    "Low": 1,
}

DEFAULT_RISK_WEIGHT = 5


def _estimate_savings(finding: Finding) -> Optional[float]:
    """Estimate monthly savings for a finding.

    Returns None when required metadata is missing or invalid.

    For EC2 instances, known instance types use their configured rates.
    Unknown instance types use the fallback rate. Missing or invalid
    instance-type metadata returns None to avoid a misleading estimate.
    """

    if finding.resource_type == "EBS Volume":
        size_gb = finding.metadata.get("size_gb")

        if (
            isinstance(size_gb, bool)
            or not isinstance(size_gb, (int, float))
            or not math.isfinite(size_gb)
            or size_gb <= 0
        ):
            return None

        return round(size_gb * EBS_GP3_PER_GB_MONTH, 2)

    if finding.resource_type == "Elastic IP":
        return ELASTIC_IP_PER_MONTH

    if finding.resource_type == "EC2 Instance":
        instance_type = finding.metadata.get("instance_type")

        # Missing or invalid metadata should not produce a price estimate.
        if (
            not isinstance(instance_type, str)
            or not instance_type.strip()
        ):
            return None

        # Known types use their configured rates. Unknown types use a
        # fallback estimate, which should not be treated as actual pricing.
        hourly_rate = EC2_HOURLY_RATES.get(
            instance_type,
            DEFAULT_EC2_HOURLY_RATE,
        )

        return round(hourly_rate * HOURS_PER_MONTH, 2)

    return None


def enrich_with_savings_estimates(
    findings: List[Finding],
) -> List[Finding]:
    """Return new findings enriched with savings estimates and risk levels.

    Scanner-failure findings are passed through unchanged because
    scanner errors do not represent resources that can be priced.
    """

    enriched = []

    for finding in findings:
        if finding.resource_type.endswith(" Scanner"):
            enriched.append(finding)
            continue

        enriched.append(
            dataclasses.replace(
                finding,
                estimated_monthly_savings=_estimate_savings(finding),
                risk_level=RISK_LEVELS.get(
                    finding.resource_type,
                    "Unknown",
                ),
            )
        )

    return enriched


def calculate_optimization_score(findings: List[Finding]) -> int:
    """Calculate an optimization score between 0 and 100.

    Starts at 100 and subtracts points according to each finding's
    risk level. The score never falls below zero.

    Scanner-failure findings are excluded because scan errors are
    not optimization findings.
    """

    penalty = 0

    for finding in findings:
        if finding.resource_type.endswith(" Scanner"):
            continue

        penalty += RISK_WEIGHTS.get(
            finding.risk_level,
            DEFAULT_RISK_WEIGHT,
        )

    return max(0, 100 - penalty)
