"""Turns scanner findings into cost-saving recommendations.

Attaches an estimated monthly savings figure and a risk level to each
finding, based on rough, approximate AWS on-demand pricing. These are
estimates, not quotes -- see the README's note on verifying against
AWS Cost Explorer before acting on any of them. moto doesn't mock
AWS's Pricing API, and real prices vary by region and change over
time, so a static reference table is the practical choice here.
"""

from __future__ import annotations

import dataclasses
from typing import List, Optional

from cloud_auditor.scanners.base import Finding

# Approximate us-east-1 on-demand pricing in USD, as of this writing.
EBS_GP3_PER_GB_MONTH = 0.08
ELASTIC_IP_PER_MONTH = 3.60  # AWS's flat ~$0.005/hr charge for an unassociated EIP

# A reference table, not an exhaustive price list. An instance type not
# listed here falls back to DEFAULT_EC2_HOURLY_RATE rather than failing
# or silently reporting $0 -- a conservative estimate beats no estimate.
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

# Reflects operational risk of acting on the finding, not the dollar
# amount: deleting an orphaned volume or releasing an unused IP is low
# risk; stopping/resizing a running server carries more risk even when
# its CPU usage looks idle (it may still serve traffic).
RISK_LEVELS = {
    "EBS Volume": "Low",
    "Elastic IP": "Low",
    "EC2 Instance": "Medium",
}


def _estimate_savings(finding: Finding) -> Optional[float]:
    if finding.resource_type == "EBS Volume":
        size_gb = finding.metadata.get("size_gb")
        if size_gb is None:
            return None
        return round(size_gb * EBS_GP3_PER_GB_MONTH, 2)

    if finding.resource_type == "Elastic IP":
        return ELASTIC_IP_PER_MONTH

    if finding.resource_type == "EC2 Instance":
        instance_type = finding.metadata.get("instance_type")
        hourly_rate = EC2_HOURLY_RATES.get(instance_type, DEFAULT_EC2_HOURLY_RATE)
        return round(hourly_rate * HOURS_PER_MONTH, 2)

    return None


def enrich_with_savings_estimates(findings: List[Finding]) -> List[Finding]:
    """Return new Finding objects with estimated_monthly_savings and
    risk_level filled in.

    A finding representing a scanner's own failure (resource_type
    ending in " Scanner", from the aggregator's fault-isolation path)
    is passed through unchanged -- there's nothing to price on an error.
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
                risk_level=RISK_LEVELS.get(finding.resource_type, "Unknown"),
            )
        )
    return enriched