#!/usr/bin/env python3
"""Generate an image via Cursor agent, then upload to Cloudflare R2.

Replaces the n8n webhook generate-image flow. Stdout: one JSON object
{ok:true, url, path, usage, ...} or {ok:false, error}. Never prints secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_DIR = SCRIPT_DIR / "logs"
LOG_FILE = LOG_DIR / "generate-image.log"
EXPORT_SECRETS = SCRIPT_DIR / "export-card-secrets.py"

DEFAULT_WORKSPACE = "/workspace/grok-tools"
DEFAULT_ARTIFACT = "artifacts/image.png"
DEFAULT_R2_PREFIX = "images"
DEFAULT_PUBLIC_BASE = "https://content.natehaskins.com"
DEFAULT_R2_BUCKET = "grokbot"
DEFAULT_MODEL = "composer-2.5"
DEFAULT_TIMEOUT_SEC = 7200

DEFAULT_PHOTO_REFS = [
    "https://content.natehaskins.com/photo_refs/nate-1.png",
    "https://content.natehaskins.com/photo_refs/nate-2.png",
]

PREPROMPT_NORMAL = (
    "Generate the requested image and save it to the artifact path. "
    "When finished, briefly confirm the file path only."
)
PREPROMPT_REF = (
    "Generate the requested image featuring the same person shown in the "
    "attached reference photos (match likeness closely — do not invent a "
    "different person). Save to the artifact path. When finished, briefly "
    "confirm the file path only."
)

# Minimal valid 1x1 PNG for --stub dry runs
MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)

SECRET_ENV_KEYS = (
    "CURSOR_API_KEY",
    "CURSOR_API_KEY_N8N",
    "R2_ACCOUNT_ID",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "CLOUDFLARE_ACCOUNT_ID",
    "CLOUDFLARE_R2_GROKBOT_ACCESS_KEY",
    "CLOUDFLARE_R2_GROKBOT_SECRET_ACCESS_KEY",
)


def log(msg: str) -> None:
    """Append a human-readable line to generate-image.log and stderr. Never log secrets."""
    ts = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    line = f"[{ts}] {msg}"
    print(line, file=sys.stderr, flush=True)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
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


def load_secrets_into_env(env: dict[str, str], *, need_r2: bool) -> dict[str, str]:
    """If secrets missing, run export-card-secrets.py and merge. Never prints values."""
    out = dict(env)
    has_cursor = _env_has_any(out, "CURSOR_API_KEY", "CURSOR_API_KEY_N8N")
    has_r2 = _env_has_any(out, "R2_ACCESS_KEY_ID", "CLOUDFLARE_R2_GROKBOT_ACCESS_KEY")
    if has_cursor and (not need_r2 or has_r2):
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


def coerce_url_list(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return []
        if s.startswith("["):
            try:
                parsed = json.loads(s)
                return coerce_url_list(parsed) if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return [s]
        return [s]
    if not isinstance(raw, list):
        if isinstance(raw, dict) and isinstance(raw.get("url"), str):
            u = raw["url"].strip()
            return [u] if u else []
        return []
    out: list[str] = []
    for item in raw:
        if not item:
            continue
        if isinstance(item, str):
            u = item.strip()
            if u:
                out.append(u)
            continue
        if isinstance(item, dict) and isinstance(item.get("url"), str):
            u = item["url"].strip()
            if u:
                out.append(u)
    return out


def dedupe_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        key = str(u).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def resolve_mode(raw: Any, body: dict[str, Any]) -> tuple[str, bool]:
    mode_raw = str(raw if raw is not None else "normal").strip().lower()
    use_photo = (
        mode_raw in ("ref", "reference", "with_face", "face")
        or body.get("usePhotoRefs") is True
        or body.get("includeFace") is True
        or body.get("withFace") is True
    )
    return ("ref" if use_photo else "normal"), use_photo


def safe_ref_name(url: str, index: int) -> str:
    base = url.rsplit("/", 1)[-1].split("?", 1)[0]
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base) or f"ref-{index}"
    if not base.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        base = f"{base}.png"
    return f"{index:02d}-{base}"


def download_reference(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url, headers={"User-Agent": "grok-tools-generate-image/1.0"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    dest.write_bytes(data)


def download_references(urls: list[str], refs_dir: Path) -> list[Path]:
    refs_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, url in enumerate(urls):
        u = str(url).strip()
        if not u:
            continue
        dest = refs_dir / safe_ref_name(u, i)
        log(f"Downloading reference {i + 1}/{len(urls)} -> {dest}")
        try:
            download_reference(u, dest)
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise RuntimeError(f"Failed to download reference {u}: {exc}") from exc
        paths.append(dest)
    return paths


def resolve_artifact_paths(
    artifact: str, workspace: Path
) -> tuple[str, Path]:
    rel = str(artifact or DEFAULT_ARTIFACT).strip() or DEFAULT_ARTIFACT
    rel_path = Path(rel)
    if rel_path.is_absolute():
        local = rel_path
        try:
            rel_str = local.relative_to(workspace).as_posix()
        except ValueError:
            rel_str = rel
    else:
        local = workspace / rel_path
        rel_str = rel_path.as_posix()
    return rel_str, local


def build_agent_prompt(
    *,
    preprompt: str,
    subject: str,
    caller_refs: list[str],
    use_photo_refs: bool,
    ref_paths: list[Path],
    rel_artifact: str,
    local_artifact: Path,
) -> str:
    parts = [preprompt, "", "## Image request", subject]
    if caller_refs and use_photo_refs:
        parts.extend(
            [
                "",
                "## Attached images",
                "Caller-supplied URL(s) are style/scene/product references.",
                "Nate face photos are also attached — match his likeness; "
                "do not invent a different person.",
            ]
        )
    elif caller_refs:
        parts.extend(
            [
                "",
                "## Attached images",
                "Caller-supplied URL(s) are visual references "
                "(style, scene, product, or layout). Use them as directed by the request.",
            ]
        )
    elif use_photo_refs:
        parts.extend(
            [
                "",
                "## Attached images",
                "Nate face reference photos are attached — match his likeness closely.",
            ]
        )
    if ref_paths:
        parts.extend(
            [
                "",
                "## Local reference files",
                "These images were downloaded for you (use them as visual references):",
                *[f"- {p}" for p in ref_paths],
            ]
        )
    parts.extend(
        [
            "",
            "## Output",
            "Generate the image and save/copy the final PNG to:",
            f"- Project-relative: {rel_artifact}",
            f"- Absolute path: {local_artifact}",
            "",
            "When finished, briefly confirm the file path only.",
        ]
    )
    return "\n".join(p for p in parts if p is not None).strip()


def r2_object_key(prefix: str, basename: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    clean = (prefix or DEFAULT_R2_PREFIX).strip().strip("/") or DEFAULT_R2_PREFIX
    name = basename.strip() or "image.png"
    return f"{clean}/{stamp}-{name}"


def read_stdin_json_optional() -> dict[str, Any]:
    """Read stdin JSON when data is available; do not block forever on empty pipes."""
    if sys.stdin.isatty():
        return {}
    try:
        import select

        ready, _, _ = select.select([sys.stdin], [], [], 0.05)
        if not ready:
            return {}
    except (ImportError, OSError, ValueError):
        # No select: only read when caller clearly omitted --prompt (blocking OK for pipes)
        pass
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid stdin JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("stdin JSON must be an object")
    return data



def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Generate an image via Cursor agent and upload to R2. "
            "Stdout is one JSON object {ok, url, path?, usage?, error?}."
        )
    )
    p.add_argument(
        "--prompt",
        default=None,
        help="Image brief. If omitted, read JSON from stdin (prompt / message).",
    )
    p.add_argument(
        "--mode",
        default=None,
        choices=("normal", "ref", "reference", "with_face", "face"),
        help="normal (default) or ref (also attach Nate face photo refs).",
    )
    p.add_argument(
        "--artifact",
        "--out",
        dest="artifact",
        default=None,
        help=f"Artifact path relative to workspace (default: {DEFAULT_ARTIFACT}).",
    )
    p.add_argument(
        "--r2-prefix",
        dest="r2_prefix",
        default=None,
        help=f"R2 key prefix / folder (default: {DEFAULT_R2_PREFIX}).",
    )
    p.add_argument(
        "--ref-url",
        dest="ref_urls",
        action="append",
        default=None,
        help="Caller reference image URL (repeatable).",
    )
    p.add_argument(
        "--photo-ref-url",
        dest="photo_ref_urls",
        action="append",
        default=None,
        help="Nate photo ref URL override (repeatable; defaults when mode=ref).",
    )
    p.add_argument(
        "--preprompt",
        default=None,
        help="Override mode preprompt (empty uses prepromptNormal / prepromptRef).",
    )
    p.add_argument(
        "--skip-r2",
        "--no-upload",
        dest="skip_r2",
        action="store_true",
        help="Stop after local file; ok:true with path, url null.",
    )
    p.add_argument(
        "--workspace",
        default=None,
        help=f"Agent workspace (default: IMAGE_AGENT_WORKSPACE or {DEFAULT_WORKSPACE}).",
    )
    p.add_argument(
        "--stub",
        action="store_true",
        help="Dry run: write a tiny placeholder PNG, skip Cursor agent.",
    )
    return p


def collect_caller_refs(args: argparse.Namespace, body: dict[str, Any]) -> list[str]:
    """Match workflow Build node + Set mapping for caller style/scene refs."""
    urls: list[str] = []
    if args.ref_urls:
        urls.extend(args.ref_urls)
    for key in (
        "callerReferenceUrls",
        "referenceImages",
        "images",
        "referenceUrl",
        "refUrl",
        "refUrls",
    ):
        urls.extend(coerce_url_list(body.get(key)))
    # Set node: callerReferenceUrls = body.callerReferenceUrls || body.referenceUrls
    # When callerReferenceUrls absent, fold referenceUrls into caller refs
    # (photo legacy path only applies when photoReferenceUrls was also omitted AND
    # mode=ref — handled in collect_photo_refs; avoid double-counting here when
    # photoReferenceUrls is unset and mode will treat referenceUrls as photos).
    if (
        body.get("callerReferenceUrls") is None
        and body.get("referenceUrls") is not None
        and body.get("photoReferenceUrls") is not None
    ):
        urls.extend(coerce_url_list(body.get("referenceUrls")))
    elif (
        body.get("callerReferenceUrls") is None
        and body.get("referenceUrls") is not None
        and body.get("photoReferenceUrls") is None
    ):
        # Webhook Set always injects photoReferenceUrls; without that field on
        # raw stdin, treat referenceUrls as caller refs for normal mode only.
        # For mode=ref with omitted photoReferenceUrls, Build uses referenceUrls
        # as photo refs — so skip here when mode looks like ref.
        mode_raw = str(body.get("mode") or "normal").strip().lower()
        if mode_raw not in ("ref", "reference", "with_face", "face"):
            urls.extend(coerce_url_list(body.get("referenceUrls")))
    return dedupe_urls(urls)


def collect_photo_refs(
    args: argparse.Namespace, body: dict[str, Any], use_photo: bool
) -> list[str]:
    if not use_photo:
        return []
    if args.photo_ref_urls:
        return dedupe_urls(list(args.photo_ref_urls))
    photo = coerce_url_list(body.get("photoReferenceUrls"))
    if photo:
        return dedupe_urls(photo)
    # Legacy: if photoReferenceUrls omitted, referenceUrls are Nate photo refs
    if "photoReferenceUrls" not in body and body.get("referenceUrls") is not None:
        legacy = coerce_url_list(body.get("referenceUrls"))
        if legacy:
            return dedupe_urls(legacy)
    return list(DEFAULT_PHOTO_REFS)


def main() -> None:
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    import agent_run  # noqa: E402
    import upload_r2  # noqa: E402

    image_model = agent_run.image_model_name
    image_timeout_sec = agent_run.image_timeout_sec

    parser = build_parser()
    args = parser.parse_args()

    try:
        # dig-style: --prompt uses CLI flags only; otherwise read one JSON object from stdin
        stdin_body: dict[str, Any] = {}
        if args.prompt is not None:
            prompt_subject = str(args.prompt).strip()
        else:
            stdin_body = read_stdin_json_optional()
            if isinstance(stdin_body.get("body"), dict) and not (
                stdin_body.get("prompt") or stdin_body.get("message")
            ):
                stdin_body = {**stdin_body, **stdin_body["body"]}
            prompt_subject = str(
                stdin_body.get("prompt")
                or stdin_body.get("message")
                or stdin_body.get("text")
                or stdin_body.get("subject")
                or ""
            ).strip()

        if not prompt_subject:
            raise RuntimeError(
                "Missing prompt. Pass --prompt or stdin JSON with prompt/message."
            )

        mode, use_photo = resolve_mode(
            args.mode if args.mode is not None else stdin_body.get("mode"),
            stdin_body,
        )

        workspace = Path(
            str(
                args.workspace
                or stdin_body.get("workspacePath")
                or stdin_body.get("workspace")
                or os.environ.get("IMAGE_AGENT_WORKSPACE")
                or DEFAULT_WORKSPACE
            ).strip()
        )
        workspace.mkdir(parents=True, exist_ok=True)

        artifact_raw = (
            args.artifact
            or stdin_body.get("artifactPath")
            or stdin_body.get("artifact")
            or DEFAULT_ARTIFACT
        )
        rel_artifact, local_artifact = resolve_artifact_paths(
            str(artifact_raw), workspace
        )

        r2_prefix = str(
            args.r2_prefix
            or stdin_body.get("r2KeyPrefix")
            or stdin_body.get("r2_prefix")
            or DEFAULT_R2_PREFIX
        ).strip() or DEFAULT_R2_PREFIX

        skip_r2 = bool(args.skip_r2) or bool(
            stdin_body.get("skipR2") or stdin_body.get("skip_r2") or stdin_body.get("noUpload")
        )
        stub = bool(args.stub) or bool(stdin_body.get("stub"))

        set_preprompt = str(
            args.preprompt
            if args.preprompt is not None
            else (stdin_body.get("preprompt") or "")
        ).strip()
        if set_preprompt:
            preprompt = set_preprompt
        elif use_photo:
            preprompt = str(
                stdin_body.get("prepromptRef") or PREPROMPT_REF
            ).strip()
        else:
            preprompt = str(
                stdin_body.get("prepromptNormal") or PREPROMPT_NORMAL
            ).strip()

        caller_refs = collect_caller_refs(args, stdin_body)
        photo_refs = collect_photo_refs(args, stdin_body, use_photo)
        reference_images = list(caller_refs)
        if use_photo:
            reference_images = dedupe_urls([*caller_refs, *photo_refs])
            if not reference_images:
                raise RuntimeError(
                    "mode=ref requires photo ref URLs "
                    "(--photo-ref-url / photoReferenceUrls or defaults)"
                )

        log(
            f"generate_image start mode={mode} prompt_len={len(prompt_subject)} "
            f"refs={len(reference_images)} artifact={rel_artifact} "
            f"workspace={workspace} skip_r2={skip_r2} stub={stub}"
        )

        local_artifact.parent.mkdir(parents=True, exist_ok=True)
        refs_dir = workspace / "artifacts" / "refs"

        usage: dict[str, Any] = {"model": image_model()}
        meta: dict[str, Any] = {}
        reply = ""

        if stub:
            local_artifact.write_bytes(MINIMAL_PNG)
            reply = "stub"
            meta = {"stub": True}
            log(f"Stub wrote placeholder PNG: {local_artifact}")
        else:
            env = load_secrets_into_env(dict(os.environ), need_r2=not skip_r2)
            # Apply env for child / grok_secrets reads
            for k, v in env.items():
                if k not in os.environ or not str(os.environ.get(k) or "").strip():
                    os.environ[k] = v

            ref_paths = (
                download_references(reference_images, refs_dir)
                if reference_images
                else []
            )
            agent_prompt = build_agent_prompt(
                preprompt=preprompt,
                subject=prompt_subject,
                caller_refs=caller_refs,
                use_photo_refs=use_photo,
                ref_paths=ref_paths,
                rel_artifact=rel_artifact,
                local_artifact=local_artifact,
            )

            api_key = agent_run.load_cursor_api_key(env)
            model = image_model()
            timeout = image_timeout_sec()
            code, stdout, stderr = agent_run.run_agent(
                agent_prompt,
                api_key,
                workspace.resolve(),
                model=model,
                timeout=timeout,
                env=env,
                log_fn=log,
            )
            reply, usage, meta, parsed = agent_run.parse_agent_stdout(stdout, model)
            if not parsed:
                log("Failed to parse Cursor agent JSON stdout; using raw stdout as text")
                meta = {"agentParseOk": False}
                reply = stdout.strip() or stderr.strip()
            elif not reply:
                reply = stderr.strip()

            if code != 0 or meta.get("agentIsError"):
                detail = (
                    f"agent exited {code}" if code != 0 else "agent returned is_error"
                )
                raise RuntimeError(f"{detail}: {(reply or '')[:500]}")

            if not local_artifact.is_file():
                raise RuntimeError(f"expected artifact missing: {local_artifact}")

        if not local_artifact.is_file():
            raise RuntimeError(f"expected artifact missing: {local_artifact}")

        image_url: str | None = None
        r2_key: str | None = None
        if skip_r2:
            log("Skipping R2 upload (--skip-r2 / --no-upload)")
        else:
            env = load_secrets_into_env(dict(os.environ), need_r2=True)
            for k, v in env.items():
                if k not in os.environ or not str(os.environ.get(k) or "").strip():
                    os.environ[k] = v
            basename = Path(rel_artifact).name or "image.png"
            r2_key = r2_object_key(r2_prefix, basename)
            log(f"Uploading to R2 key={r2_key}")
            result = upload_r2.upload_file(
                local_artifact, r2_key, DEFAULT_R2_BUCKET
            )
            image_url = result.get("url") or result.get("imageUrl")
            if not image_url:
                raise RuntimeError("R2 upload finished but no image URL was resolved")
            log(f"Uploaded: {image_url}")

        payload: dict[str, Any] = {
            "ok": True,
            "url": image_url,
            "path": str(local_artifact.resolve()),
            "artifactPath": rel_artifact,
            "localArtifactPath": str(local_artifact.resolve()),
            "mode": mode,
            "r2KeyPrefix": r2_prefix,
            "r2ObjectKey": r2_key,
            "usage": usage,
            "meta": meta,
            "reply": reply or None,
            "referenceImageCount": len(reference_images),
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        # Compat aliases matching old n8n finalize shape
        if image_url:
            payload["imageUrl"] = image_url

        log(
            f"generate_image success url={image_url or 'null'} path={local_artifact}"
        )
        emit_and_exit(payload, ok=True)

    except subprocess.TimeoutExpired as exc:
        err = f"Timed out: {exc}"
        log(f"generate_image failure: {err}")
        emit_and_exit({"ok": False, "error": err, "url": None}, ok=False)
    except Exception as exc:
        err = str(exc).strip() or repr(exc)
        log(f"generate_image failure: {err[:500]}")
        emit_and_exit(
            {"ok": False, "error": err[:800], "url": None},
            ok=False,
        )


if __name__ == "__main__":
    main()
