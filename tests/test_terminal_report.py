"""Tests for the Rich terminal report renderer and `report --format terminal`."""

import io

from moto import mock_aws
from rich.console import Console
from typer.testing import CliRunner

from cloud_auditor.auth.aws import create_session
from cloud_auditor.cli import app
from cloud_auditor.reporting.rich_report import build_findings_table, render_terminal_report
from cloud_auditor.scanners.base import Finding

runner = CliRunner()


def _sample_findings():
    return [
        Finding(
            "vol-1",
            "EBS Volume",
            "us-east-1",
            "Unattached",
            "Delete",
            metadata={"size_gb": 20},
            estimated_monthly_savings=1.60,
            risk_level="Low",
        ),
        Finding(
            "eipalloc-1",
            "Elastic IP",
            "us-east-1",
            "Unassociated",
            "Release",
            estimated_monthly_savings=3.60,
            risk_level="Low",
        ),
    ]


def _render_to_text(findings):
    buffer = io.StringIO()
    console = Console(file=buffer, width=150)
    render_terminal_report(findings, console=console)
    return buffer.getvalue()


def test_build_findings_table_has_one_row_per_finding():
    table = build_findings_table(_sample_findings())

    assert len(table.columns) == 7
    assert table.columns[0].header == "Resource ID"
    assert table.row_count == 2


def test_render_terminal_report_shows_no_findings_message_when_empty():
    output = _render_to_text([])

    assert "No audit findings detected" in output


def test_render_terminal_report_shows_resource_ids_and_savings():
    output = _render_to_text(_sample_findings())

    assert "vol-1" in output
    assert "eipalloc-1" in output
    assert "$1.60" in output
    assert "$3.60" in output


@mock_aws
def test_report_command_terminal_format_prints_real_findings():
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    volume = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)
    eip = ec2.allocate_address(Domain="vpc")

    result = runner.invoke(
        app,
        ["--region", "us-east-1", "report", "--format", "terminal"],
    )

    assert result.exit_code == 0
    assert volume["VolumeId"] in result.output
    assert eip["AllocationId"] in result.output