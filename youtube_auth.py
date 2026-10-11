#!/usr/bin/env python3
"""YouTube Data API v3 OAuth helper for Grok Bot. Prints one JSON object to stdout.

Nate approves in his OWN browser (a different machine), so a localhost callback on
the box can never be received. Two paths:

  1. Device flow (preferred): `start` prints a verification URL + short user code.
     Nate opens the URL anywhere, enters the code, approves. Then `poll` (or
     `start --wait`) exchanges it. Needs a "TVs and Limited Input devices" client.
  2. Manual code: if the client rejects device flow, `start` prints an auth URL with
     redirect_uri http://localhost (override with --redirect-uri). After approving,
     Nate's browser lands on a dead page; he copies the full URL from the address
     bar and Grok Bot runs `finish --alias X --code-env VAR` (or pipes it on stdin).
     Never pass the code on argv.

Tokens: data/youtube_tokens.json (0600), keyed by alias (main, clips), with the
channel id/title fetched after auth. Pending auth state: data/youtube_pending.json.

Secrets (process.env via grok_secrets): YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET,
falling back to GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET. Never printed.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets as pysecrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
TOKENS_PATH = DATA_DIR / "youtube_tokens.json"
PENDING_PATH = DATA_DIR / "youtube_pending.json"

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
DEVICE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://www.googleapis.com/youtube/v3"

# Device flow only allows the broad youtube scope (it covers upload + thumbnails).
DEVICE_SCOPES = ["https://www.googleapis.com/auth/youtube"]
MANUAL_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]
ALIASES = ("main", "clips")
DEFAULT_REDIRECT = "http://localhost"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def emit(obj: dict) -> None:
    print(json.dumps(obj, indent=2), flush=True)


def emit_failure(error: str, **extra) -> None:
    emit({"ok": False, "error": error, **extra})
    sys.exit(1)


class GoogleError(RuntimeError):
    def __init__(self, status: int, payload: dict | str):
        self.status = status
        self.payload = payload
        if isinstance(payload, dict):
            err = payload.get("error")
            if isinstance(err, dict):  # API-style error
                msg = err.get("message") or json.dumps(err)
                self.code = (err.get("errors") or [{}])[0].get("reason") or err.get("status")
            else:
                msg = f"{err}: {payload.get('error_description', '')}".strip(": ")
                self.code = err
        else:
            msg, self.code = str(payload)[:500], None
        super().__init__(f"HTTP {status}: {msg}")


# ---------- secrets / files ----------

def client_creds() -> tuple[str, str | None]:
    import grok_secrets

    cid = grok_secrets.require("YOUTUBE_CLIENT_ID", "GOOGLE_CLIENT_ID", label="Google OAuth client id")
    csec = grok_secrets.get("YOUTUBE_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET")
    return cid, csec


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text() or "{}")


def _write_private_json(path: Path, obj: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def load_tokens() -> dict:
    return _read_json(TOKENS_PATH)


def save_tokens(tokens: dict) -> None:
    _write_private_json(TOKENS_PATH, tokens)


# ---------- HTTP ----------

def http_json(url: str, data: dict | None = None, headers: dict | None = None,
              method: str | None = None, body: bytes | None = None, timeout: int = 60) -> dict:
    if data is not None:
        body = urlencode(data).encode()
        headers = {"Content-Type": "application/x-www-form-urlencoded", **(headers or {})}
    req = Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode() or "{}"
            return json.loads(raw)
    except HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = raw
        raise GoogleError(e.code, payload) from None


def exchange_token(params: dict) -> dict:
    cid, csec = client_creds()
    data = {"client_id": cid, **params}
    if csec:
        data["client_secret"] = csec
    return http_json(TOKEN_URL, data=data)


def fetch_channel(access_token: str) -> dict:
    j = http_json(f"{API_BASE}/channels?part=snippet&mine=true",
                  headers={"Authorization": f"Bearer {access_token}"})
    items = j.get("items") or []
    if not items:
        return {"channel_id": None, "channel_title": None}
    it = items[0]
    return {"channel_id": it.get("id"), "channel_title": it.get("snippet", {}).get("title")}


def access_token_for(alias: str) -> tuple[str, dict]:
    """Refresh and return (access_token, token_record). Used by youtube_upload.py."""
    tokens = load_tokens()
    rec = tokens.get(alias)
    if not rec or not rec.get("refresh_token"):
        raise RuntimeError(f"No refresh token for alias '{alias}'. Run: youtube_auth.py start --alias {alias}")
    tok = exchange_token({"grant_type": "refresh_token", "refresh_token": rec["refresh_token"]})
    if tok.get("refresh_token"):  # rotation, rare
        rec["refresh_token"] = tok["refresh_token"]
    rec["last_refresh"] = _now()
    tokens[alias] = rec
    save_tokens(tokens)
    return tok["access_token"], rec


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def store_grant(alias: str, tok: dict, flow: str) -> dict:
    if not tok.get("refresh_token"):
        raise RuntimeError("Google returned no refresh_token (need access_type=offline + prompt=consent).")
    ch = fetch_channel(tok["access_token"])
    tokens = load_tokens()
    tokens[alias] = {
        "refresh_token": tok["refresh_token"],
        "scope": tok.get("scope"),
        "flow": flow,
        "granted_at": _now(),
        **ch,
    }
    save_tokens(tokens)
    pending = _read_json(PENDING_PATH)
    pending.pop(alias, None)
    _write_private_json(PENDING_PATH, pending)
    return {"alias": alias, **ch, "scope": tok.get("scope"), "flow": flow}


# ---------- flows ----------

def start_device(alias: str) -> dict:
    cid, _ = client_creds()
    j = http_json(DEVICE_URL, data={"client_id": cid, "scope": " ".join(DEVICE_SCOPES)})
    pending = _read_json(PENDING_PATH)
    pending[alias] = {
        "flow": "device",
        "device_code": j["device_code"],
        "interval": j.get("interval", 5),
        "expires_at": time.time() + int(j.get("expires_in", 1800)),
    }
    _write_private_json(PENDING_PATH, pending)
    return {
        "flow": "device",
        "verification_url": j.get("verification_url") or j.get("verification_uri"),
        "user_code": j["user_code"],
        "expires_in_seconds": j.get("expires_in"),
        "next": f"After Nate approves: python3 youtube_auth.py poll --alias {alias} --wait",
    }


def start_manual(alias: str, redirect_uri: str) -> dict:
    cid, _ = client_creds()
    verifier = base64.urlsafe_b64encode(pysecrets.token_bytes(48)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = f"{alias}-{pysecrets.token_urlsafe(12)}"
    url = AUTH_URL + "?" + urlencode({
        "client_id": cid,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(MANUAL_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    pending = _read_json(PENDING_PATH)
    pending[alias] = {"flow": "manual", "redirect_uri": redirect_uri, "state": state,
                      "code_verifier": verifier, "created_at": time.time()}
    _write_private_json(PENDING_PATH, pending)
    return {
        "flow": "manual",
        "auth_url": url,
        "redirect_uri": redirect_uri,
        "next": ("Nate opens auth_url, picks the channel, approves, then copies the full URL of the "
                 "dead localhost page. Then: YT_CODE='<url>' python3 youtube_auth.py finish "
                 f"--alias {alias} --code-env YT_CODE"),
    }


def probe_auth_url(url: str) -> dict:
    """GET the consent URL without a session to catch invalid_client / redirect_uri_mismatch early."""
    import re

    try:
        with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
            final, body = r.url, r.read().decode(errors="replace")
    except HTTPError as e:
        final, body = url, e.read().decode(errors="replace")
    errs = sorted(set(re.findall(
        r"(invalid_client|deleted_client|disabled_client|redirect_uri_mismatch|invalid_request|"
        r"access_denied|admin_policy_enforced|org_internal|unauthorized_client)", body)))
    return {"error_page": "/signin/oauth/error" in final or bool(errs), "errors_seen": errs}


def poll_device(alias: str, wait: bool) -> dict:
    pending = _read_json(PENDING_PATH).get(alias)
    if not pending or pending.get("flow") != "device":
        raise RuntimeError(f"No pending device flow for '{alias}'. Run start first.")
    interval = int(pending.get("interval", 5))
    while True:
        if time.time() > pending["expires_at"]:
            raise RuntimeError("Device code expired. Run start again.")
        try:
            tok = exchange_token({"device_code": pending["device_code"],
                                  "grant_type": "urn:ietf:params:oauth:grant-type:device_code"})
            return store_grant(alias, tok, "device")
        except GoogleError as e:
            if e.code == "authorization_pending":
                if not wait:
                    return {"alias": alias, "pending": True, "note": "Not approved yet."}
            elif e.code == "slow_down":
                interval += 5
            else:
                raise
        log(f"waiting for approval ({alias})...")
        time.sleep(interval)


def extract_code(raw: str) -> tuple[str, str | None]:
    raw = raw.strip()
    if "code=" in raw or raw.startswith("http"):
        q = parse_qs(urlparse(raw).query) if "?" in raw else parse_qs(raw)
        if "error" in q:
            raise RuntimeError(f"Google redirected with error: {q['error'][0]}")
        code = (q.get("code") or [None])[0]
        if not code:
            raise RuntimeError("No code= found in the pasted URL.")
        return code, (q.get("state") or [None])[0]
    return raw, None


def finish_manual(alias: str, raw: str) -> dict:
    pending = _read_json(PENDING_PATH).get(alias)
    if not pending or pending.get("flow") != "manual":
        raise RuntimeError(f"No pending manual flow for '{alias}'. Run start first.")
    code, state = extract_code(raw)
    if state and state != pending["state"]:
        raise RuntimeError("State mismatch: this URL belongs to a different start (wrong alias or stale).")
    tok = exchange_token({"grant_type": "authorization_code", "code": code,
                          "redirect_uri": pending["redirect_uri"],
                          "code_verifier": pending["code_verifier"]})
    return store_grant(alias, tok, "manual")


def status() -> dict:
    out = []
    for alias, rec in sorted(load_tokens().items()):
        row = {"alias": alias, "channel_id": rec.get("channel_id"),
               "channel_title": rec.get("channel_title"), "granted_at": rec.get("granted_at")}
        try:
            at, _ = access_token_for(alias)
            ch = fetch_channel(at)
            row.update(valid=True, **ch)
        except Exception as e:  # noqa: BLE001
            row.update(valid=False, error=str(e))
        out.append(row)
    pending = {k: v.get("flow") for k, v in _read_json(PENDING_PATH).items()}
    return {"aliases": out, "pending": pending}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start", help="Begin auth for a channel alias")
    s.add_argument("--alias", required=True, choices=ALIASES)
    s.add_argument("--flow", choices=("auto", "device", "manual"), default="auto",
                   help="auto = try device flow, fall back to manual (default)")
    s.add_argument("--redirect-uri", default=DEFAULT_REDIRECT,
                   help="Redirect for manual flow (must be allowed by the client)")
    s.add_argument("--wait", action="store_true", help="Device flow: keep polling until approved")
    p = sub.add_parser("poll", help="Device flow: exchange once approved")
    p.add_argument("--alias", required=True, choices=ALIASES)
    p.add_argument("--wait", action="store_true")
    f = sub.add_parser("finish", help="Manual flow: exchange the redirected URL/code")
    f.add_argument("--alias", required=True, choices=ALIASES)
    f.add_argument("--code-env", help="Env var holding the redirected URL or code (else read stdin)")
    sub.add_parser("status", help="List aliases and check tokens by refreshing")
    args = ap.parse_args()

    try:
        if args.cmd == "start":
            result, device_error = None, None
            if args.flow in ("auto", "device"):
                try:
                    result = start_device(args.alias)
                except GoogleError as e:
                    device_error = str(e)
                    log(f"device flow rejected: {e}")
                    if args.flow == "device" or e.code == "invalid_client" and "not found" in str(e).lower():
                        emit_failure(f"Device flow failed: {e}", google_error=e.payload)
            if result is None:
                result = start_manual(args.alias, args.redirect_uri)
                result["probe"] = probe_auth_url(result["auth_url"])
                if device_error:
                    result["device_flow_error"] = device_error
                if result["probe"]["error_page"]:
                    emit_failure("Google rejected the consent URL", **result)
            if args.wait and result["flow"] == "device":
                emit({"ok": True, "alias": args.alias, **result})
                result = poll_device(args.alias, wait=True)
            emit({"ok": True, "alias": args.alias, **result})
        elif args.cmd == "poll":
            emit({"ok": True, **poll_device(args.alias, args.wait)})
        elif args.cmd == "finish":
            raw = os.environ.get(args.code_env, "") if args.code_env else sys.stdin.read()
            if not raw.strip():
                emit_failure("No code/URL provided (env var empty or stdin empty)")
            emit({"ok": True, **finish_manual(args.alias, raw)})
        elif args.cmd == "status":
            emit({"ok": True, **status()})
    except GoogleError as e:
        emit_failure(str(e), google_error=e.payload)
    except (RuntimeError, URLError, KeyError) as e:
        emit_failure(str(e))


if __name__ == "__main__":
    main()
