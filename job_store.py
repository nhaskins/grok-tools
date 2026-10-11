#!/usr/bin/env python3
"""Local job-listing ledger (SQLite) for dig.py duplicate protection.

DB path: $GROK_TOOLS_DB, else /workspace/grok-tools/data/grok-tools.db
Table:   job_listings (created with CREATE TABLE IF NOT EXISTS; nothing else touched)

Dedupe keys:
  1. url_hash          sha256(normalized URL)            -> exact duplicate (UNIQUE)
  2. company_title_key "<company_norm>|<title_norm>"     -> likely repost (indexed, not unique)

CLI:
  job_store.py stats
  job_store.py list [--status S] [--source S] [--limit N]
  job_store.py check --url URL [--company C --title T]
  job_store.py mark (--url URL | --id N | --card CARD_ID) --status S
  job_store.py seed-dig FILE [FILE ...]          # dig stdout JSON or dig review .md
  job_store.py seed-trello --list NAME --status S [--limit N] [--board IcpbhHlF]   # read-only on Trello
  job_store.py normalize URL                     # show url_norm / hash

Never prints secrets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DB = SCRIPT_DIR / "data" / "grok-tools.db"
DEFAULT_BOARD = "IcpbhHlF"  # Opportunity Engine

STATUSES = ("seen", "potential", "posted", "applied", "dead")
# Automatic upserts never move a row "backwards" (e.g. dig re-seeing a dead job).
STATUS_RANK = {"seen": 0, "potential": 1, "posted": 2, "applied": 3, "dead": 4}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS job_listings (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  url               TEXT,
  url_norm          TEXT,
  url_hash          TEXT UNIQUE,
  company           TEXT,
  title             TEXT,
  title_norm        TEXT,
  company_title_key TEXT,
  location          TEXT,
  pay               TEXT,
  posted_date       TEXT,
  source            TEXT NOT NULL DEFAULT 'dig',
  status            TEXT NOT NULL DEFAULT 'seen'
                    CHECK (status IN ('seen','potential','posted','dead','applied')),
  trello_card_id    TEXT,
  trello_card_url   TEXT,
  first_seen_at     TEXT NOT NULL,
  last_seen_at      TEXT NOT NULL,
  notes             TEXT
);
CREATE INDEX IF NOT EXISTS idx_job_listings_ctk    ON job_listings(company_title_key);
CREATE INDEX IF NOT EXISTS idx_job_listings_status ON job_listings(status);
CREATE INDEX IF NOT EXISTS idx_job_listings_card   ON job_listings(trello_card_id);
"""

# ---------------------------------------------------------------- normalization

TRACKING_PARAMS = {
    "ref", "refid", "ref_id", "referrer", "referer", "source", "src", "gh_src",
    "trk", "trkinfo", "trackingid", "tracking_id", "lever-source", "lever-origin",
    "lever-via", "fbclid", "gclid", "gclsrc", "dclid", "msclkid", "yclid", "twclid",
    "li_fat_id", "mc_cid", "mc_eid", "_hsenc", "_hsmi", "hsctatracking", "igshid",
    "si", "spm", "campaign", "campaignid", "medium", "share", "shared", "sharesource",
    "cmp", "codes", "jobsource", "source_id", "sourceid", "iis", "iisn", "from",
    "position", "pagenum", "searchid", "refreshed", "originalsubdomain", "currentjobid",
    "_ga", "_gl", "ebp", "ccuid",
}
TRACKING_PREFIXES = ("utm_", "pk_", "mtm_", "hsa_", "ga_")


def _is_tracking(key: str) -> bool:
    k = key.lower()
    return k in TRACKING_PARAMS or k.startswith(TRACKING_PREFIXES)


