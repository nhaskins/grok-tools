#!/usr/bin/env python3
"""Resolve secrets from process.env only.

Before scripts run, export-card-secrets.py can inject Grok Bot's secret store
into the environment. This helper only reads that injected env — it never
opens a secrets file.
"""
from __future__ import annotations

import os


def get(*keys: str) -> str | None:
    """Return the first non-empty process.env value among keys."""
    for key in keys:
        val = os.environ.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def require(*keys: str, label: str = "secret") -> str:
    val = get(*keys)
    if not val:
        names = " / ".join(keys)
        raise RuntimeError(
            f"Missing {label} ({names}) in process.env. "
            "Inject Grok Bot's secret store (export-card-secrets.py) before this script runs."
        )
    return val
