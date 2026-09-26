"""Tests for config/config.yaml loading."""

from cloud_auditor.utils.config import load_audit_config


def test_loads_real_config_file():
    config = load_audit_config()
    assert config["ec2"]["cpu_threshold"] == 5
    assert config["ec2"]["period_days"] == 14
    assert config["ebs"]["enabled"] is True
    assert config["elastic_ip"]["enabled"] is True


def test_falls_back_to_defaults_when_file_missing(tmp_path):
    missing_path = tmp_path / "does_not_exist.yaml"
    config = load_audit_config(path=missing_path)
    assert config["ec2"]["cpu_threshold"] == 5
    assert config["ebs"]["enabled"] is True