"""Tests for region discovery and credential verification against a
mocked AWS backend (moto's in-process mock_aws decorator).
"""

from moto import mock_aws

from cloud_auditor.auth.aws import create_session, verify_credentials
from cloud_auditor.utils.regions import get_enabled_regions


@mock_aws
def test_get_enabled_regions_returns_sorted_names():
    session = create_session(region="us-east-1")

    result = get_enabled_regions(session)

    assert isinstance(result, list)
    assert "us-east-1" in result
    assert result == sorted(result)


@mock_aws
def test_verify_credentials_returns_identity():
    session = create_session(region="us-east-1")

    identity = verify_credentials(session)

    assert "Account" in identity
    assert "Arn" in identity