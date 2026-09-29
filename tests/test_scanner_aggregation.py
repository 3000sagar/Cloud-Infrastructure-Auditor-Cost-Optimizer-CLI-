"""The audit must honour config/config.yaml and survive a failing scanner."""

from unittest.mock import patch

from cloud_auditor.audit.orchestrator import run_audit
from cloud_auditor.scanners.base import Finding, ScannerError

EBS = "cloud_auditor.scanners.aggregator.scan_unattached_volumes"
EIP = "cloud_auditor.scanners.aggregator.scan_unassociated_addresses"
EC2 = "cloud_auditor.scanners.aggregator.scan_underutilized_instances"
CONFIG = "cloud_auditor.scanners.aggregator.load_audit_config"


def _finding(resource_id, resource_type):
    return Finding(resource_id, resource_type, "us-east-1", "issue", "fix")


def test_disabled_scanner_is_skipped():
    config = {
        "ebs": {"enabled": False},
        "elastic_ip": {"enabled": True},
        "ec2": {"enabled": True, "cpu_threshold": 5, "period_days": 14},
    }
    with patch(CONFIG, return_value=config), patch(EBS) as ebs, patch(
        EIP, return_value=[_finding("eipalloc-1", "Elastic IP")]
    ), patch(EC2, return_value=[]):
        findings = run_audit(session=object(), regions=["us-east-1"])

    ebs.assert_not_called()
    assert [f.resource_id for f in findings] == ["eipalloc-1"]


def test_config_thresholds_reach_the_ec2_scanner():
    config = {"ec2": {"enabled": True, "cpu_threshold": 12, "period_days": 30}}
    with patch(CONFIG, return_value=config), patch(EBS, return_value=[]), patch(
        EIP, return_value=[]
    ), patch(EC2, return_value=[]) as ec2:
        run_audit(session=object(), regions=["us-east-1"])

    _, kwargs = ec2.call_args
    assert kwargs["cpu_threshold"] == 12
    assert kwargs["period_days"] == 30


def test_one_failing_scanner_does_not_abort_the_audit():
    with patch(EBS, side_effect=ScannerError("AccessDenied")), patch(
        EIP, return_value=[_finding("eipalloc-1", "Elastic IP")]
    ), patch(EC2, return_value=[]):
        findings = run_audit(session=object(), regions=["us-east-1"])

    types = [f.resource_type for f in findings]
    assert "EBS Scanner" in types
    assert "Elastic IP" in types
    assert any("AccessDenied" in f.issue for f in findings)