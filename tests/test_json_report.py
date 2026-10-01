"""Tests for the JSON report exporter and the `report` command."""

import datetime as dt
import json

from moto import mock_aws
from typer.testing import CliRunner

from cloud_auditor.auth.aws import create_session
from cloud_auditor.cli import app
from cloud_auditor.reporting.json_report import build_report, write_json_report
from cloud_auditor.scanners.base import Finding

runner = CliRunner()


def _sample_findings():
    return [
        Finding("vol-1", "EBS Volume", "us-east-1", "Unattached", "Delete"),
        Finding("vol-2", "EBS Volume", "us-east-1", "Unattached", "Delete"),
        Finding("eipalloc-1", "Elastic IP", "us-east-1", "Unassociated", "Release"),
    ]


def test_build_report_summarises_findings_by_type():
    report = build_report(_sample_findings(), regions=["us-east-1"])

    assert report["regions"] == ["us-east-1"]
    assert report["summary"]["total_findings"] == 3
    assert report["summary"]["by_type"] == {"EBS Volume": 2, "Elastic IP": 1}
    assert report["findings"][0]["resource_id"] == "vol-1"


def test_write_json_report_creates_directory_and_valid_json(tmp_path):
    output_dir = tmp_path / "nested" / "reports"

    path = write_json_report(_sample_findings(), ["us-east-1"], output_dir)

    assert path == output_dir / "audit-report.json"
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["summary"]["total_findings"] == 3


@mock_aws
def test_report_command_writes_real_findings(tmp_path):
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    cloudwatch = session.client("cloudwatch", region_name="us-east-1")

    volume = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)
    eip = ec2.allocate_address(Domain="vpc")
    instance = ec2.run_instances(
        ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t2.micro"
    )["Instances"][0]
    now = dt.datetime.now(dt.timezone.utc)
    for day_offset in range(14):
        cloudwatch.put_metric_data(
            Namespace="AWS/EC2",
            MetricData=[
                {
                    "MetricName": "CPUUtilization",
                    "Dimensions": [{"Name": "InstanceId", "Value": instance["InstanceId"]}],
                    "Timestamp": now - dt.timedelta(days=day_offset),
                    "Value": 1.5,
                    "Unit": "Percent",
                }
            ],
        )

    result = runner.invoke(
        app,
        ["--region", "us-east-1", "report", "--format", "json", "--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 0
    loaded = json.loads((tmp_path / "audit-report.json").read_text(encoding="utf-8"))
    ids = {f["resource_id"] for f in loaded["findings"]}
    assert ids == {volume["VolumeId"], eip["AllocationId"], instance["InstanceId"]}
    assert loaded["summary"]["total_findings"] == 3


def test_report_command_rejects_unknown_format():
    result = runner.invoke(app, ["report", "--format", "xml"])
    assert result.exit_code == 2
    assert "Unknown format" in result.stdout



@mock_aws
def test_report_without_region_scans_every_enabled_region(tmp_path):
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    volume = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)

    result = runner.invoke(app, ["report", "--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    loaded = json.loads((tmp_path / "audit-report.json").read_text(encoding="utf-8"))
    assert len(loaded["regions"]) > 1
    assert "us-east-1" in loaded["regions"]
    assert volume["VolumeId"] in {f["resource_id"] for f in loaded["findings"]}