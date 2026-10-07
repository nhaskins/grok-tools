#!/usr/bin/env python3
"""General Cursor-CLI digger: research prompt + result schema → structured JSON.

Caller passes a research brief and the shape of array items to return.
Optional Trello card creation. See README for examples.

Stdout: one JSON object {ok, statusCode, items, doc?, trello?, usage?, error?}.
On success, also writes a short markdown review doc under /workspace/tmp/ (or --out).
Never prints secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_DIR = SCRIPT_DIR / "logs"
LOG_FILE = LOG_DIR / "dig.log"
LEGACY_LOG_FILE = LOG_DIR / "dig-jobs.log"

TRELLO_COMMENT = SCRIPT_DIR / "trello-comment.py"
EXPORT_SECRETS = SCRIPT_DIR / "export-card-secrets.py"

DEFAULT_WORKSPACE = "/workspace/grok-tools"
DEFAULT_LIST_ID = "6a67a6a08493050e627d93bb"
DEFAULT_ITEM_KEY = "items"
DEFAULT_DOC_DIR = Path("/workspace/tmp")

# Jobs preset: same semantics as dig-jobs-agent (active listings only).
JOBS_PRESET_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Role name only (no company prefix unless part of official title)",
                    },
                    "pay": {
                        "type": ["string", "null"],
                        "description": "Compensation short string, or null when unknown",
                    },
                    "url": {
                        "type": "string",
                        "description": "Direct listing URL (https). Required for each job.",
                    },
                },
                "required": ["title", "url"],
            },
        }
    },
    "required": ["items"],
}

JOBS_PRESET_EXTRA_RULES = """
- Only include jobs that are still active (open, currently accepting applications).
- Exclude closed, expired, filled, or otherwise inactive postings.
- Prefer verifying the listing page is live before including it; if unsure it is active, omit it.
- Include every distinct active job you recommend in `items`.
- `title`: role name only (no company prefix unless part of the official title).
- `pay`: known compensation as a short string, or JSON null when unknown.
- `url`: direct listing URL (https). Required for each job.
""".strip()

SECRET_KEYS = (
    "CURSOR_API_KEY",
    "CURSOR_API_KEY_N8N",
    "TRELLO_API_KEY",
    "TRELLO_KEY",
    "TRELLO_TOKEN",
    "TRELLO_API_TOKEN",
)


def log(msg: str, *, also_legacy: bool = False) -> None:
    """Append a human-readable line to dig.log (and stderr). Never log secrets."""
    ts = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    line = f"[{ts}] {msg}"
    print(line, file=sys.stderr, flush=True)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        if also_legacy:
            with LEGACY_LOG_FILE.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
    except OSError as exc:
        print(f"warning: could not write log: {exc}", file=sys.stderr, flush=True)


def emit_and_exit(payload: dict[str, Any], ok: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)
    sys.exit(0 if ok else 1)


def _env_has_any(env: dict[str, str], *keys: str) -> bool:
    for key in keys:
        val = env.get(key)
        if val is not None and str(val).strip():
            return True
    return False


def secrets_already_present(env: dict[str, str], *, need_trello: bool) -> bool:
    has_cursor = _env_has_any(env, "CURSOR_API_KEY", "CURSOR_API_KEY_N8N")
    if not has_cursor:
        return False
    if not need_trello:
        return True
    has_trello_key = _env_has_any(env, "TRELLO_API_KEY", "TRELLO_KEY")
    has_trello_token = _env_has_any(env, "TRELLO_TOKEN", "TRELLO_API_TOKEN")
    return has_trello_key and has_trello_token


def parse_export_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, _, rest = line.partition("=")
    key = key.strip()
    if not key:
        return None
    try:
        parts = shlex.split(rest, posix=True)
    except ValueError:
        return None
    if not parts:
        return key, ""
    return key, parts[0]


def load_secrets_into_env(env: dict[str, str], *, need_trello: bool) -> dict[str, str]:
    """If secrets missing, run export-card-secrets.py and merge. Never prints values."""
    out = dict(env)
    if secrets_already_present(out, need_trello=need_trello):
        log("Secrets already present in environment; skipping export-card-secrets")
        return out

    if not EXPORT_SECRETS.is_file():
        raise RuntimeError(f"export-card-secrets.py not found: {EXPORT_SECRETS}")

    log(f"Loading secrets via {EXPORT_SECRETS}")
    proc = subprocess.run(
        [sys.executable, str(EXPORT_SECRETS)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[:400]
        raise RuntimeError(
            f"export-card-secrets failed (exit {proc.returncode}): {err or 'no output'}"
        )

    injected = 0
    for line in (proc.stdout or "").splitlines():
        parsed = parse_export_line(line)
        if not parsed:
            continue
        key, value = parsed
        existing = out.get(key)
        if existing is not None and str(existing).strip():
            continue
        out[key] = value
        injected += 1

    log(f"Injected {injected} secret key(s) into child environment (values not logged)")
    return out


def parse_last_json_line(stdout: str) -> dict[str, Any]:
    raw = (stdout or "").strip()
    if not raw:
        raise RuntimeError("child produced no stdout JSON")
    for candidate in reversed([ln.strip() for ln in raw.splitlines() if ln.strip()]):
        try:
            body = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(body, dict):
            return body
    raise RuntimeError(f"stdout is not valid JSON: {raw[:500]}")


def run_json_script(
    script: Path,
    payload: dict[str, Any],
    env: dict[str, str],
    *,
    timeout: int,
    label: str,
) -> dict[str, Any]:
    if not script.is_file():
        raise RuntimeError(f"{label} script not found: {script}")

    child_env = dict(env)
    scripts_dir = str(script.parent)
    py_path = child_env.get("PYTHONPATH", "")
    parts = [p for p in py_path.split(os.pathsep) if p]
    if scripts_dir not in parts:
        child_env["PYTHONPATH"] = (
            scripts_dir if not parts else scripts_dir + os.pathsep + py_path
        )

    log(f"Running {label}: {script.name}")
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        env=child_env,
        timeout=timeout,
        cwd=str(script.parent.parent),
    )
    if proc.stderr:
        for err_line in proc.stderr.rstrip().splitlines():
            log(f"  [{label}] {err_line}")

    try:
        body = parse_last_json_line(proc.stdout or "")
    except RuntimeError:
        if proc.returncode != 0:
            hint = (proc.stderr or proc.stdout or "").strip()[:800]
            raise RuntimeError(
                hint or f"{label} failed (exit {proc.returncode})"
            ) from None
        raise

    if proc.returncode != 0 or body.get("ok") is False:
        err = body.get("error") if isinstance(body, dict) else None
        hint = str(err or "").strip() or (proc.stderr or "").strip()[:800]
        raise RuntimeError(hint or f"{label} returned ok:false (exit {proc.returncode})")

    return body


def schema_field_names(schema: Any) -> list[str]:
    """Best-effort list of item property names from a schema-ish object."""
    if schema is None:
        return []
    if isinstance(schema, list):
        # Compact field list: ["title","pay","url"] or [{"title":..}, ...]
        names: list[str] = []
        for el in schema:
            if isinstance(el, str):
                names.append(el.strip())
            elif isinstance(el, dict):
                names.extend(str(k) for k in el.keys())
                break  # example object
        return [n for n in names if n]
    if isinstance(schema, str):
        # "title,pay,url"
        return [p.strip() for p in schema.split(",") if p.strip()]
    if not isinstance(schema, dict):
        return []

    # JSON Schema: properties.items.items.properties OR properties.items.properties
    props = schema.get("properties")
    if isinstance(props, dict):
        items_prop = props.get("items") or props.get("jobs")
        if isinstance(items_prop, dict):
            inner = items_prop.get("items")
            if isinstance(inner, dict) and isinstance(inner.get("properties"), dict):
                return list(inner["properties"].keys())
            if isinstance(items_prop.get("properties"), dict):
                return list(items_prop["properties"].keys())

    # Example shape: {"items": [{"title": "", "pay": null, "url": ""}]}
    for key in ("items", "jobs"):
        arr = schema.get(key)
        if isinstance(arr, list) and arr and isinstance(arr[0], dict):
            return list(arr[0].keys())

    # Bare item object example: {"title": "", "pay": null}
    if "type" not in schema and "properties" not in schema:
        return list(schema.keys())

    # Direct items schema fragment
    if isinstance(schema.get("items"), dict):
        inner = schema["items"]
        if isinstance(inner.get("properties"), dict):
            return list(inner["properties"].keys())

    return []


def normalize_schema(raw: Any) -> Any:
    """Accept JSON Schema-ish, example shape, field list, or comma string → usable object."""
    if raw is None:
        raise RuntimeError("schema is required")
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            raise RuntimeError("schema is empty")
        # Try JSON first
        if s.startswith("{") or s.startswith("["):
            try:
                return json.loads(s)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid schema JSON: {exc}") from exc
        # Compact field list: title,pay,url
        fields = [p.strip() for p in s.split(",") if p.strip()]
        if not fields:
            raise RuntimeError("schema field list is empty")
        return {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {f: {"type": "string"} for f in fields},
                    },
                }
            },
            "required": ["items"],
        }
    if isinstance(raw, list):
        if all(isinstance(x, str) for x in raw):
            fields = [str(x).strip() for x in raw if str(x).strip()]
            return {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {f: {"type": "string"} for f in fields},
                        },
                    }
                },
                "required": ["items"],
            }
        return raw  # example array of objects
    if isinstance(raw, dict):
        return raw
    raise RuntimeError(f"Unsupported schema type: {type(raw).__name__}")


def build_agent_suffix(
    schema: Any,
    *,
    item_key: str,
    extra_rules: str = "",
) -> str:
    schema_pretty = json.dumps(schema, indent=2, ensure_ascii=False)
    rule_lines: list[str] = [
        "- Only include active/open/current items; omit if unsure.",
        "- Prefer https URLs when a url/link field is present.",
        "- Omit items you cannot verify; do not invent URLs or facts.",
        "- The JSON must be valid and parseable.",
        f'- Top-level key for the array must be "{item_key}".',
    ]
    if extra_rules.strip():
        for line in extra_rules.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if not line.startswith("-"):
                line = f"- {line}"
            if line not in rule_lines:
                rule_lines.append(line)
    rules_block = "\n".join(rule_lines)

    return f"""

