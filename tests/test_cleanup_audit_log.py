"""Tests for the cleanup audit log and its wiring into `cleanup --execute`."""

import json

from moto import mock_aws
from typer.testing import CliRunner

from cloud_auditor.auth.aws import create_session
from cloud_auditor.cleanup.audit_log import write_cleanup_audit_log
from cloud_auditor.cleanup.executor import CleanupResult
from cloud_auditor.cli import app

runner = CliRunner()


def test_write_cleanup_audit_log_appends_one_line_per_result(tmp_path):
    results = [
        CleanupResult("vol-1", "EBS Volume", "us-east-1", "deleted"),
        CleanupResult("eipalloc-1", "Elastic IP", "us-east-1", "error", "boom"),
    ]

    path = write_cleanup_audit_log(results, tmp_path)

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    entries = [json.loads(line) for line in lines]
    assert entries[0]["resource_id"] == "vol-1"
    assert entries[0]["status"] == "deleted"
    assert entries[1]["resource_id"] == "eipalloc-1"
    assert entries[1]["status"] == "error"
    assert entries[1]["error"] == "boom"


def test_write_cleanup_audit_log_creates_directory_if_missing(tmp_path):
    output_dir = tmp_path / "nested" / "logs"

    path = write_cleanup_audit_log([CleanupResult("vol-1", "EBS Volume", "us-east-1", "deleted")], output_dir)

    assert path == output_dir / "cleanup-audit.jsonl"
    assert path.exists()


def test_write_cleanup_audit_log_appends_across_multiple_calls(tmp_path):
    write_cleanup_audit_log([CleanupResult("vol-1", "EBS Volume", "us-east-1", "deleted")], tmp_path)
    path = write_cleanup_audit_log(
        [CleanupResult("vol-2", "EBS Volume", "us-east-1", "deleted")], tmp_path
    )

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_write_cleanup_audit_log_includes_timestamp(tmp_path):
    path = write_cleanup_audit_log(
        [CleanupResult("vol-1", "EBS Volume", "us-east-1", "deleted")], tmp_path
    )

    entry = json.loads(path.read_text(encoding="utf-8").strip())
    assert "timestamp" in entry
    assert entry["timestamp"]


@mock_aws
def test_cleanup_command_execute_confirmed_writes_audit_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    volume = ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)

    result = runner.invoke(
        app, ["--region", "us-east-1", "cleanup", "--execute"], input="y\n"
    )

    assert result.exit_code == 0
    log_path = tmp_path / "logs" / "cleanup-audit.jsonl"
    assert log_path.exists()
    entry = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert entry["resource_id"] == volume["VolumeId"]
    assert entry["status"] == "deleted"


@mock_aws
def test_cleanup_command_dry_run_does_not_write_audit_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = create_session(region="us-east-1")
    ec2 = session.client("ec2", region_name="us-east-1")
    ec2.create_volume(AvailabilityZone="us-east-1a", Size=8)

    runner.invoke(app, ["--region", "us-east-1", "cleanup"])

    assert not (tmp_path / "logs" / "cleanup-audit.jsonl").exists()