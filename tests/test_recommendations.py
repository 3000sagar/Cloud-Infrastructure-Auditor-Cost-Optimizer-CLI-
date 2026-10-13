"""Tests for cost estimates, risk levels, and optimization scoring."""

from cloud_auditor.analysis.recommendations import (
    calculate_optimization_score,
    enrich_with_savings_estimates,
)

from cloud_auditor.scanners.base import Finding


def test_ebs_volume_savings_scales_with_size():
    finding = Finding(
        "vol-1",
        "EBS Volume",
        "us-east-1",
        "Unattached",
        "Delete",
        metadata={"size_gb": 100},
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings == 8.00
    assert enriched.risk_level == "Low"


def test_ebs_volume_without_size_metadata_has_no_estimate():
    finding = Finding(
        "vol-1",
        "EBS Volume",
        "us-east-1",
        "Unattached",
        "Delete",
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings is None


def test_ebs_volume_with_negative_size_has_no_estimate():
    finding = Finding(
        "vol-1",
        "EBS Volume",
        "us-east-1",
        "Unattached",
        "Delete",
        metadata={"size_gb": -100},
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings is None


def test_ebs_volume_with_invalid_size_has_no_estimate():
    finding = Finding(
        "vol-1",
        "EBS Volume",
        "us-east-1",
        "Unattached",
        "Delete",
        metadata={"size_gb": "invalid"},
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings is None


def test_ebs_volume_with_boolean_size_has_no_estimate():
    finding = Finding(
        "vol-1",
        "EBS Volume",
        "us-east-1",
        "Unattached",
        "Delete",
        metadata={"size_gb": True},
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings is None


def test_ebs_volume_with_infinite_size_has_no_estimate():
    finding = Finding(
        "vol-1",
        "EBS Volume",
        "us-east-1",
        "Unattached",
        "Delete",
        metadata={"size_gb": float("inf")},
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings is None


def test_elastic_ip_uses_flat_rate():
    finding = Finding(
        "eipalloc-1",
        "Elastic IP",
        "us-east-1",
        "Unassociated",
        "Release",
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings == 3.60
    assert enriched.risk_level == "Low"


def test_known_ec2_instance_type_uses_its_own_rate():
    finding = Finding(
        "i-1",
        "EC2 Instance",
        "us-east-1",
        "Idle",
        "Review",
        metadata={"instance_type": "t2.micro"},
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings == round(
        0.0116 * 730,
        2,
    )
    assert enriched.risk_level == "Medium"


def test_unknown_ec2_instance_type_falls_back_to_default_rate():
    finding = Finding(
        "i-1",
        "EC2 Instance",
        "us-east-1",
        "Idle",
        "Review",
        metadata={"instance_type": "x9.mega-giant"},
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings == round(
        0.10 * 730,
        2,
    )




def test_unknown_resource_type_has_no_estimate():
    finding = Finding(
        "resource-1",
        "Unknown Resource",
        "us-east-1",
        "Unknown issue",
        "Investigate",
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings is None
    assert enriched.risk_level == "Unknown"


def test_scanner_failure_finding_passes_through_unestimated():
    finding = Finding(
        "-",
        "EBS Scanner",
        "us-east-1",
        "Scan failed: denied",
        "Check IAM",
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings is None
    assert enriched.risk_level == "Unknown"
    assert enriched is finding


def test_empty_findings_have_perfect_score():
    assert calculate_optimization_score([]) == 100


def test_low_risk_finding_reduces_score_by_one():
    finding = Finding(
        "vol-1",
        "EBS Volume",
        "us-east-1",
        "Unattached",
        "Delete",
        risk_level="Low",
    )

    assert calculate_optimization_score([finding]) == 99


def test_medium_risk_finding_reduces_score_by_two():
    finding = Finding(
        "i-1",
        "EC2 Instance",
        "us-east-1",
        "Idle",
        "Review",
        risk_level="Medium",
    )

    assert calculate_optimization_score([finding]) == 98


def test_high_risk_finding_reduces_score_by_five():
    finding = Finding(
        "resource-1",
        "Unknown Resource",
        "us-east-1",
        "Potential risk",
        "Investigate",
        risk_level="High",
    )

    assert calculate_optimization_score([finding]) == 95


def test_unknown_risk_level_uses_default_penalty():
    finding = Finding(
        "resource-1",
        "Unknown Resource",
        "us-east-1",
        "Potential risk",
        "Investigate",
        risk_level="Unexpected",
    )

    assert calculate_optimization_score([finding]) == 95


def test_optimization_score_never_falls_below_zero():
    findings = [
        Finding(
            f"resource-{index}",
            "Unknown Resource",
            "us-east-1",
            "Potential risk",
            "Investigate",
            risk_level="High",
        )
        for index in range(25)
    ]

    assert calculate_optimization_score(findings) == 0


def test_scanner_failures_do_not_reduce_optimization_score():
    finding = Finding(
        "-",
        "EBS Scanner",
        "us-east-1",
        "Scan failed",
        "Check IAM",
        risk_level="High",
    )

    assert calculate_optimization_score([finding]) == 100


def test_multiple_findings_reduce_score_correctly():
    findings = [
        Finding(
            "vol-1",
            "EBS Volume",
            "us-east-1",
            "Unattached",
            "Delete",
            risk_level="Low",
        ),
        Finding(
            "i-1",
            "EC2 Instance",
            "us-east-1",
            "Idle",
            "Review",
            risk_level="Medium",
        ),
    ]

    assert calculate_optimization_score(findings) == 97



def test_ec2_without_instance_type_has_no_estimate():
    finding = Finding(
        "i-1",
        "EC2 Instance",
        "us-east-1",
        "Idle",
        "Review",
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings is None
    assert enriched.risk_level == "Medium"


def test_ec2_with_empty_instance_type_has_no_estimate():
    finding = Finding(
        "i-1",
        "EC2 Instance",
        "us-east-1",
        "Idle",
        "Review",
        metadata={"instance_type": "   "},
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings is None


def test_ec2_with_invalid_instance_type_metadata_has_no_estimate():
    finding = Finding(
        "i-1",
        "EC2 Instance",
        "us-east-1",
        "Idle",
        "Review",
        metadata={"instance_type": 123},
    )

    [enriched] = enrich_with_savings_estimates([finding])

    assert enriched.estimated_monthly_savings is None