def normalize_url(url: str | None) -> str | None:
    """Canonical form for dedupe. Returns None for empty / non-http values."""
    if not url or not isinstance(url, str):
        return None
    raw = url.strip()
    if not raw:
        return None
    if raw.startswith("//"):
        raw = "https:" + raw
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        if re.match(r"^[\w.-]+\.[a-z]{2,}(/|$)", raw, re.I):
            raw = "https://" + raw
        else:
            return None
    parts = urlsplit(raw)
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        return None
    scheme = "https"  # http/https variants of one posting are the same listing
    host = (parts.hostname or "").lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return None
    port = parts.port
    netloc = host if port in (None, 80, 443) else f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "")
    if len(path) > 1:
        path = path.rstrip("/")
    if path == "/":
        path = ""
    query_pairs = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _is_tracking(k)
    ]
    query_pairs.sort()
    query = urlencode(query_pairs, doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))


def url_hash(url_norm: str | None) -> str | None:
    if not url_norm:
        return None
    return hashlib.sha256(url_norm.encode("utf-8")).hexdigest()


_ABBREV = {"sr": "senior", "jr": "junior", "snr": "senior", "mgr": "manager", "eng": "engineer"}
_TITLE_NOISE = re.compile(r"\s*[—–-]+\s*role tbd\s*$|\s*★.*$", re.I)


def clean_title(title: str | None) -> str:
    """Strip board decorations (— Role TBD, ★ apply) but keep the human title."""
    t = (title or "").strip()
    prev = None
    while prev != t:
        prev = t
        t = _TITLE_NOISE.sub("", t).strip()
    return t


def normalize_title(title: str | None) -> str:
    t = clean_title(title).lower()
    if not t:
        return ""
    t = re.sub(r"#\s*[a-z]*[-\d][\w-]*", " ", t)          # '#26-21440', '#R12345'
    t = re.sub(r"\b(req|requisition|job id|jr)\s*[#:]?\s*\d[\w-]*", " ", t)
    t = re.sub(r"\s[-–—]\s*\d[\d-]*\s*$", " ", t)         # trailing '- 2522'
    t = re.sub(r"\([^)]*\)", " ", t)                       # '(12345)', '(Remote US)', '(AI & Automation)'
    t = re.sub(r"[^a-z0-9]+", " ", t)
    words = [_ABBREV.get(w, w) for w in t.split()]
    return " ".join(words)


_COMPANY_SUFFIX = re.compile(
    r"\b(incorporated|inc|llc|l l c|corp|corporation|co|company|ltd|limited|plc|lp|llp|gmbh)\b"
)


def normalize_company(company: str | None) -> str:
    c = (company or "").lower().strip()
    if not c:
        return ""
    c = re.sub(r"\([^)]*\)", " ", c)                       # '(S3)', '(STL)', '(Dice)'
    c = c.replace("&", " and ")
    c = re.sub(r"[^a-z0-9]+", " ", c)
    c = _COMPANY_SUFFIX.sub(" ", c)
    return " ".join(c.split())


def company_title_key(company: str | None, title: str | None) -> str | None:
    cn, tn = normalize_company(company), normalize_title(title)
    if not cn or not tn:
        return None  # title alone is too loose to call something a repost
    return f"{cn}|{tn}"


# ---------------------------------------------------------------- store

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def db_path() -> Path:
    return Path(os.environ.get("GROK_TOOLS_DB") or DEFAULT_DB)


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    p = Path(path) if path else db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA_SQL)
    return conn


def _first(item: dict[str, Any], *keys: str) -> str | None:
    for k in keys:
        v = item.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def item_fields(item: dict[str, Any]) -> dict[str, Any]:
    """Map a dig item (any job-ish shape) to ledger columns."""
    url = _first(item, "url", "link", "href", "listingUrl", "listing_url", "applyUrl")
    company = _first(item, "company", "employer", "organization", "companyName")
    title = clean_title(_first(item, "title", "role", "position", "name"))
    un = normalize_url(url)
    return {
        "url": url if un else None,
        "url_norm": un,
        "url_hash": url_hash(un),
        "company": company,
        "title": title or None,
        "title_norm": normalize_title(title) or None,
        "company_title_key": company_title_key(company, title),
        "location": _first(item, "location", "city"),
        "pay": _first(item, "pay", "salary", "compensation"),
        "posted_date": _first(item, "postedDate", "posted_date", "posted", "datePosted"),
    }


