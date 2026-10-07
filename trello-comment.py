#!/usr/bin/env python3
"""Trello helpers (stdin JSON → stdout JSON).

Preferred stdin contract (one JSON object):

- **comment** (``mode``: ``comment``):
  ``{ "mode": "comment", "content", "card_id" | "cardId" }`` — post a comment on a card.

- **card** (``mode``: ``card``; aliases ``create-card``):
  ``{ "mode": "card", "list_id" | "listId" | "trelloListId",
  "name" | "title" (or first line of ``content``), optional ``desc`` | ``description`` or ``content`` }``
  — description is ``desc`` / ``description`` / ``content`` (not forced equal to name).

Legacy shapes still supported: ``{ "cardId", "text" }``, ``action``: ``create-card``, etc.

Stdout: ``{"ok": true, "data": {...}}`` or ``{"ok": false, "error": "..."}`` (stderr = logs).
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

TRELLO_COMMENT_URL = "https://api.trello.com/1/cards/{card_id}/actions/comments"
TRELLO_CARDS_URL = "https://api.trello.com/1/cards"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def emit_failure(error: str, exit_code: int = 1) -> None:
    print(json.dumps({"ok": False, "error": error}), flush=True)
    sys.exit(exit_code)


def load_credentials() -> tuple[str, str]:
    import grok_secrets

    api_key = grok_secrets.get("TRELLO_API_KEY", "TRELLO_KEY")
    token = grok_secrets.get("TRELLO_TOKEN", "TRELLO_API_TOKEN")
    if not api_key or not token:
        raise RuntimeError(
            "Trello credentials incomplete. Set TRELLO_API_KEY and TRELLO_TOKEN "
            "in Grok Bot's secret store."
        )
    return api_key, token


def read_stdin_request() -> dict:
    if sys.stdin.isatty():
        emit_failure("Expected one JSON request object on stdin")
    raw = sys.stdin.read().strip()
    if not raw:
        emit_failure("Empty stdin")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        emit_failure(f"Invalid stdin JSON: {exc}")
    if not isinstance(data, dict):
        emit_failure("stdin JSON must be an object")
    return data


def resolve_content(req: dict) -> str:
    for key in ("content", "text", "comment", "message"):
        val = req.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def resolve_text(req: dict) -> str:
    return resolve_content(req)


def resolve_card_id(req: dict) -> str:
    for key in ("card_id", "cardId"):
        val = req.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def resolve_list_id(req: dict) -> str:
    for key in ("list_id", "listId", "trelloListId"):
        val = req.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def resolve_desc(req: dict) -> str:
    for key in ("desc", "description"):
        val = req.get(key)
        if val is not None and str(val).strip():
            return str(val)
    return ""


def resolve_card_desc(req: dict) -> str:
    explicit = resolve_desc(req)
    if explicit:
        return explicit
    return resolve_content(req)


def resolve_comment_body(req: dict) -> str:
    for key in ("content", "message", "text", "desc", "description"):
        val = req.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def resolve_name(req: dict, content: str) -> str:
    for key in ("name", "title"):
        val = req.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    first_line = content.split("\n", 1)[0].strip() if content else ""
    if len(first_line) > 100:
        return first_line[:97] + "..."
    return first_line


def normalize_mode(req: dict) -> str:
    raw = str(req.get("mode") or "").strip().lower()
    aliases = {"create-card": "card", "create_card": "card"}
    if raw in aliases:
        raw = aliases[raw]
    if raw in ("comment", "card"):
        return raw

    explicit = str(req.get("action") or "").strip().lower()
    if explicit == "comment":
        return "comment"
    if explicit in ("create-card", "card"):
        return "card"

    card_id = resolve_card_id(req)
    list_id = resolve_list_id(req)
    name = str(req.get("name") or req.get("title") or "").strip()
    content = resolve_content(req)
    if card_id:
        return "comment"
    if list_id and (name or content):
        return "card"
    if explicit:
        raise RuntimeError(f"Unknown action: {explicit}")
    if list_id:
        raise RuntimeError("Missing content or name for card mode")
    raise RuntimeError(
        "Missing mode and could not infer: need comment+card_id or card+list_id+content"
    )


def trello_post_form(path: str, form: dict) -> tuple[int, dict]:
    api_key, token = load_credentials()
    query = urllib.parse.urlencode({"key": api_key, "token": token})
    url = f"{path}?{query}"
    body = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = response.getcode()
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        log(f"Trello HTTP {exc.code}: {detail[:500]}")
        raise RuntimeError(f"Trello API error (HTTP {exc.code})") from exc
    except urllib.error.URLError as exc:
        log(str(exc.reason))
        raise RuntimeError(f"Trello request failed: {exc.reason}") from exc
    return status, payload


def post_comment(card_id: str, text: str) -> dict:
    path = TRELLO_COMMENT_URL.format(
        card_id=urllib.parse.quote(card_id, safe="")
    )
    status, payload = trello_post_form(path, {"text": text})

    comment_id = payload.get("id")
    if not comment_id:
        raise RuntimeError("Trello response missing comment id")

    result = {
        "action": "comment",
        "cardId": card_id,
        "commentId": str(comment_id),
        "text": text,
        "status": status,
    }
    short_link = (payload.get("data") or {}).get("card", {}).get("shortLink")
    if short_link:
        result["shortLink"] = short_link
        result["cardUrl"] = f"https://trello.com/c/{short_link}"
    return result


def create_card(list_id: str, name: str, desc: str) -> dict:
    form: dict[str, str] = {"idList": list_id, "name": name}
    if desc:
        form["desc"] = desc
    status, payload = trello_post_form(TRELLO_CARDS_URL, form)

    card_id = payload.get("id")
    if not card_id:
        raise RuntimeError("Trello response missing card id")

    result = {
        "action": "create-card",
        "cardId": str(card_id),
        "listId": list_id,
        "name": name,
        "status": status,
    }
    if desc:
        result["desc"] = desc
    short_link = payload.get("shortLink")
    if short_link:
        result["shortLink"] = str(short_link)
        result["cardUrl"] = f"https://trello.com/c/{short_link}"
    return result


def dispatch(req: dict) -> dict:
    mode = normalize_mode(req)
    if mode == "comment":
        card_id = resolve_card_id(req)
        if not card_id:
            raise RuntimeError("Missing card_id (or cardId)")
        text = resolve_comment_body(req)
        if not text:
            raise RuntimeError(
                "Missing content (or text, message, desc, description)"
            )
        return post_comment(card_id, text)

    list_id = resolve_list_id(req)
    if not list_id:
        raise RuntimeError("Missing list_id (or listId, trelloListId)")
    content = resolve_content(req)
    name = resolve_name(req, content)
    if not name:
        raise RuntimeError("Missing name/title or content for card mode")
    desc = resolve_card_desc(req)
    return create_card(list_id, name, desc)


def main() -> None:
    req = read_stdin_request()
    try:
        data = dispatch(req)
        print(json.dumps({"ok": True, "data": data}), flush=True)
    except Exception as exc:
        log(str(exc))
        emit_failure(str(exc))


if __name__ == "__main__":
    main()
