"""AWS credential resolution.

Uses boto3's standard credential chain (env vars, ~/.aws, IAM role).
If an endpoint URL is given (e.g. a local moto server), dummy
credentials are supplied when none exist, so no real account is needed.
"""

from typing import Optional

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    ProfileNotFound,
)

from cloud_auditor.utils.retry import get_boto_config

DEFAULT_REGION = "us-east-1"


class AuthError(Exception):
    """Raised when credentials can't be resolved or verified."""


def create_session(
    profile: Optional[str] = None,
    region: Optional[str] = None,
    endpoint_url: Optional[str] = None,
) -> boto3.Session:
    try:
        session = boto3.Session(
            profile_name=profile, region_name=region or DEFAULT_REGION
        )
    except ProfileNotFound as exc:
        raise AuthError(f"AWS profile not found: {profile}") from exc

    if endpoint_url and session.get_credentials() is None:
        session = boto3.Session(
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
            region_name=region or DEFAULT_REGION,
        )
    return session


def get_client(session, service, region=None, endpoint_url=None):
    return session.client(
        service,
        region_name=region or session.region_name or DEFAULT_REGION,
        endpoint_url=endpoint_url,
        config=get_boto_config(),
    )


def verify_credentials(session, endpoint_url: Optional[str] = None) -> dict:
    """Fail fast with a readable error instead of a raw traceback."""
    try:
        return get_client(session, "sts", endpoint_url=endpoint_url).get_caller_identity()
    except NoCredentialsError as exc:
        raise AuthError("No AWS credentials found. Configure a profile or env vars.") from exc
    except ClientError as exc:
        raise AuthError(f"AWS rejected the credentials: {exc}") from exc
    except BotoCoreError as exc:
        raise AuthError(f"Could not reach AWS: {exc}") from exc