#!/usr/bin/env python3
"""Thin wrapper around dig.py for the old Dig jobs CLI.

Equivalent to: dig.py --preset jobs --trello [same flags]
Use --skip-trello to run research without creating cards.
Deprecated for new callers — prefer dig.py directly.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DIG_PY = SCRIPT_DIR / "dig.py"
LOG_DIR = SCRIPT_DIR / "logs"
LEGACY_LOG = LOG_DIR / "dig-jobs.log"

DEFAULT_WORKSPACE = "/workspace/grok-tools"
DEFAULT_LIST_ID = "6a67a6a08493050e627d93bb"


def _legacy_log(msg: str) -> None:
    ts = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    line = f"[{ts}] {msg}"
    print(line, file=sys.stderr, flush=True)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with LEGACY_LOG.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dig_jobs.py",
        description=(
            "Deprecated wrapper: Dig jobs via dig.py --preset jobs --trello. "
            "Prefer /workspace/grok-tools/dig.py for new use."
        ),
    )
    p.add_argument(
        "--prompt",
        help="Job-search brief for the agent. If omitted, read JSON from stdin.",
    )
    p.add_argument(
        "--workspace",
        default=None,
        help=f"Agent workspace path (default: {DEFAULT_WORKSPACE})",
    )
    p.add_argument(
        "--list-id",
        default=None,
        dest="list_id",
        help=f"Trello list id for new cards (default: {DEFAULT_LIST_ID})",
    )
    p.add_argument(
        "--skip-trello",
        action="store_true",
        help="Run the agent only; do not create Trello cards.",
    )
    return p


def main() -> None:
    parser = build_parser()
    args, unknown = parser.parse_known_args()

    if not DIG_PY.is_file():
        print(
            '{"ok": false, "statusCode": 500, "error": "dig.py not found", "jobs": [], "trello": []}',
            flush=True,
        )
        sys.exit(1)

    _legacy_log(
        "dig_jobs.py is a thin wrapper → dig.py --preset jobs "
        + ("(skip-trello)" if args.skip_trello else "--trello")
        + "; prefer dig.py for new callers"
    )

    cmd = [sys.executable, str(DIG_PY), "--preset", "jobs"]
    if args.skip_trello:
        cmd.append("--skip-trello")
    else:
        cmd.append("--trello")

    if args.prompt is not None:
        cmd.extend(["--prompt", args.prompt])
    if args.workspace is not None:
        cmd.extend(["--workspace", args.workspace])
    if args.list_id is not None:
        cmd.extend(["--list-id", args.list_id])
    if unknown:
        cmd.extend(unknown)

    # Forward stdin when --prompt omitted (webhook JSON shape).
    if args.prompt is None:
        stdin_data = sys.stdin.read()
        proc = subprocess.run(cmd, input=stdin_data, text=True)
    else:
        proc = subprocess.run(cmd)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
