"""Load audit configuration from config/config.yaml.

Falls back to built-in defaults if the file is missing or a key is
absent, so the tool still works with no config file present.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_CONFIG_PATH = Path("config/config.yaml")

DEFAULTS: Dict[str, Any] = {
    "ec2": {"enabled": True, "cpu_threshold": 5, "period_days": 14},
    "ebs": {"enabled": True},
    "elastic_ip": {"enabled": True},
}


def load_audit_config(path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Return the 'audit' section of config.yaml, merged over defaults.

    A value present in the file overrides the default; a key missing
    from the file (or a missing file entirely) falls back to DEFAULTS.
    """
    config = {scanner: dict(settings) for scanner, settings in DEFAULTS.items()}

    if path.exists():
        with path.open() as f:
            loaded = yaml.safe_load(f) or {}
        for scanner, settings in loaded.get("audit", {}).items():
            config.setdefault(scanner, {}).update(settings)

    return config