After completing your research, end your reply with a fenced JSON block (```json ... ```) containing an object whose "{item_key}" array matches this schema:

{schema_pretty}

Rules:
{rules_block}
- You may include a short human summary above the JSON block; the JSON must be valid and parseable.
"""


def light_normalize_item(item: Any, field_names: list[str]) -> dict[str, Any] | None:
    """Keep dict items; optionally ensure known fields exist (null if missing)."""
    if not isinstance(item, dict):
        return None
    out = dict(item)
    # Normalize common url aliases lightly
    if "url" in field_names and not out.get("url"):
        for alt in ("link", "href", "listingUrl", "listing_url"):
            if out.get(alt):
                out["url"] = out[alt]
                break
    if "title" in field_names and not out.get("title"):
        for alt in ("name", "role", "summary", "position"):
            if out.get(alt):
                out["title"] = out[alt]
                break
    url = out.get("url")
    if isinstance(url, str) and url.strip() and not url.strip().startswith(("http://", "https://")):
        out["url"] = None
    # Presence only — fill missing schema fields with None
    for name in field_names:
        if name not in out:
            out[name] = None
    return out


def card_title(item: dict[str, Any], title_field: str) -> str:
    for key in (title_field, "title", "name", "summary"):
        val = item.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()[:256]
    return "Untitled"


def card_desc(
    item: dict[str, Any],
    *,
    title_field: str,
    template: str | None,
) -> str:
    if template:
        try:
            return template.format_map(_SafeFormat(item))
        except Exception:
            pass  # fall through to auto

    # Auto: Key: value lines for remaining fields
    lines: list[str] = []
    skip = {title_field, "title", "name"} if title_field in ("title", "name") else {title_field}
    # Prefer stable order: known-ish then rest
    preferred = ["pay", "url", "start", "end", "location", "summary", "description", "date", "when"]
    keys = [k for k in preferred if k in item and k not in skip]
    keys += [k for k in item.keys() if k not in skip and k not in keys]
    for key in keys:
        val = item.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            # Still show pay for jobs-like cards
            if key == "pay":
                lines.append("Pay: unknown")
            elif key == "url":
                lines.append("Listing: (no URL)")
            continue
        label = key.replace("_", " ").strip().capitalize()
        if key == "pay":
            lines.append(f"Pay: {val}")
        elif key == "url":
            lines.append(f"Listing: {val}")
        else:
            lines.append(f"{label}: {val}")
    return "\n".join(lines) if lines else ""


class _SafeFormat(dict):
    def __missing__(self, key: str) -> str:
        return ""



def default_doc_path() -> Path:
    """Timestamped markdown path under /workspace/tmp/."""
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    return DEFAULT_DOC_DIR / f"dig-{stamp}.md"


def _item_title(item: dict[str, Any]) -> str:
    for key in ("title", "name", "summary", "role", "position"):
        val = item.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return "Untitled"


def _is_urlish(key: str, val: Any) -> bool:
    if key.lower() in ("url", "link", "href", "listingurl", "listing_url", "website"):
        return True
    if isinstance(val, str):
        s = val.strip()
        return s.startswith("http://") or s.startswith("https://")
    return False


def _fmt_scalar(val: Any, *, max_len: int = 400) -> str:
    if val is None:
        return ""
    if isinstance(val, (dict, list)):
        try:
            s = json.dumps(val, ensure_ascii=False)
        except (TypeError, ValueError):
            s = str(val)
    else:
        s = str(val).strip()
    if len(s) > max_len:
        s = s[: max_len - 1].rstrip() + "…"
    return s


def format_items_markdown(
    items: list[dict[str, Any]],
    *,
    prompt: str = "",
    schema_src: str = "",
) -> str:
    """Lean reviewable markdown: H1 + numbered items with key fields and links."""
    n = len(items)
    lines: list[str] = [f"# Dig results ({n})", ""]
    dug = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    meta_bits = [f"Dug {dug}"]
    if schema_src:
        meta_bits.append(schema_src)
    lines.append(" · ".join(meta_bits))
    if prompt.strip():
        # One short line only — no full dump
        brief = prompt.strip().replace("\n", " ")
        if len(brief) > 160:
            brief = brief[:159].rstrip() + "…"
        lines.append(f"Prompt: {brief}")
    lines.append("")

    title_keys = {"title", "name", "summary", "role", "position"}
    # Prefer these early after the heading
    early = ("date", "start", "when", "end", "pay", "location", "venue")

    if not items:
        lines.append("_No items._")
        lines.append("")
        return "\n".join(lines)

    for idx, item in enumerate(items, start=1):
        title = _item_title(item)
        lines.append(f"{idx}. **{title}**")

        used = set()
        # Mark which title field we used so we don't repeat it
        for key in ("title", "name", "summary", "role", "position"):
            val = item.get(key)
            if val is not None and str(val).strip() == title:
                used.add(key)
                break

        # Early fields (date/start/etc.) then url, then the rest
        ordered: list[str] = []
        for key in early:
            if key in item and key not in used:
                ordered.append(key)
        # urls next
        url_keys = [
            k
            for k in item.keys()
            if k not in used
            and k not in ordered
            and _is_urlish(k, item.get(k))
        ]
        ordered.extend(url_keys)
        # remaining
        for key in item.keys():
            if key in used or key in ordered:
                continue
            ordered.append(key)

        for key in ordered:
            val = item.get(key)
            if val is None:
                continue
            if isinstance(val, str) and not val.strip():
                continue
            label = key.replace("_", " ").strip().capitalize()
            if key.lower() in ("url", "link", "href"):
                label = key.upper() if key.lower() == "url" else label
            if _is_urlish(key, val):
                href = _fmt_scalar(val, max_len=2000)
                if href.startswith(("http://", "https://")):
                    lines.append(f"   - {label}: [{href}]({href})")
                else:
                    lines.append(f"   - {label}: {href}")
            else:
                lines.append(f"   - {label}: {_fmt_scalar(val)}")

        lines.append("")

    return "\n".join(lines)


def write_items_doc(
    items: list[dict[str, Any]],
    out_path: Path,
    *,
    prompt: str = "",
    schema_src: str = "",
) -> Path:
    """Write markdown doc; create parent dirs. Returns absolute path."""
    path = out_path.expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    body = format_items_markdown(items, prompt=prompt, schema_src=schema_src)
    path.write_text(body, encoding="utf-8")
    return path


def create_trello_cards(
    items: list[dict[str, Any]],
    list_id: str,
    env: dict[str, str],
    *,
    title_field: str,
    desc_template: str | None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for idx, item in enumerate(items, start=1):
        name = card_title(item, title_field)
        desc = card_desc(item, title_field=title_field, template=desc_template)
        log(f"Creating Trello card {idx}/{len(items)}: {name[:80]}")
        body = run_json_script(
            TRELLO_COMMENT,
            {
                "mode": "card",
                "list_id": list_id,
                "name": name,
                "desc": desc,
                "content": "",
            },
            env,
            timeout=90,
            label="trello-comment",
        )
        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        results.append(
            {
                "ok": True,
                "statusCode": 200,
                "name": name,
                "cardId": data.get("cardId"),
                "cardUrl": data.get("cardUrl"),
                "shortLink": data.get("shortLink"),
                "listId": data.get("listId") or list_id,
            }
        )
    return results


def read_stdin_json() -> dict[str, Any]:
    if sys.stdin.isatty():
        raise RuntimeError(
            "Expected --prompt (and schema/--preset) or one JSON object on stdin"
        )
    raw = sys.stdin.read().strip()
    if not raw:
        raise RuntimeError("Empty stdin; provide --prompt or a JSON object")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid stdin JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("stdin JSON must be an object")
    return data


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dig.py",
        description=(
            "General digger: run Cursor agent with a research prompt and result "
            "schema; optionally create Trello cards. Standard top-level array key "
            "is `items` (jobs preset also accepts/emits `jobs` for compat)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Schema sources (first match wins): --schema-file, --schema, stdin.schema, --preset.
Presets:
  jobs   Active job listings shape: items[{title, pay, url}].
         For old dig_jobs behavior: --preset jobs --trello

Examples:
  dig.py --preset jobs --trello --prompt "Find open remote Python roles"
  dig.py --schema-file events.schema.json --trello --prompt "Food events this weekend"
  dig.py --schema '{"items":[{"summary":"","start":"","end":"","location":"","url":""}]}' \\
         --prompt "Calendar-worthy events in Austin next week"
  dig.py --preset jobs --prompt "..." --out /workspace/tmp/jobs.md
""",
    )
    p.add_argument("--prompt", help="Research brief. If omitted, read JSON from stdin.")
    p.add_argument(
        "--schema",
        help="JSON Schema-ish object, example shape, field list JSON, or comma-separated fields.",
    )
    p.add_argument(
        "--schema-file",
        dest="schema_file",
        help="Path to JSON file containing the schema.",
    )
    p.add_argument(
        "--preset",
        choices=("jobs",),
        help="Built-in schema preset (jobs = dig-jobs shape/semantics).",
    )
    p.add_argument(
        "--item-key",
        dest="item_key",
        default=None,
        help=f'Top-level array key in agent JSON (default: "{DEFAULT_ITEM_KEY}").',
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
        "--trello",
        action="store_true",
        help="Create one Trello card per item. Off by default (even with --preset jobs).",
    )
    p.add_argument(
        "--skip-trello",
        action="store_true",
        help="Do not create Trello cards (alias of omitting --trello; compat with dig_jobs).",
    )
    p.add_argument(
        "--card-title-field",
        dest="card_title_field",
        default=None,
        help='Item field used as Trello card title (default: "title", else "name").',
    )
    p.add_argument(
        "--card-desc-template",
        dest="card_desc_template",
        default=None,
        help="Optional Python format string for card desc, e.g. 'Pay: {pay}\\n{url}'.",
    )
    p.add_argument(
        "--out",
        dest="out",
        default=None,
        help=(
            "Write review markdown to this path. Default: "
            f"{DEFAULT_DOC_DIR}/dig-<YYYYMMDD-HHMMSS>.md"
        ),
    )
    return p


