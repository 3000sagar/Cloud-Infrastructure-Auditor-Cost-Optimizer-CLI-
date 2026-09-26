"""End-to-end test for the wired-up `audit` command -- invokes the
real CLI, not just the aggregator function directly.
"""

import datetime as dt

from moto import mock_aws
from typer.testing import CliRunner

from cloud_auditor.auth.aws import create_session
from cloud_auditor.cli import app

runner = CliRunner()


@mock_aws
def test_audit_command_reports_all_finding_types():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    cloudwatch = session.client("cloudwatch", region_name="us-east-1")

    orphaned_volume = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)
    orphaned_eip = ec2.allocate_address(Domain="vpc")
    idle_instance = ec2.run_instances(
        ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t2.micro"
    )["Instances"][0]

    now = dt.datetime.now(dt.timezone.utc)
    for day_offset in range(14):
        cloudwatch.put_metric_data(
            Namespace="AWS/EC2",
            MetricData=[
                {
                    "MetricName": "CPUUtilization",
                    "Dimensions": [
                        {"Name": "InstanceId", "Value": idle_instance["InstanceId"]}
                    ],
                    "Timestamp": now - dt.timedelta(days=day_offset),
                    "Value": 1.5,
                    "Unit": "Percent",
                }
            ],
        )

    result = runner.invoke(app, ["--region", "us-east-1", "audit"])

    assert result.exit_code == 0
    assert orphaned_volume["VolumeId"] in result.stdout
    assert orphaned_eip["AllocationId"] in result.stdout
    assert idle_instance["InstanceId"] in result.stdout


@mock_aws
def test_audit_command_reports_no_issues_when_clean():
    result = runner.invoke(app, ["--region", "us-east-1", "audit"])
    assert result.exit_code == 0
    assert "No issues found" in result.stdout