def find_seen(conn: sqlite3.Connection, item: dict[str, Any]) -> tuple[str | None, sqlite3.Row | None]:
    """('url', row) exact dup; ('repost', row) same company+title, different URL; (None, None)."""
    f = item_fields(item)
    if f["url_hash"]:
        row = conn.execute("SELECT * FROM job_listings WHERE url_hash=?", (f["url_hash"],)).fetchone()
        if row:
            return "url", row
    if f["company_title_key"]:
        row = conn.execute(
            "SELECT * FROM job_listings WHERE company_title_key=? ORDER BY id LIMIT 1",
            (f["company_title_key"],),
        ).fetchone()
        if row:
            return "repost", row
    return None, None


def upsert(
    conn: sqlite3.Connection,
    item: dict[str, Any],
    *,
    source: str,
    status: str = "seen",
    trello_card_id: str | None = None,
    trello_card_url: str | None = None,
    notes: str | None = None,
    force_status: bool = False,
) -> tuple[str, int]:
    """Insert or refresh one listing. Returns ('inserted'|'updated', id).

    Match order: url_hash, then trello_card_id, then (URL-less items only) company_title_key.
    Existing non-null fields are kept; nulls are filled. Status only moves forward
    (seen<potential<posted<applied<dead) unless force_status=True.
    """
    if status not in STATUSES:
        raise ValueError(f"bad status {status!r}; expected one of {STATUSES}")
    f = item_fields(item)
    ts = now_iso()
    row = None
    if f["url_hash"]:
        row = conn.execute("SELECT * FROM job_listings WHERE url_hash=?", (f["url_hash"],)).fetchone()
    if row is None and trello_card_id:
        row = conn.execute(
            "SELECT * FROM job_listings WHERE trello_card_id=?", (trello_card_id,)
        ).fetchone()
    if row is None and not f["url_hash"] and f["company_title_key"]:
        row = conn.execute(
            "SELECT * FROM job_listings WHERE url_hash IS NULL AND company_title_key=?",
            (f["company_title_key"],),
        ).fetchone()

    if row is None:
        cur = conn.execute(
            """INSERT INTO job_listings (url,url_norm,url_hash,company,title,title_norm,
               company_title_key,location,pay,posted_date,source,status,trello_card_id,
               trello_card_url,first_seen_at,last_seen_at,notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (f["url"], f["url_norm"], f["url_hash"], f["company"], f["title"], f["title_norm"],
             f["company_title_key"], f["location"], f["pay"], f["posted_date"], source, status,
             trello_card_id, trello_card_url, ts, ts, notes),
        )
        conn.commit()
        return "inserted", int(cur.lastrowid)

    new_status = row["status"]
    if force_status or STATUS_RANK[status] >= STATUS_RANK.get(row["status"], 0):
        new_status = status
    updates: dict[str, Any] = {"last_seen_at": ts, "status": new_status}
    for col in ("url", "url_norm", "url_hash", "company", "title", "title_norm",
                "company_title_key", "location", "pay", "posted_date"):
        if row[col] in (None, "") and f[col]:
            updates[col] = f[col]
    if trello_card_id and row["trello_card_id"] != trello_card_id:
        if row["trello_card_id"]:
            # Same posting on a second card: keep the first card, note the other one.
            extra = f"also on card {trello_card_url or trello_card_id}"
            notes = f"{notes}; {extra}" if notes else extra
        else:
            updates["trello_card_id"] = trello_card_id
            if trello_card_url:
                updates["trello_card_url"] = trello_card_url
    if notes and notes not in (row["notes"] or ""):
        updates["notes"] = ((row["notes"] + "; ") if row["notes"] else "") + notes
    sets = ", ".join(f"{k}=?" for k in updates)
    conn.execute(f"UPDATE job_listings SET {sets} WHERE id=?", (*updates.values(), row["id"]))
    conn.commit()
    return "updated", int(row["id"])


def mark_status(
    conn: sqlite3.Connection,
    status: str,
    *,
    url: str | None = None,
    row_id: int | None = None,
    trello_card_id: str | None = None,
) -> int:
    """Force a status (manual override). Returns rows changed."""
    if status not in STATUSES:
        raise ValueError(f"bad status {status!r}")
    if url:
        h = url_hash(normalize_url(url))
        cur = conn.execute("UPDATE job_listings SET status=?, last_seen_at=? WHERE url_hash=?",
                           (status, now_iso(), h))
    elif row_id is not None:
        cur = conn.execute("UPDATE job_listings SET status=?, last_seen_at=? WHERE id=?",
                           (status, now_iso(), row_id))
    elif trello_card_id:
        cur = conn.execute("UPDATE job_listings SET status=?, last_seen_at=? WHERE trello_card_id=?",
                           (status, now_iso(), trello_card_id))
    else:
        raise ValueError("need url, row_id or trello_card_id")
    conn.commit()
    return cur.rowcount


def seen_pairs_for_prompt(conn: sqlite3.Connection, *, limit: int = 40, max_chars: int = 2000) -> list[str]:
    """Most recent 'Company — Title' strings, capped so the dig prompt stays small."""
    out: list[str] = []
    total = 0
    seen_keys: set[str] = set()
    for r in conn.execute(
        "SELECT company, title, company_title_key FROM job_listings "
        "WHERE title IS NOT NULL ORDER BY last_seen_at DESC, id DESC"
    ):
        key = r["company_title_key"] or (r["title"] or "").lower()
        if key in seen_keys:
            continue
        seen_keys.add(key)
        s = f"{r['company']} — {r['title']}" if r["company"] else str(r["title"])
        s = s[:120]
        if len(out) >= limit or total + len(s) + 2 > max_chars:
            break
        out.append(s)
        total += len(s) + 2
    return out


def filter_new(
    conn: sqlite3.Connection,
    items: list[dict[str, Any]],
    *,
    allow_reposts: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split items into (kept, dropped). Also drops in-batch duplicates.

    Exact URL matches are always dropped. Company+title matches are dropped unless
    allow_reposts, in which case they are kept and flagged with item['repostOf'].
    """
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    batch_hashes: set[str] = set()
    batch_keys: set[str] = set()
    for item in items:
        f = item_fields(item)
        info = {"title": f["title"], "company": f["company"], "url": f["url"]}
        if f["url_hash"] and f["url_hash"] in batch_hashes:
            dropped.append({**info, "reason": "duplicate-in-batch"})
            continue
        kind, row = find_seen(conn, item)
        if kind is None and f["company_title_key"] and f["company_title_key"] in batch_keys:
            kind = "repost-in-batch"
        if kind == "url":
            dropped.append({**info, "reason": "url-seen", "matchedId": row["id"],
                            "matchedStatus": row["status"], "matchedCard": row["trello_card_url"]})
            continue
        if kind in ("repost", "repost-in-batch"):
            if not allow_reposts:
                d = {**info, "reason": kind}
                if row is not None:
                    d.update(matchedId=row["id"], matchedStatus=row["status"],
                             matchedUrl=row["url"], matchedCard=row["trello_card_url"])
                dropped.append(d)
                continue
            label = "same company+title earlier in this batch"
            if row is not None:
                label = (f"#{row['id']} {row['company']} — {row['title']} "
                         f"[{row['status']}] {row['trello_card_url'] or row['url'] or ''}").strip()
            item = {**item, "repostOf": label}
        if f["url_hash"]:
            batch_hashes.add(f["url_hash"])
        if f["company_title_key"]:
            batch_keys.add(f["company_title_key"])
        kept.append(item)
    return kept, dropped


def is_job_shaped(field_names: Iterable[str], *, preset_jobs: bool = False) -> bool:
    names = {n.lower() for n in field_names}
    if preset_jobs:
        return True
    has_title = bool(names & {"title", "role", "position"})
    has_url = bool(names & {"url", "link", "listingurl", "listing_url", "applyurl"})
    jobish = bool(names & {"company", "employer", "pay", "salary", "compensation",
                           "posteddate", "posted_date", "employmenttype", "workarrangement"})
    return has_title and has_url and jobish


# ---------------------------------------------------------------- seed sources

def load_dig_items(path: Path) -> list[dict[str, Any]]:
    """Items from dig stdout JSON (last JSON line) or a dig review markdown doc."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".md", ".markdown"):
        return _parse_dig_markdown(text)
    body = None
    try:
        body = json.loads(text)
    except json.JSONDecodeError:
        for line in reversed([l for l in text.splitlines() if l.strip()]):
            try:
                body = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    if isinstance(body, dict):
        arr = body.get("items") or body.get("jobs") or []
    elif isinstance(body, list):
        arr = body
    else:
        arr = []
    return [x for x in arr if isinstance(x, dict)]


_MD_KEYMAP = {"url": "url", "pay": "pay", "company": "company", "location": "location",
              "posteddate": "postedDate", "posted": "postedDate"}


def _parse_dig_markdown(text: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    for line in text.splitlines():
        m = re.match(r"^\d+\.\s+\*\*(.+?)\*\*\s*$", line)
        if m:
            cur = {"title": m.group(1).strip()}
            items.append(cur)
            continue
        m = re.match(r"^\s+-\s+([^:]+):\s*(.*)$", line)
        if m and cur is not None:
            key = m.group(1).strip().lower().replace(" ", "")
            val = m.group(2).strip()
            lm = re.match(r"^\[([^\]]+)\]\(([^)]+)\)$", val)
            if lm:
                val = lm.group(2)
            if key in _MD_KEYMAP:
                cur[_MD_KEYMAP[key]] = val
    return items


NON_JOB_PATTERNS = [
    r"\bbrew in the lou\b", r"\bstreet food festival\b", r"\btaste of green\b",
    r"^jobs in the st\.? louis region", r"\bconnection test\b", r"\bfestival\b",
]


def non_job_reason(name: str) -> str | None:
    n = name.lower()
    for pat in NON_JOB_PATTERNS:
        if re.search(pat, n):
            if "jobs in the st" in pat:
                return "note card (search brief, not a listing)"
            if "connection test" in pat:
                return "test card"
            return "event card"
    return None


_ROLE_WORDS = re.compile(
    r"\b(engineers?|developers?|scientists?|architects?|consultants?|analysts?|managers?|directors?|"
    r"leads?|advocates?|specialists?|designers?|programmers?|administrators?|sre|devops|builders?|"
    r"representatives?|associates?|interns?|principal|staff|head of|vp|officers?|technicians?|"
    r"strategists?|forward deployed|machine learning|ai/ml|swe|educator|facilitator|founder)\b",
    re.I,
)
_SOURCE_PREFIX = re.compile(r"^(linkedin|indeed|dice|glassdoor|builtin|ziprecruiter)\s*[-:|]\s*", re.I)


def _roleish(text: str) -> bool:
    return bool(_ROLE_WORDS.search(re.sub(r"\([^)]*\)", " ", text)))


def parse_card_name(name: str) -> tuple[str | None, str]:
    """Card name -> (company, title).

    Handles 'Company — Title', 'Title — Company', 'Company - Title — Role TBD',
    'Title | Company — Role TBD', and bare titles ('Sr AI Engineer - 2522',
    'Forward Deployed Engineer - Databricks - ...'), using role words to tell which
    side is the title. Company is None when the name doesn't carry one.
    """
    n = _SOURCE_PREFIX.sub("", clean_title(name)).strip()
    if " — " in n and not _roleish(n.split(" — ", 1)[0]):
        left, right = (x.strip() for x in n.split(" — ", 1))
        return left or None, right                # 'Company — Title | East or Central US | Remote'
    if " | " in n:
        title, company = n.rsplit(" | ", 1)
        return company.strip() or None, title.strip()
    for sep, strong in ((" — ", True), (" – ", False), (" - ", False)):
        if sep not in n:
            continue
        left, right = (x.strip() for x in n.split(sep, 1))
        l_role, r_role = _roleish(left), _roleish(right)
        if not l_role and r_role:
            return left or None, right            # Company — Title
        if strong and l_role and not r_role:
            return right or None, left            # Title — Company (em dash only)
        if strong and not l_role and not r_role:
            return left or None, right
        if l_role:
            if strong:
                return left or None, right        # both role-ish: keep Company — Title convention
            return None, n                        # 'Title - qualifier' => whole thing is the title
    return None, n


_AGGREGATOR_HOSTS = (
    "dice.com", "indeed.com", "linkedin.com", "builtin.com", "nexxt.com", "lensa.com", "jobera.com",
    "snaprecruit.com", "haystackapp.io", "ihiretechnology.com", "diversityjobs.com", "usa.jobs",
    "ziprecruiter.com", "glassdoor.com", "simplyhired.com", "monster.com", "ey.jobs",
)
_ATS_HOSTS = ("greenhouse.io", "ashbyhq.com", "lever.co", "myworkdayjobs.com", "zohorecruit.com",
              "applytojob.com", "paylocity.com", "rippling.com", "smartrecruiters.com", "icims.com")


def company_from_url(url: str | None) -> str | None:
    """Best-effort employer from a posting URL (LinkedIn slug, ATS tenant, or careers.<co>.com)."""
    un = normalize_url(url)
    if not un:
        return None
    parts = urlsplit(un)
    host, path = parts.hostname or "", parts.path
    m = re.search(r"/jobs/view/[^/]*-at-([a-z0-9-]+?)-\d{6,}$", path)
    if m:
        return m.group(1).replace("-", " ").title()
    if any(host == h or host.endswith("." + h) for h in _AGGREGATOR_HOSTS):
        return None
    if host.endswith("myworkdayjobs.com"):
        return host.split(".")[0].replace("-", " ").title()
    for ats in ("greenhouse.io", "ashbyhq.com", "lever.co"):
        if host.endswith(ats):
            seg = path.strip("/").split("/")
            return seg[0].replace("-", " ").title() if seg and seg[0] else None
    if any(host.endswith(a) for a in _ATS_HOSTS):
        return None
    labels = host.split(".")
    if len(labels) >= 2:
        core = labels[-2]
        if core in ("co", "com") and len(labels) >= 3:
            core = labels[-3]
        return core.replace("-", " ").title()
    return None


def is_specific_posting(url: str | None) -> bool:
    """True when the URL looks like one job (an id in the path), not a careers index/company page."""
    un = normalize_url(url)
    if not un:
        return False
    path = urlsplit(un).path
    if re.search(r"/company/|/careers/?(list|search)?/?$|/about/?$", path, re.I) and not re.search(r"\d{4,}", path):
        return False
    return bool(re.search(r"\d{4,}|[0-9a-f]{8}-[0-9a-f]{4}-", path, re.I))


_URL_RE = re.compile(r"https?://[^\s<>\)\]\"'|]+")


def card_posting_url(card: dict[str, Any]) -> tuple[str | None, str]:
    for a in card.get("attachments") or []:
        u = a.get("url") or ""
        if not a.get("isUpload") and u.startswith("http") and "trello.com" not in u:
            return u, "attachment"
    for src, text in (("description", card.get("desc") or ""), ("name", card.get("name") or "")):
        for u in _URL_RE.findall(text):
            u = u.rstrip(".,;")
            if "trello.com" not in u:
                return u, src
    return None, "none"


def _desc_field(desc: str, *labels: str) -> str | None:
    for lab in labels:
        m = re.search(rf"^\s*{lab}\s*:\s*(.+)$", desc, re.I | re.M)
        if m:
            v = m.group(1).strip()
            if v and v.lower() not in ("unknown", "n/a"):
                return v
    return None


def trello_get(path: str, **params: Any) -> Any:
    import urllib.parse
    import urllib.request
    sys.path.insert(0, str(SCRIPT_DIR))
    import grok_secrets  # env first, then Grok Bot secret store; never printed
    key = grok_secrets.get("TRELLO_API_KEY", "TRELLO_KEY")
    tok = grok_secrets.get("TRELLO_TOKEN", "TRELLO_API_TOKEN")
    if not key or not tok:
        raise RuntimeError("TRELLO_API_KEY / TRELLO_TOKEN not available")
    q = urllib.parse.urlencode({**params, "key": key, "token": tok})
    with urllib.request.urlopen(f"https://api.trello.com/1/{path}?{q}", timeout=30) as r:
        return json.load(r)


def fetch_list_cards(board: str, list_name: str) -> list[dict[str, Any]]:
    lists = trello_get(f"boards/{board}/lists", fields="name")
    match = [l for l in lists if l["name"].strip().lower() == list_name.strip().lower()]
    if not match:
        raise RuntimeError(f"list {list_name!r} not found on board {board}")
    cards = trello_get(
        f"lists/{match[0]['id']}/cards", fields="name,desc,pos,shortUrl,idList",
        attachments="true", attachment_fields="name,url,isUpload",
    )
    return sorted(cards, key=lambda c: c.get("pos", 0))


def seed_cards(
    conn: sqlite3.Connection,
    cards: list[dict[str, Any]],
    *,
    status: str,
    source: str = "trello-seed",
) -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []
    for c in cards:
        name = c.get("name") or ""
        base = {"cardId": c.get("id"), "cardUrl": c.get("shortUrl"), "name": name}
        reason = non_job_reason(name)
        if reason:
            report.append({**base, "action": "skipped", "reason": reason})
            continue
        url, url_src = card_posting_url(c)
        company, title = parse_card_name(name)
        notes: list[str] = []
        cleaned = clean_title(name)
        if company is None and not _roleish(cleaned) and not re.search(r"[—|]| - ", cleaned):
            # Bare company name: a target-company bookmark unless it links to one specific posting.
            if not is_specific_posting(url):
                report.append({**base, "action": "skipped", "url": url,
                               "reason": "company bookmark (no specific posting)"})
                continue
            company, title = cleaned, None
            notes.append("card names company only; title unknown")
        if company is None:
            inferred = company_from_url(url)
            if inferred:
                company = inferred
                notes.append("company inferred from URL")
        if not url:
            notes.append("no posting URL on card")
        desc = c.get("desc") or ""
        item = {
            "title": title, "company": company, "url": url,
            "pay": _desc_field(desc, "Pay", "Salary", "Compensation"),
            "location": _desc_field(desc, "Location"),
            "postedDate": _desc_field(desc, "Posted", "Posted date"),
        }
        action, rid = upsert(
            conn, item, source=source, status=status, trello_card_id=c.get("id"),
            trello_card_url=c.get("shortUrl"), force_status=True,
            notes="; ".join(notes) or None,
        )
        report.append({**base, "action": action, "id": rid, "company": company, "title": title,
                       "url": url, "urlFrom": url_src})
    return report


# ---------------------------------------------------------------- CLI

def _rows(conn, sql, args=()):
    return [dict(r) for r in conn.execute(sql, args)]


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="job_store.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", help=f"SQLite path (default $GROK_TOOLS_DB or {DEFAULT_DB})")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats")
    sp = sub.add_parser("list")
    sp.add_argument("--status")
    sp.add_argument("--source")
    sp.add_argument("--limit", type=int, default=50)
    sp = sub.add_parser("check")
    sp.add_argument("--url")
    sp.add_argument("--company")
    sp.add_argument("--title")
    sp = sub.add_parser("mark")
    sp.add_argument("--url")
    sp.add_argument("--id", type=int)
    sp.add_argument("--card")
    sp.add_argument("--status", required=True, choices=STATUSES)
    sp = sub.add_parser("seed-dig")
    sp.add_argument("files", nargs="+")
    sp.add_argument("--status", default="seen", choices=STATUSES)
    sp.add_argument("--source", default="dig")
    sp = sub.add_parser("seed-trello")
    sp.add_argument("--board", default=DEFAULT_BOARD)
    sp.add_argument("--list", required=True, dest="list_name")
    sp.add_argument("--status", required=True, choices=STATUSES)
    sp.add_argument("--limit", type=int, default=None, help="first N cards in list order")
    sp.add_argument("--source", default="trello-seed")
    sp = sub.add_parser("normalize")
    sp.add_argument("url")
    a = p.parse_args(argv)

    if a.cmd == "normalize":
        un = normalize_url(a.url)
        print(json.dumps({"url": a.url, "url_norm": un, "url_hash": url_hash(un)}, indent=2))
        return

    conn = connect(a.db)
    out: Any
    if a.cmd == "stats":
        out = {
            "db": str(Path(a.db) if a.db else db_path()),
            "total": conn.execute("SELECT COUNT(*) FROM job_listings").fetchone()[0],
            "byStatus": dict(conn.execute(
                "SELECT status, COUNT(*) FROM job_listings GROUP BY status ORDER BY status").fetchall()),
            "bySource": dict(conn.execute(
                "SELECT source, COUNT(*) FROM job_listings GROUP BY source ORDER BY source").fetchall()),
            "byStatusSource": [dict(r) for r in conn.execute(
                "SELECT status, source, COUNT(*) AS n FROM job_listings GROUP BY 1,2 ORDER BY 1,2")],
            "noUrl": conn.execute("SELECT COUNT(*) FROM job_listings WHERE url IS NULL").fetchone()[0],
        }
    elif a.cmd == "list":
        where, args = [], []
        if a.status:
            where.append("status=?"); args.append(a.status)
        if a.source:
            where.append("source=?"); args.append(a.source)
        sql = ("SELECT id,status,source,company,title,url,trello_card_url,first_seen_at "
               "FROM job_listings" + (" WHERE " + " AND ".join(where) if where else "")
               + " ORDER BY id LIMIT ?")
        out = _rows(conn, sql, (*args, a.limit))
    elif a.cmd == "check":
        kind, row = find_seen(conn, {"url": a.url, "company": a.company, "title": a.title})
        out = {"match": kind, "row": dict(row) if row else None,
               "url_norm": normalize_url(a.url)}
    elif a.cmd == "mark":
        out = {"changed": mark_status(conn, a.status, url=a.url, row_id=a.id, trello_card_id=a.card)}
    elif a.cmd == "seed-dig":
        rep = []
        for fpath in a.files:
            for it in load_dig_items(Path(fpath)):
                action, rid = upsert(conn, it, source=a.source, status=a.status)
                rep.append({"file": Path(fpath).name, "action": action, "id": rid,
                            "company": it.get("company"), "title": it.get("title")})
        out = {"processed": len(rep),
               "inserted": sum(r["action"] == "inserted" for r in rep),
               "updated": sum(r["action"] == "updated" for r in rep), "rows": rep}
    elif a.cmd == "seed-trello":
        cards = fetch_list_cards(a.board, a.list_name)
        if a.limit:
            cards = cards[: a.limit]
        rep = seed_cards(conn, cards, status=a.status, source=a.source)
        out = {"list": a.list_name, "cards": len(cards),
               "inserted": sum(r["action"] == "inserted" for r in rep),
               "updated": sum(r["action"] == "updated" for r in rep),
               "skipped": sum(r["action"] == "skipped" for r in rep), "rows": rep}
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
