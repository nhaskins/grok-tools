#!/usr/bin/env python3
"""Resumable YouTube upload (Data API v3, stdlib). Prints one JSON object to stdout.

Picks the channel by --alias (main | clips) using refresh tokens saved by
youtube_auth.py in data/youtube_tokens.json. With --publish-at (RFC3339), the video
is uploaded as private with status.publishAt so YouTube publishes it at that time.
--dry-run validates inputs and auth (refreshes the token, reads the channel) and
uploads nothing.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import youtube_auth as ya  # noqa: E402

UPLOAD_HOST = "www.googleapis.com"
CHUNK = 8 * 1024 * 1024  # multiple of 256 KiB
MAX_THUMB = 2 * 1024 * 1024


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def parse_rfc3339(value: str) -> str:
    v = value.strip()
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        raise RuntimeError(f"--publish-at is not RFC3339: {value!r}") from None
    if dt.tzinfo is None:
        raise RuntimeError("--publish-at needs a timezone offset (e.g. 2026-10-13T08:00:00-05:00)")
    if dt <= datetime.now(timezone.utc):
        raise RuntimeError("--publish-at must be in the future")
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _conn(host: str = UPLOAD_HOST) -> http.client.HTTPSConnection:
    return http.client.HTTPSConnection(host, timeout=300)


def _json_or_text(raw: bytes):
    try:
        return json.loads(raw.decode() or "{}")
    except ValueError:
        return raw.decode(errors="replace")


def start_session(token: str, meta: dict, size: int, mime: str, notify: bool) -> str:
    qs = urlencode({"uploadType": "resumable", "part": "snippet,status",
                    "notifySubscribers": "true" if notify else "false"})
    body = json.dumps(meta).encode()
    c = _conn()
    c.request("POST", f"/upload/youtube/v3/videos?{qs}", body=body, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Length": str(size),
        "X-Upload-Content-Type": mime,
    })
    r = c.getresponse()
    raw = r.read()
    if r.status != 200 or not r.getheader("Location"):
        raise ya.GoogleError(r.status, _json_or_text(raw))
    return r.getheader("Location")


def upload_file(session_url: str, path: Path, size: int, mime: str) -> dict:
    u = urlparse(session_url)
    target = u.path + ("?" + u.query if u.query else "")
    offset, retries = 0, 0
    with path.open("rb") as f:
        while offset < size:
            f.seek(offset)
            chunk = f.read(CHUNK)
            end = offset + len(chunk) - 1
            try:
                c = _conn(u.netloc)
                c.request("PUT", target, body=chunk, headers={
                    "Content-Length": str(len(chunk)),
                    "Content-Type": mime,
                    "Content-Range": f"bytes {offset}-{end}/{size}",
                })
                r = c.getresponse()
                raw = r.read()
            except (OSError, http.client.HTTPException) as e:
                retries += 1
                if retries > 5:
                    raise RuntimeError(f"Upload failed after retries: {e}") from None
                log(f"chunk error ({e}); querying offset and retrying")
                offset = query_offset(u, target, size)
                continue
            if r.status in (200, 201):
                return _json_or_text(raw)
            if r.status == 308:
                rng = r.getheader("Range")
                offset = int(rng.split("-")[1]) + 1 if rng else 0
                retries = 0
                log(f"uploaded {offset}/{size} bytes ({offset * 100 // size}%)")
                continue
            if r.status >= 500 and retries < 5:
                retries += 1
                offset = query_offset(u, target, size)
                continue
            raise ya.GoogleError(r.status, _json_or_text(raw))
    raise RuntimeError("Upload ended without a final response")


def query_offset(u, target: str, size: int) -> int:
    c = _conn(u.netloc)
    c.request("PUT", target, body=b"", headers={"Content-Length": "0", "Content-Range": f"bytes */{size}"})
    r = c.getresponse()
    r.read()
    rng = r.getheader("Range")
    return int(rng.split("-")[1]) + 1 if (r.status == 308 and rng) else 0


def set_thumbnail(token: str, video_id: str, thumb: Path) -> dict:
    data = thumb.read_bytes()
    mime = "image/png" if thumb.suffix.lower() == ".png" else "image/jpeg"
    c = _conn()
    c.request("POST", f"/upload/youtube/v3/thumbnails/set?{urlencode({'videoId': video_id})}",
              body=data, headers={"Authorization": f"Bearer {token}", "Content-Type": mime,
                                  "Content-Length": str(len(data))})
    r = c.getresponse()
    raw = r.read()
    if r.status != 200:
        raise ya.GoogleError(r.status, _json_or_text(raw))
    return _json_or_text(raw)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True, help="Path to .mp4")
    ap.add_argument("--alias", required=True, choices=ya.ALIASES, help="Channel alias")
    ap.add_argument("--title", required=True, help="Max 100 chars")
    ap.add_argument("--description", default="", help="Max 5000 bytes")
    ap.add_argument("--description-file", help="Read description from a file instead")
    ap.add_argument("--tags", default="", help="Comma-separated")
    ap.add_argument("--privacy", default="private", choices=("private", "unlisted", "public"))
    ap.add_argument("--publish-at", help="RFC3339 time; forces private + scheduled publish")
    ap.add_argument("--thumbnail", help="Custom thumbnail .jpg/.png (<=2MB; channel must be verified)")
    ap.add_argument("--category", default="28", help="Category id (28 Science & Tech, 24 Entertainment)")
    ap.add_argument("--made-for-kids", choices=("true", "false"), default="false")
    ap.add_argument("--notify-subscribers", choices=("true", "false"), default="true")
    ap.add_argument("--dry-run", action="store_true", help="Validate inputs + auth; upload nothing")
    args = ap.parse_args()

    try:
        path = Path(args.file).expanduser()
        if not path.is_file():
            raise RuntimeError(f"File not found: {path}")
        size = path.stat().st_size
        if size == 0:
            raise RuntimeError("File is empty")
        mime = "video/mp4" if path.suffix.lower() == ".mp4" else "application/octet-stream"
        desc = Path(args.description_file).read_text() if args.description_file else args.description
        title = args.title.strip()
        if not title or len(title) > 100 or "<" in title or ">" in title:
            raise RuntimeError("Title must be 1-100 chars without < or >")
        if len(desc.encode()) > 5000 or "<" in desc or ">" in desc:
            raise RuntimeError("Description must be <=5000 bytes without < or >")
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        if sum(len(t) + 2 for t in tags) > 500:
            raise RuntimeError("Tags exceed ~500 characters total")
        thumb = None
        if args.thumbnail:
            thumb = Path(args.thumbnail).expanduser()
            if not thumb.is_file():
                raise RuntimeError(f"Thumbnail not found: {thumb}")
            if thumb.stat().st_size > MAX_THUMB:
                raise RuntimeError("Thumbnail exceeds 2MB")
        status = {"privacyStatus": args.privacy,
                  "selfDeclaredMadeForKids": args.made_for_kids == "true"}
        publish_at = None
        if args.publish_at:
            publish_at = parse_rfc3339(args.publish_at)
            status.update(privacyStatus="private", publishAt=publish_at)
        meta = {"snippet": {"title": title, "description": desc, "tags": tags,
                            "categoryId": str(args.category)},
                "status": status}

        token, rec = ya.access_token_for(args.alias)
        channel = ya.fetch_channel(token)
        base = {"alias": args.alias, **channel, "file": str(path), "bytes": size,
                "privacyStatus": status["privacyStatus"], "publishAt": publish_at,
                "thumbnail": str(thumb) if thumb else None}
        if args.dry_run:
            print(json.dumps({"ok": True, "dry_run": True, **base, "metadata": meta}, indent=2))
            return

        log(f"uploading {path.name} ({size} bytes) to {channel.get('channel_title')} [{args.alias}]")
        session = start_session(token, meta, size, mime, args.notify_subscribers == "true")
        video = upload_file(session, path, size, mime)
        vid = video.get("id")
        result = {"ok": True, **base, "video_id": vid,
                  "url": f"https://youtu.be/{vid}",
                  "studio_url": f"https://studio.youtube.com/video/{vid}/edit",
                  "upload_status": video.get("status", {}).get("uploadStatus")}
        if thumb and vid:
            try:
                set_thumbnail(token, vid, thumb)
                result["thumbnail_set"] = True
            except ya.GoogleError as e:  # video is up; report thumbnail failure, don't fail upload
                result.update(thumbnail_set=False, thumbnail_error=str(e))
        print(json.dumps(result, indent=2), flush=True)
    except ya.GoogleError as e:
        ya.emit_failure(str(e), google_error=e.payload)
    except (RuntimeError, OSError) as e:
        ya.emit_failure(str(e))


if __name__ == "__main__":
    main()
