#!/usr/bin/env python3
"""Shared Cursor agent runner for dig.py (adapted from dig-jobs-agent.py).

Never prints secret values.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_BIN = os.environ.get("CURSOR_AGENT_BIN", "agent")
DEFAULT_MODEL = "composer-2.5"
DEFAULT_TIMEOUT_SEC = 1200


def model_name() -> str:
    """Default model for dig; prefer DIG_* env. IMAGE_* is ignored here."""
    return (
        os.environ.get("DIG_AGENT_MODEL")
        or os.environ.get("DIG_JOBS_AGENT_MODEL")
        or DEFAULT_MODEL
    )


def timeout_sec() -> int:
    """Default timeout for dig; prefer DIG_* env. IMAGE_* is ignored here."""
    raw = (
        os.environ.get("DIG_AGENT_TIMEOUT_SEC")
        or os.environ.get("DIG_JOBS_AGENT_TIMEOUT_SEC")
        or str(DEFAULT_TIMEOUT_SEC)
    )
    return int(raw)


def image_model_name() -> str:
    """Model for generate_image (IMAGE_AGENT_MODEL, else dig default)."""
    return os.environ.get("IMAGE_AGENT_MODEL") or model_name()


def image_timeout_sec() -> int:
    """Timeout for generate_image (IMAGE_AGENT_TIMEOUT_SEC default 7200)."""
    raw = os.environ.get("IMAGE_AGENT_TIMEOUT_SEC")
    if raw is not None and str(raw).strip():
        return int(raw)
    return 7200


def load_cursor_api_key(env: dict[str, str] | None = None) -> str:
    """Resolve Cursor API key from env or local grok_secrets."""
    source = env if env is not None else os.environ
    for key in ("CURSOR_API_KEY_N8N", "CURSOR_API_KEY"):
        val = source.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()

    scripts = str(SCRIPT_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import grok_secrets  # noqa: E402

    key = grok_secrets.get("CURSOR_API_KEY_N8N", "CURSOR_API_KEY")
    if key:
        return key
    raise RuntimeError(
        "CURSOR_API_KEY_N8N/CURSOR_API_KEY missing in process.env "
        "(inject Grok Bot secret store before running)."
    )


def _is_usage_cost_key(key: str) -> bool:
    if not isinstance(key, str) or not key or not key[0].islower():
        return False
    return "cost" in key.replace("_", "").lower()


def _copy_usage_cost_fields(src: dict, usage: dict) -> None:
    for key, val in src.items():
        if _is_usage_cost_key(key):
            usage[key] = val


def usage_from_agent_result(obj: dict, model: str | None = None) -> dict:
    usage_raw = obj.get("usage") if isinstance(obj.get("usage"), dict) else {}
    usage: dict = {"model": str(obj.get("model") or model or model_name())}
    for key in (
        "inputTokens",
        "outputTokens",
        "cacheReadTokens",
        "cacheWriteTokens",
        "cacheReadInputTokens",
        "cacheCreationInputTokens",
    ):
        if key in usage_raw:
            usage[key] = usage_raw[key]
    _copy_usage_cost_fields(usage_raw, usage)
    cost_top = obj.get("cost")
    if isinstance(cost_top, dict):
        usage["cost"] = cost_top
    else:
        _copy_usage_cost_fields(obj, usage)
    if usage_raw:
        usage["raw"] = usage_raw
    if obj.get("session_id"):
        usage["sessionId"] = obj["session_id"]
    if obj.get("request_id"):
        usage["requestId"] = obj["request_id"]
    if obj.get("duration_ms") is not None:
        usage["durationMs"] = obj["duration_ms"]
    if obj.get("duration_api_ms") is not None:
        usage["durationApiMs"] = obj["duration_api_ms"]
    return usage


def parse_agent_stdout(stdout: str, model: str | None = None) -> tuple[str, dict, dict, bool]:
    """Parse Cursor CLI --output-format json stdout; fallback to raw text on failure."""
    mdl = model or model_name()
    raw = (stdout or "").strip()
    if not raw:
        return "", {"model": mdl}, {}, False

    candidates: list[dict] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            candidates.append(parsed)

    if not candidates:
        try:
            whole = json.loads(raw)
            if isinstance(whole, dict):
                candidates = [whole]
        except json.JSONDecodeError:
            return raw, {"model": mdl}, {}, False

    result_obj = next(
        (c for c in reversed(candidates) if c.get("type") == "result"),
        candidates[-1],
    )
    text = str(
        result_obj.get("result")
        or result_obj.get("text")
        or result_obj.get("message")
        or ""
    ).strip()
    usage = usage_from_agent_result(result_obj, mdl)
    meta: dict = {
        "agentParseOk": True,
        "agentSubtype": result_obj.get("subtype"),
        "agentIsError": bool(result_obj.get("is_error")),
    }
    return text, usage, meta, True


def extract_json_objects(text: str) -> list[Any]:
    found: list[Any] = []
    if not text:
        return found

    fence_re = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)
    for block in fence_re.findall(text):
        block = block.strip()
        if not block:
            continue
        try:
            found.append(json.loads(block))
        except json.JSONDecodeError:
            pass

    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch not in "{[":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
            found.append(obj)
        except json.JSONDecodeError:
            continue
    return found


def extract_items_array(
    reply: str,
    *,
    item_key: str = "items",
    alias_keys: tuple[str, ...] = ("jobs",),
) -> list[Any]:
    """Pull the items array from fenced/embedded JSON in the agent reply.

    Prefers ``item_key`` (default ``items``), then each alias (e.g. ``jobs``).
    Also accepts a bare top-level array.
    """
    text = (reply or "").strip()
    if not text:
        return []

    keys = (item_key,) + tuple(k for k in alias_keys if k != item_key)
    objects = extract_json_objects(text)
    if not objects:
        try:
            objects = [json.loads(text)]
        except json.JSONDecodeError:
            return []

    for obj in objects:
        if isinstance(obj, list):
            return list(obj)
        if isinstance(obj, dict):
            for key in keys:
                val = obj.get(key)
                if isinstance(val, list):
                    return list(val)
            # Common alternates
            for key in ("results", "data", "events"):
                val = obj.get(key)
                if isinstance(val, list):
                    return list(val)
    return []


def run_agent(
    prompt: str,
    api_key: str,
    workspace: Path,
    *,
    model: str | None = None,
    timeout: int | None = None,
    env: dict[str, str] | None = None,
    log_fn: Any = None,
) -> tuple[int, str, str]:
    """Run Cursor agent CLI; return (exit_code, stdout, stderr). Never logs secrets."""
    mdl = model or model_name()
    tsec = timeout if timeout is not None else timeout_sec()
    _log = log_fn or (lambda m: print(m, file=sys.stderr, flush=True))

    child_env = dict(env) if env is not None else dict(os.environ)
    home = str(Path.home())
    local_bin = f"{home}/.local/bin"
    path = child_env.get("PATH", "")
    if local_bin not in path.split(":"):
        child_env["PATH"] = f"{local_bin}:{path}" if path else local_bin
    child_env["CURSOR_API_KEY"] = api_key

    ws = str(workspace)
    cmd = [
        AGENT_BIN,
        "-p",
        prompt,
        "--model",
        mdl,
        "--output-format",
        "json",
        "--trust",
        "--force",
        "--workspace",
        ws,
    ]
    _log(f"Starting Cursor agent (model={mdl}, timeout={tsec}s, workspace={ws})")
    proc = subprocess.run(
        cmd,
        cwd=ws,
        env=child_env,
        capture_output=True,
        text=True,
        timeout=tsec,
    )
    if proc.stderr:
        _log(proc.stderr.rstrip())
    return proc.returncode, proc.stdout or "", proc.stderr or ""
