#!/usr/bin/env python3
"""Upload a local file to Cloudflare R2 (S3-compatible). Prints one JSON object to stdout.

Secrets: Grok Bot secret store via grok_secrets (env override OK).
Uses AWS Signature Version 4 (stdlib only; no boto3).
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import mimetypes
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

# Allow `import grok_secrets` when invoked by absolute path
sys.path.insert(0, str(Path(__file__).resolve().parent))

DEFAULT_PUBLIC_BASE = "https://content.natehaskins.com"
DEFAULT_BUCKET = "grokbot"
R2_REGION = "auto"
SERVICE = "s3"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def emit_failure(error: str) -> None:
    print(json.dumps({"ok": False, "error": error}), flush=True)
    sys.exit(1)


def load_config(bucket_override: str | None = None) -> dict:
    import grok_secrets

    account_id = grok_secrets.get("R2_ACCOUNT_ID", "CLOUDFLARE_ACCOUNT_ID")
    access_key = grok_secrets.get("R2_ACCESS_KEY_ID", "CLOUDFLARE_R2_GROKBOT_ACCESS_KEY")
    secret_key = grok_secrets.get(
        "R2_SECRET_ACCESS_KEY", "CLOUDFLARE_R2_GROKBOT_SECRET_ACCESS_KEY"
    )
    endpoint = grok_secrets.get("R2_S3_ENDPOINT", "CLOUDFLARE_S3_API")
    public_base = (
        grok_secrets.get("R2_PUBLIC_BASE_GROKBOT", "CLOUDFLARE_R2_GROKBOT_URL")
        or DEFAULT_PUBLIC_BASE
    )
    bucket = (
        bucket_override
        or grok_secrets.get("R2_BUCKET_GROKBOT", "CLOUDFLARE_R2_GROKBOT_BUCKET")
        or DEFAULT_BUCKET
    )

    if not (account_id and access_key and secret_key):
        raise RuntimeError(
            "R2 credentials missing in Grok Bot secret store / process.env. "
            "Need R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY."
        )

    if not endpoint:
        endpoint = f"https://{account_id}.r2.cloudflarestorage.com"

    return {
        "account_id": account_id,
        "access_key": access_key,
        "secret_key": secret_key,
        "endpoint": endpoint.rstrip("/"),
        "public_base": public_base.rstrip("/"),
        "bucket": bucket,
    }


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _signing_key(secret_key: str, date_stamp: str) -> bytes:
    k_date = _hmac_sha256(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _hmac_sha256(k_date, R2_REGION)
    k_service = _hmac_sha256(k_region, SERVICE)
    return _hmac_sha256(k_service, "aws4_request")


def _aws_uri_encode(s: str, encode_slash: bool = False) -> str:
    safe = "-_.~"
    if not encode_slash:
        safe += "/"
    return quote(s, safe=safe)


def _canonical_uri(bucket: str, object_key: str) -> str:
    parts = [_aws_uri_encode(bucket, encode_slash=True)]
    if object_key:
        parts.extend(
            _aws_uri_encode(p, encode_slash=True) for p in object_key.split("/")
        )
    return "/" + "/".join(parts)


def _put_object_sigv4(
    cfg: dict,
    bucket: str,
    object_key: str,
    body: bytes,
    content_type: str | None,
) -> None:
    access_key = cfg["access_key"]
    secret_key = cfg["secret_key"]
    endpoint = cfg["endpoint"]

    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    payload_hash = _sha256_hex(body)

    canonical_uri = _canonical_uri(bucket, object_key)
    host = endpoint.replace("https://", "").replace("http://", "").split("/")[0]

    headers: dict[str, str] = {
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    if content_type:
        headers["content-type"] = content_type

    signed_header_names = sorted(headers.keys())
    canonical_headers = "".join(
        f"{k}:{headers[k].strip()}\n" for k in signed_header_names
    )
    signed_headers = ";".join(signed_header_names)

    canonical_request = "\n".join(
        [
            "PUT",
            canonical_uri,
            "",
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )

    credential_scope = f"{date_stamp}/{R2_REGION}/{SERVICE}/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            _sha256_hex(canonical_request.encode("utf-8")),
        ]
    )

    signature = hmac.new(
        _signing_key(secret_key, date_stamp),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    authorization = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    url = f"{endpoint}{canonical_uri}"
    req_headers = {
        "Authorization": authorization,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
    }
    if content_type:
        req_headers["Content-Type"] = content_type

    request = Request(url, data=body, method="PUT", headers=req_headers)
    try:
        with urlopen(request, timeout=300) as resp:
            if resp.status not in (200, 201, 204):
                raise RuntimeError(f"R2 PUT unexpected status {resp.status}")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"R2 PUT failed HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"R2 PUT request failed: {exc.reason}") from exc


def upload_file(
    local_path: Path, object_key: str, bucket: str | None = None
) -> dict:
    cfg = load_config(bucket)
    bucket_name = cfg["bucket"]
    key = object_key.lstrip("/")

    if not local_path.is_file():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    body = local_path.read_bytes()
    size = len(body)
    content_type, _ = mimetypes.guess_type(str(local_path))

    _put_object_sigv4(cfg, bucket_name, key, body, content_type)

    image_url = f"{cfg['public_base']}/{key}"
    return {
        "path": str(local_path.resolve()),
        "bucket": bucket_name,
        "key": key,
        "url": image_url,
        "imageUrl": image_url,
        "size": size,
    }


def read_stdin_request() -> dict | None:
    """Read stdin JSON when data is available; do not block forever on empty pipes."""
    if sys.stdin.isatty():
        return None
    try:
        import select

        ready, _, _ = select.select([sys.stdin], [], [], 0.05)
        if not ready:
            return None
    except (ImportError, OSError, ValueError):
        pass
    raw = sys.stdin.read().strip()
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        emit_failure(f"Invalid stdin JSON: {exc}")
    if not isinstance(data, dict):
        emit_failure("stdin JSON must be an object")
    return data



def parse_args():
    parser = argparse.ArgumentParser(
        description="Upload a local file to Cloudflare R2 (S3-compatible)."
    )
    parser.add_argument(
        "--file",
        "-f",
        default=None,
        help="Local path to upload (optional if stdin JSON provides file)",
    )
    parser.add_argument(
        "--key",
        "-k",
        default=None,
        help="Object key (optional if stdin JSON provides key)",
    )
    parser.add_argument(
        "--bucket",
        "-b",
        default=None,
        help=f"Bucket name (default: env / {DEFAULT_BUCKET})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # Only consume stdin when CLI did not already supply file+key (avoids hanging on --help / pipes)
    stdin_req = None
    if not (args.file and args.key):
        stdin_req = read_stdin_request()

    file_path = (stdin_req or {}).get("file") or args.file
    object_key = (stdin_req or {}).get("key") or args.key
    bucket = (stdin_req or {}).get("bucket") or args.bucket

    if not file_path or not object_key:
        emit_failure("Missing file and key (stdin JSON or --file/--key)")

    try:
        result = upload_file(Path(str(file_path)).expanduser(), str(object_key), bucket)
        print(json.dumps({"ok": True, "data": result}), flush=True)
    except Exception as exc:
        log(str(exc))
        emit_failure(str(exc))


if __name__ == "__main__":
    main()
