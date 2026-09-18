"""Shared botocore configuration: adaptive retry/backoff for every client."""

from botocore.config import Config


def get_boto_config() -> Config:
    return Config(
        retries={"max_attempts": 10, "mode": "adaptive"},
        connect_timeout=5,
        read_timeout=30,
    )