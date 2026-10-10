"""Tests for calculate_optimization_score and where it surfaces."""

from cloud_auditor.analysis.recommendations import calculate_optimization_score
from cloud_auditor.reporting.json_report import build_report
from cloud_auditor.reporting.rich_report import render_terminal_report
from cloud_auditor.scanners.base import Finding
from rich.console import Console
import io


def _finding(risk_level, resource_type="EBS Volume"):
    return Finding(
        "res-1",
        resource_type,
        "us-east-1",
        "issue",
        "recommendation",
        risk_level=risk_level,
    )


def test_clean_scan_scores_100():
    assert calculate_optimization_score([]) == 100


def test_low_risk_findings_subtract_one_point_each():
    findings = [_finding("Low"), _finding("Low"), _finding("Low")]
    assert calculate_optimization_score(findings) == 97


def test_medium_risk_findings_subtract_two_points_each():
    findings = [_finding("Medium"), _finding("Medium")]
    assert calculate_optimization_score(findings) == 96


def test_high_risk_findings_subtract_five_points_each():
    findings = [_finding("High")]
    assert calculate_optimization_score(findings) == 95


def test_score_floors_at_zero_not_negative():
    findings = [_finding("High") for _ in range(30)]
    assert calculate_optimization_score(findings) == 0


def test_scanner_failure_findings_are_excluded_from_score():
    findings = [_finding("High", resource_type="EBS Scanner")]
    assert calculate_optimization_score(findings) == 100


def test_build_report_summary_includes_optimization_score():
    findings = [_finding("Low")]
    report = build_report(findings, ["us-east-1"])
    assert report["summary"]["optimization_score"] == 99


def test_render_terminal_report_shows_optimization_score():
    buffer = io.StringIO()
    console = Console(file=buffer, width=150)
    render_terminal_report([_finding("Low")], console=console)
    assert "Optimization score: 99/100" in buffer.getvalue()


def test_render_terminal_report_shows_100_when_no_findings():
    buffer = io.StringIO()
    console = Console(file=buffer, width=150)
    render_terminal_report([], console=console)
    assert "Optimization score: 100/100" in buffer.getvalue()