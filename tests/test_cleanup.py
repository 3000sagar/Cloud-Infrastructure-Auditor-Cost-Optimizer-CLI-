"""Tests for the cleanup executor and the `cleanup` CLI command.

Safety is the point of this module, so these tests lean heavily on
proving the negative: an EC2 finding passed to execute_cleanup must
never result in an AWS call or a CleanupResult, and a dry run (or a
declined confirmation) must never delete anything.
"""

from moto import mock_aws
from typer.testing import CliRunner

from cloud_auditor.auth.aws import create_session
from cloud_auditor.cleanup.executor import execute_cleanup, plan_cleanup
from cloud_auditor.cli import app
from cloud_auditor.scanners.base import Finding

runner = CliRunner()


def _ebs_finding(resource_id, region="us-east-1"):
    return Finding(resource_id, "EBS Volume", region, "Unattached", "Delete")


def _eip_finding(resource_id, region="us-east-1"):
    return Finding(resource_id, "Elastic IP", region, "Unassociated", "Release")


def _ec2_finding(resource_id, region="us-east-1"):
    return Finding(resource_id, "EC2 Instance", region, "Idle", "Review")


def test_plan_cleanup_includes_ebs_and_eip_only():
    findings = [
        _ebs_finding("vol-1"),
        _eip_finding("eipalloc-1"),
        _ec2_finding("i-1"),
        Finding("n/a", "EBS Scanner", "us-east-1", "Scan failed: boom", "Retry"),
    ]

    planned = plan_cleanup(findings)

    assert {f.resource_id for f in planned} == {"vol-1", "eipalloc-1"}


def test_plan_cleanup_returns_empty_list_when_nothing_cleanable():
    assert plan_cleanup([_ec2_finding("i-1")]) == []


@mock_aws
def test_execute_cleanup_deletes_ebs_volume():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    volume = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)

    results = execute_cleanup(session, [_ebs_finding(volume["VolumeId"])])

    assert len(results) == 1
    assert results[0].status == "deleted"
    remaining_available = [
        v["VolumeId"]
        for v in ec2.describe_volumes(
            Filters=[{"Name": "status", "Values": ["available"]}]
        )["Volumes"]
    ]
    assert volume["VolumeId"] not in remaining_available


@mock_aws
def test_execute_cleanup_releases_elastic_ip():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    eip = ec2.allocate_address(Domain="vpc")

    results = execute_cleanup(session, [_eip_finding(eip["AllocationId"])])

    assert len(results) == 1
    assert results[0].status == "deleted"
    remaining = [a.get("AllocationId") for a in ec2.describe_addresses()["Addresses"]]
    assert eip["AllocationId"] not in remaining


@mock_aws
def test_execute_cleanup_never_touches_ec2_findings():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    volume = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)

    # A fake/nonexistent EC2 instance ID mixed in -- if execute_cleanup
    # ever tried to act on it, this would raise. It must not even try.
    results = execute_cleanup(
        session, [_ebs_finding(volume["VolumeId"]), _ec2_finding("i-doesnotexist")]
    )

    assert len(results) == 1
    assert results[0].resource_type == "EBS Volume"


@mock_aws
def test_execute_cleanup_reports_error_for_missing_resource():
    session = create_session(region="us-east-1")

    results = execute_cleanup(session, [_ebs_finding("vol-doesnotexist")])

    assert len(results) == 1
    assert results[0].status == "error"
    assert results[0].error


@mock_aws
def test_cleanup_command_dry_run_deletes_nothing_by_default():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    volume = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)

    result = runner.invoke(app, ["--region", "us-east-1", "cleanup"])

    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    still_available = [
        v["VolumeId"]
        for v in ec2.describe_volumes(
            Filters=[{"Name": "status", "Values": ["available"]}]
        )["Volumes"]
    ]
    assert volume["VolumeId"] in still_available


@mock_aws
def test_cleanup_command_execute_declined_deletes_nothing():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    volume = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)

    result = runner.invoke(
        app, ["--region", "us-east-1", "cleanup", "--execute"], input="n\n"
    )

    assert result.exit_code == 1
    assert "Aborted" in result.output
    still_available = [
        v["VolumeId"]
        for v in ec2.describe_volumes(
            Filters=[{"Name": "status", "Values": ["available"]}]
        )["Volumes"]
    ]
    assert volume["VolumeId"] in still_available


@mock_aws
def test_cleanup_command_execute_confirmed_deletes_resource():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    volume = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)

    result = runner.invoke(
        app, ["--region", "us-east-1", "cleanup", "--execute"], input="y\n"
    )

    assert result.exit_code == 0
    assert "1 deleted, 0 error(s)" in result.output
    still_available = [
        v["VolumeId"]
        for v in ec2.describe_volumes(
            Filters=[{"Name": "status", "Values": ["available"]}]
        )["Volumes"]
    ]
    assert volume["VolumeId"] not in still_available