def resolve_schema(args: argparse.Namespace, stdin_body: dict[str, Any]) -> tuple[Any, str]:
    """Return (normalized_schema, source_label)."""
    if args.schema_file:
        path = Path(args.schema_file)
        if not path.is_file():
            raise RuntimeError(f"schema file not found: {path}")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid schema file JSON: {exc}") from exc
        return normalize_schema(raw), f"file:{path}"

    if args.schema is not None:
        return normalize_schema(args.schema), "cli:--schema"

    if stdin_body.get("schema") is not None:
        return normalize_schema(stdin_body["schema"]), "stdin:schema"

    if args.preset == "jobs":
        return JOBS_PRESET_SCHEMA, "preset:jobs"

    # stdin may use preset
    preset = str(stdin_body.get("preset") or "").strip().lower()
    if preset == "jobs":
        return JOBS_PRESET_SCHEMA, "stdin:preset:jobs"

    raise RuntimeError(
        "schema is required: pass --schema-file, --schema, stdin.schema, or --preset jobs"
    )


def main() -> None:
    # Ensure local agent_run import
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    import agent_run  # noqa: E402

    parser = build_parser()
    args = parser.parse_args()

    try:
        stdin_body: dict[str, Any] = {}
        if args.prompt is not None:
            prompt = str(args.prompt).strip()
        else:
            stdin_body = read_stdin_json()
            if isinstance(stdin_body.get("body"), dict) and not stdin_body.get("prompt"):
                stdin_body = {**stdin_body, **stdin_body["body"]}
            prompt = str(
                stdin_body.get("prompt") or stdin_body.get("message") or ""
            ).strip()
            if args.preset is None and stdin_body.get("preset"):
                args.preset = str(stdin_body["preset"]).strip().lower() or None
            if args.schema is None and stdin_body.get("schema") is None and args.schema_file is None:
                pass  # resolve_schema will check stdin schema / preset
            # Trello flags from stdin
            if stdin_body.get("trello") is True:
                args.trello = True
            if stdin_body.get("skipTrello") is True or stdin_body.get("skip_trello") is True:
                args.skip_trello = True

        if not prompt:
            raise RuntimeError("prompt is required (non-empty string)")

        schema, schema_src = resolve_schema(args, stdin_body)
        item_key = (
            args.item_key
            or stdin_body.get("item_key")
            or stdin_body.get("itemKey")
            or DEFAULT_ITEM_KEY
        )
        item_key = str(item_key).strip() or DEFAULT_ITEM_KEY

        workspace = str(
            args.workspace
            or stdin_body.get("workspacePath")
            or stdin_body.get("workspace")
            or DEFAULT_WORKSPACE
        ).strip()
        list_id = str(
            args.list_id
            or stdin_body.get("trelloListId")
            or stdin_body.get("list_id")
            or stdin_body.get("listId")
            or DEFAULT_LIST_ID
        ).strip()

        do_trello = bool(args.trello) and not bool(args.skip_trello)
        title_field = (
            args.card_title_field
            or stdin_body.get("cardTitleField")
            or stdin_body.get("card_title_field")
            or "title"
        )
        title_field = str(title_field).strip() or "title"
        desc_template = args.card_desc_template or stdin_body.get("cardDescTemplate")
        if desc_template is not None:
            desc_template = str(desc_template)

        is_jobs = args.preset == "jobs" or schema_src.endswith("jobs")
        also_legacy = is_jobs
        if also_legacy:
            log(
                "note: dig_jobs redirected through dig.py "
                "(use dig.py --preset jobs --trello for equivalent behavior)",
                also_legacy=True,
            )

        log(
            f"dig start prompt_len={len(prompt)} schema={schema_src} "
            f"item_key={item_key} workspace={workspace} trello={do_trello} "
            f"list_id={list_id if do_trello else '-'}"
        )

        env = load_secrets_into_env(dict(os.environ), need_trello=do_trello)

        extra_rules = JOBS_PRESET_EXTRA_RULES if is_jobs else ""
        # For jobs preset, agent may still emit "jobs"; we ask for items but accept both.
        agent_item_key = item_key
        agent_prompt = prompt + build_agent_suffix(
            schema, item_key=agent_item_key, extra_rules=extra_rules
        )

        ws_path = Path(workspace)
        ws_path.mkdir(parents=True, exist_ok=True)
        if not ws_path.is_dir():
            raise RuntimeError(f"workspace is not a directory: {ws_path}")

        api_key = agent_run.load_cursor_api_key(env)
        code, stdout, stderr = agent_run.run_agent(
            agent_prompt,
            api_key,
            ws_path.resolve(),
            env=env,
            log_fn=log,
        )

        reply, usage, meta, parsed = agent_run.parse_agent_stdout(stdout)
        if not parsed:
            log("Failed to parse Cursor agent JSON stdout; using raw stdout as reply")
            reply = stdout.strip() or stderr.strip()
        elif not reply:
            reply = stderr.strip()

        if code != 0 or meta.get("agentIsError"):
            detail = f"agent exited {code}" if code != 0 else "agent returned is_error"
            raise RuntimeError(f"{detail}: {(reply or '')[:500]}")

        alias = ("jobs",) if is_jobs or item_key == "items" else ()
        raw_items = agent_run.extract_items_array(
            reply, item_key=item_key, alias_keys=alias
        )
        field_names = schema_field_names(schema)
        items: list[dict[str, Any]] = []
        for raw in raw_items:
            norm = light_normalize_item(raw, field_names)
            if norm is not None:
                items.append(norm)

        log(f"Agent ok; items={len(items)}")

        trello_results: list[dict[str, Any]] = []
        if not do_trello:
            log("Skipping Trello (pass --trello to create cards)")
        elif not items:
            log("No items; skipping Trello")
        else:
            trello_results = create_trello_cards(
                items,
                list_id,
                env,
                title_field=title_field,
                desc_template=desc_template,
            )
            if len(trello_results) != len(items) or not all(
                r.get("ok") for r in trello_results
            ):
                raise RuntimeError("One or more Trello card creates failed")

        from agent_run import model_name

        # Resolve out path: --out, stdin.out / stdin.doc, or default timestamped file
        out_arg = args.out or stdin_body.get("out") or stdin_body.get("doc")
        if out_arg:
            doc_target = Path(str(out_arg).strip())
        else:
            doc_target = default_doc_path()

        doc_abs: str | None = None
        try:
            doc_path = write_items_doc(
                items,
                doc_target,
                prompt=prompt,
                schema_src=schema_src,
            )
            doc_abs = str(doc_path)
            log(f"Wrote review doc: {doc_abs}")
            print(f"DOC={doc_abs}", file=sys.stderr, flush=True)
        except OSError as exc:
            # Doc is best-effort on success path; still return items
            log(f"warning: could not write review doc: {exc}")

        payload: dict[str, Any] = {
            "ok": True,
            "statusCode": 200,
            "prompt": prompt,
            "items": items,
            "trello": trello_results,
            "usage": usage,
            "reply": reply,
            "workspace": str(ws_path.resolve()),
            "model": usage.get("model") if isinstance(usage, dict) else model_name(),
            "itemKey": item_key,
            "schemaSource": schema_src,
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if doc_abs:
            payload["doc"] = doc_abs
        # Backward compat for jobs consumers
        if is_jobs:
            payload["jobs"] = items

        log(
            f"dig success items={len(items)} trello={len(trello_results)}"
            + (f" doc={doc_abs}" if doc_abs else ""),
            also_legacy=also_legacy,
        )
        emit_and_exit(payload, ok=True)

    except subprocess.TimeoutExpired as exc:
        err = f"Timed out: {exc}"
        log(f"dig failure: {err}")
        emit_and_exit(
            {"ok": False, "statusCode": 500, "error": err, "items": [], "trello": []},
            ok=False,
        )
    except Exception as exc:
        err = str(exc).strip() or repr(exc)
        log(f"dig failure: {err[:500]}")
        fail: dict[str, Any] = {
            "ok": False,
            "statusCode": 500,
            "error": err[:800],
            "items": [],
            "trello": [],
        }
        emit_and_exit(fail, ok=False)


if __name__ == "__main__":
    main()
