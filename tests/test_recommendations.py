"""Tests for cost-estimate and risk-level enrichment."""

from cloud_auditor.analysis.recommendations import enrich_with_savings_estimates
from cloud_auditor.scanners.base import Finding


def test_ebs_volume_savings_scales_with_size():
    finding = Finding(
        "vol-1", "EBS Volume", "us-east-1", "Unattached", "Delete",
        metadata={"size_gb": 100},
    )
    [enriched] = enrich_with_savings_estimates([finding])
    assert enriched.estimated_monthly_savings == 8.00  # 100 GB * $0.08/GB-month
    assert enriched.risk_level == "Low"


def test_ebs_volume_without_size_metadata_has_no_estimate():
    finding = Finding("vol-1", "EBS Volume", "us-east-1", "Unattached", "Delete")
    [enriched] = enrich_with_savings_estimates([finding])
    assert enriched.estimated_monthly_savings is None


def test_elastic_ip_uses_flat_rate():
    finding = Finding("eipalloc-1", "Elastic IP", "us-east-1", "Unassociated", "Release")
    [enriched] = enrich_with_savings_estimates([finding])
    assert enriched.estimated_monthly_savings == 3.60
    assert enriched.risk_level == "Low"


def test_known_ec2_instance_type_uses_its_own_rate():
    finding = Finding(
        "i-1", "EC2 Instance", "us-east-1", "Idle", "Review",
        metadata={"instance_type": "t2.micro"},
    )
    [enriched] = enrich_with_savings_estimates([finding])
    assert enriched.estimated_monthly_savings == round(0.0116 * 730, 2)
    assert enriched.risk_level == "Medium"


def test_unknown_ec2_instance_type_falls_back_to_default_rate():
    finding = Finding(
        "i-1", "EC2 Instance", "us-east-1", "Idle", "Review",
        metadata={"instance_type": "x9.mega-giant"},
    )
    [enriched] = enrich_with_savings_estimates([finding])
    assert enriched.estimated_monthly_savings == round(0.10 * 730, 2)


def test_scanner_failure_finding_passes_through_unestimated():
    finding = Finding("-", "EBS Scanner", "us-east-1", "Scan failed: denied", "Check IAM")
    [enriched] = enrich_with_savings_estimates([finding])
    assert enriched.estimated_monthly_savings is None
    assert enriched.risk_level == "Unknown"
    assert enriched is finding  # passed through, not rebuilt