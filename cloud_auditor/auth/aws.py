"""AWS credential resolution and client construction.

Every AWS call in this tool goes through this module. Scanners never
call boto3.client() directly — they ask for a client here, so that
profile selection, region targeting, and the moto endpoint override
are handled in exactly one place.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    ProfileNotFound,
)


class CredentialError(Exception):
    """Raised when AWS credentials are missing, invalid, or unusable."""


@dataclass
class AWSContext:
    """Resolved authentication settings for a single run of the CLI.

    endpoint_url is what makes local development possible: when it is
    set (e.g. http://localhost:5000), every client is pointed at a
    moto server instead of real AWS. When it is None, boto3 talks to
    the real thing.
    """

    profile: Optional[str] = None
    region: Optional[str] = None
    endpoint_url: Optional[str] = None

    _session: Optional[boto3.session.Session] = None

    @property
    def session(self) -> boto3.session.Session:
        """The boto3 Session for this run, created once and reused.

        Passing profile_name=None makes boto3 fall back to its standard
        credential chain: environment variables, then the shared
        credentials file, then instance metadata.
        """
        if self._session is None:
            try:
                self._session = boto3.session.Session(
                    profile_name=self.profile,
                    region_name=self.region,
                )
            except ProfileNotFound as exc:
                raise CredentialError(
                    f"AWS profile '{self.profile}' was not found. "
                    "Check ~/.aws/credentials or run 'aws configure --profile "
                    f"{self.profile}'."
                ) from exc
        return self._session

    def client(self, service_name: str, region: Optional[str] = None):
        """Build a boto3 client for the given service.

        region overrides the context's region, which matters for
        multi-region scanning: one context, many regional clients.
        """
        return self.session.client(
            service_name,
            region_name=region or self.region,
            endpoint_url=self.endpoint_url,
        )

    def verify_credentials(self) -> dict:
        """Fail fast with a readable message instead of a traceback.

        Calls sts:GetCallerIdentity, which needs no IAM permissions
        beyond valid credentials, and returns the identity so the CLI
        can show the user which account they are about to audit.
        """
        try:
            identity = self.client("sts").get_caller_identity()
        except NoCredentialsError as exc:
            raise CredentialError(
                "No AWS credentials found. Set AWS_ACCESS_KEY_ID and "
                "AWS_SECRET_ACCESS_KEY, run 'aws configure', or pass "
                "--endpoint-url to target a local moto server."
            ) from exc
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "Unknown")
            raise CredentialError(
                f"AWS rejected the credentials (error code: {code}). "
                "They may be expired, revoked, or for the wrong account."
            ) from exc
        except BotoCoreError as exc:
            raise CredentialError(
                f"Could not reach AWS to verify credentials: {exc}"
            ) from exc

        return {
            "account": identity.get("Account"),
            "arn": identity.get("Arn"),
            "user_id": identity.get("UserId"),
        }