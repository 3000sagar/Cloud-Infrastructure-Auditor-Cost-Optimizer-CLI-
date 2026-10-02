from unittest.mock import patch

from cloud_auditor.audit.orchestrator import run_audit
from cloud_auditor.scanners.base import Finding


def test_run_audit_combines_findings_from_all_scanners():
    ebs_finding = Finding(
        resource_id="vol-123",
        resource_type="EBS Volume",
        region="ap-south-1",
        issue="Unattached",
        recommendation="Delete if unused",
    )

    eip_finding = Finding(
        resource_id="eipalloc-123",
        resource_type="Elastic IP",
        region="ap-south-1",
        issue="Unassociated",
        recommendation="Release if unused",
    )

    ec2_finding = Finding(
        resource_id="i-123",
        resource_type="EC2 Instance",
        region="ap-south-1",
        issue="Low CPU",
        recommendation="Review for downsizing",
    )

    with (
        patch(
            "cloud_auditor.scanners.aggregator.scan_unattached_volumes",
            return_value=[ebs_finding],
        ),
        patch(
            "cloud_auditor.scanners.aggregator.scan_unassociated_addresses",
            return_value=[eip_finding],
        ),
        patch(
            "cloud_auditor.scanners.aggregator.scan_underutilized_instances",
            return_value=[ec2_finding],
        ),
    ):
        findings = run_audit(
            session=object(),
            regions=["ap-south-1"],
        )

    # Exact equality isn't used here: the aggregator enriches findings
    # with cost/risk estimates (see test_recommendations.py), so the
    # returned objects legitimately differ from what the scanners
    # returned. What this test actually verifies is that all three
    # scanners' findings made it into the combined result.
    ids = {f.resource_id for f in findings}
    assert ids == {"vol-123", "eipalloc-123", "i-123"}