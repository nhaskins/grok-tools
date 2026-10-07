#!/usr/bin/env python3
"""POST a message to Captain Riker's Titan webhook.

Secrets (process.env only — never log values):
  RIKER_WEBHOOK_URL   HTTPS webhook URL
  RIKER_WEBHOOK_AUTH  Bearer token, raw key, or full "Authorization: …" value

Usage:
  echo '{"message":"Hello Number One"}' | python3 send_riker.py
  python3 send_riker.py --message "Hello Number One"
  python3 send_riker.py --json '{"message":"…","from":"Picard"}'

Stdout JSON: {"ok": true, "status": 200, …} or {"ok": false, "error": "…"}
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grok_secrets  # noqa: E402


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def emit(obj: dict, code: int = 0) -> None:
    print(json.dumps(obj), flush=True)
    sys.exit(code)


def auth_header(raw: str) -> str:
    v = raw.strip()
    low = v.lower()
    if low.startswith("authorization:"):
        return v.split(":", 1)[1].strip()
    if low.startswith("bearer "):
        return v
    return f"Bearer {v}"


def build_payload(args: argparse.Namespace) -> dict:
    if args.json:
        try:
            data = json.loads(args.json)
        except json.JSONDecodeError as exc:
            emit({"ok": False, "error": f"Invalid --json: {exc}"}, 1)
        if not isinstance(data, dict):
            emit({"ok": False, "error": "--json must be an object"}, 1)
        return data
    if args.message is not None:
        return {"message": args.message, "from": "Picard"}
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if not raw:
            emit({"ok": False, "error": "Empty stdin"}, 1)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            emit({"ok": False, "error": f"Invalid stdin JSON: {exc}"}, 1)
        if not isinstance(data, dict):
            emit({"ok": False, "error": "stdin JSON must be an object"}, 1)
        return data
    emit({"ok": False, "error": "Provide --message, --json, or stdin JSON"}, 1)
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a message to Riker Titan webhook")
    parser.add_argument("--message", "-m", help="Plain message text")
    parser.add_argument("--json", help="Raw JSON object body")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    try:
        url = grok_secrets.require("RIKER_WEBHOOK_URL", label="Riker webhook URL")
        auth = grok_secrets.require("RIKER_WEBHOOK_AUTH", label="Riker webhook auth")
    except RuntimeError as exc:
        emit({"ok": False, "error": str(exc)}, 1)

    if not url.lower().startswith("https://"):
        emit({"ok": False, "error": "RIKER_WEBHOOK_URL must be https://"}, 1)

    payload = build_payload(args)
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": auth_header(auth),
            "Accept": "application/json",
            "User-Agent": "grok-tools-send-riker/1.0",
        },
    )
    log(f"POSTing to Riker Titan ({len(body)} bytes)")
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            resp_body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")[:500]
        emit(
            {
                "ok": False,
                "error": f"HTTP {exc.code}",
                "status": exc.code,
                "body": err_body,
            },
            1,
        )
    except urllib.error.URLError as exc:
        emit({"ok": False, "error": f"URL error: {exc.reason}"}, 1)

    out: dict = {"ok": True, "status": status}
    if resp_body.strip():
        try:
            out["data"] = json.loads(resp_body)
        except json.JSONDecodeError:
            out["body"] = resp_body[:500]
    emit(out)


if __name__ == "__main__":
    main()
