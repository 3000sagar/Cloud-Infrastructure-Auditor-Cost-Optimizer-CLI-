"""Tests for the CSV report exporter and the `report --format csv` command."""

import csv

from moto import mock_aws
from typer.testing import CliRunner

from cloud_auditor.auth.aws import create_session
from cloud_auditor.cli import app
from cloud_auditor.reporting.csv_report import write_csv_report
from cloud_auditor.scanners.base import Finding

runner = CliRunner()


def _sample_findings():
    return [
        Finding("vol-1", "EBS Volume", "us-east-1", "Unattached", "Delete"),
        Finding("eipalloc-1", "Elastic IP", "us-east-1", "Unassociated", "Release"),
    ]


def test_write_csv_report_creates_one_row_per_finding(tmp_path):
    output_dir = tmp_path / "nested" / "reports"

    path = write_csv_report(_sample_findings(), output_dir)

    assert path == output_dir / "audit-report.csv"
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["resource_id"] == "vol-1"
    assert rows[0]["resource_type"] == "EBS Volume"
    assert rows[1]["resource_id"] == "eipalloc-1"


def test_write_csv_report_handles_no_findings(tmp_path):
    path = write_csv_report([], tmp_path)

    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Header row still gets written even with zero findings, so the
    # file is still a valid, openable CSV rather than an empty file.
    assert rows == []


@mock_aws
def test_report_command_csv_format_writes_real_findings(tmp_path):
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    volume = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)
    eip = ec2.allocate_address(Domain="vpc")

    result = runner.invoke(
        app,
        ["--region", "us-east-1", "report", "--format", "csv", "--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 0
    with (tmp_path / "audit-report.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    ids = {row["resource_id"] for row in rows}
    assert ids == {volume["VolumeId"], eip["AllocationId"]}