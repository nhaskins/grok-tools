#!/usr/bin/env python3
"""Export Grok Bot secret-store card keys as shell KEY=value lines for `eval`/`set -a`.

Reads the platform secret store (default: Grok Bot box-secrets card) and prints
assignments suitable for injecting into process.env before running workflow scripts.
Never logs secret values.

Override store path with GROKBOT_SECRETS_STORE if needed.
"""
from __future__ import annotations

import json
import os
import shlex
from pathlib import Path

STORE = Path(
    os.environ.get("GROKBOT_SECRETS_STORE", "/home/box/agent-data/box-secrets.json")
)


def main() -> None:
    if not STORE.is_file():
        raise SystemExit(f"Grok Bot secret store missing: {STORE}")
    data = json.loads(STORE.read_text(encoding="utf-8"))
    card = data.get("card") or {}
    if not isinstance(card, dict):
        raise SystemExit("secret store card missing or invalid")
    for k, v in card.items():
        if not isinstance(k, str) or not k:
            continue
        if v is None:
            continue
        print(f"{k}={shlex.quote(str(v))}")


if __name__ == "__main__":
    main()
