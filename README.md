# grok-tools

Python scripts Grok Bot writes and runs. Logs go in `logs/` (not committed). Secrets come from env, never files.

## dig.py

General Cursor-CLI digger: pass a **research prompt** and the **shape of results** to return. Different tasks use different schemas (job cards, calendar events, food events, …).

Stdout is one JSON object: `{ok, statusCode, items, doc?, trello?, usage?, error?}`. Progress logs go to `logs/dig.log` and stderr. Secrets are never printed.

### Review markdown doc

On success, dig writes a short reviewable markdown file of the returned items (title/key fields + links — no full agent reply dump):

- Default path: `/workspace/tmp/dig-<YYYYMMDD-HHMMSS>.md` (directory created if needed)
- Override with `--out path.md` (or stdin JSON `out` / `doc`)
- Absolute path is in the stdout JSON field **`doc`**, and logged to stderr / `logs/dig.log` as `DOC=...`
- On failure, no doc is required (skipped)

### How schema is passed (first match wins)

1. `--schema-file path.json` — JSON Schema-ish object, or an example `{ "items": [ {...} ] }` shape
2. `--schema '...'` — same, as a JSON string; also accepts compact field lists (`title,pay,url` or `["title","pay","url"]`)
3. stdin JSON field `schema`
4. `--preset jobs` — built-in active job listings shape: `items[{title, pay, url}]` (same semantics as the old dig-jobs-agent)

Top-level array key defaults to **`items`**. Use `--item-key` to change it. The jobs preset also accepts agent output under `jobs` and includes a `jobs` alias in the success payload for backward compatibility.

### Trello

- `--trello` creates one card per item (off by default).
- `--preset jobs` does **not** auto-enable Trello; for old dig_jobs behavior pass **`--preset jobs --trello`**.
- `--skip-trello` is an alias of omitting `--trello` (compat).
- `--list-id`, `--card-title-field` (default `title` / `name`), `--card-desc-template` (optional; otherwise auto `Key: value` lines).

### Examples

**Jobs + Trello** (old Dig jobs workflow):

```bash
python3 /workspace/grok-tools/dig.py \
  --preset jobs --trello \
  --prompt "Find open remote Python roles for Nate Haskins"
```

**Events → Trello** (custom schema file):

```bash
# events.schema.json example:
# {"items":[{"title":"","date":"","venue":"","url":"","notes":""}]}
python3 /workspace/grok-tools/dig.py \
  --schema-file /path/to/events.schema.json \
  --trello --list-id 6a67a6a08493050e627d93bb \
  --card-title-field title \
  --prompt "Find food festivals and pop-up dinners in Austin this weekend"
```

**Calendar-shaped results (no Trello):**

```bash
python3 /workspace/grok-tools/dig.py \
  --schema '{"items":[{"summary":"","start":"","end":"","location":"","url":""}]}' \
  --prompt "Public events in Chicago next week worth putting on a calendar"
```

**Custom review doc path:**

```bash
python3 /workspace/grok-tools/dig.py \
  --preset jobs --prompt "Find open remote Python roles" \
  --out /workspace/tmp/jobs.md
```

**Stdin JSON** (when `--prompt` is omitted):

```bash
echo '{"prompt":"Find open jobs","preset":"jobs","trello":true,"workspacePath":"/workspace/grok-tools"}' \
  | python3 /workspace/grok-tools/dig.py
```

### Env

| Variable | Default | Meaning |
|----------|---------|---------|
| `DIG_AGENT_MODEL` | `composer-2.5` | Cursor agent model (`DIG_JOBS_AGENT_MODEL` also accepted) |
| `DIG_AGENT_TIMEOUT_SEC` | `1200` | Agent timeout (`DIG_JOBS_AGENT_TIMEOUT_SEC` also accepted) |
| `CURSOR_AGENT_BIN` | `agent` | Cursor CLI binary |

Needs `agent` on PATH plus Cursor (and Trello if `--trello`) secrets in env, or the box secret store via `/workspace/grok-tools/export-card-secrets.py`.

Shared agent helpers live in `agent_run.py`.

### Duplicate protection (job ledger)

Job-shaped results (`--preset jobs`, or any schema with title + url + a job field like company/pay/postedDate) are checked against a local SQLite ledger before they're returned or posted to Trello. Non-job schemas (events, calendar) are untouched.

- DB: `/workspace/grok-tools/data/grok-tools.db` (override with `GROK_TOOLS_DB`), table `job_listings`. Module + CLI: `job_store.py`.
- Exact duplicate = same `url_hash` (sha256 of the normalized URL: lowercase scheme/host, no `www.`, no fragment, tracking params like `utm_*`, `ref`, `source`, `gh_src`, `trk`, `gclid`, `fbclid` removed, other params sorted, no trailing slash). Always dropped.
- Likely repost = same `company_title_key` (normalized company without inc/llc/corp/parentheticals + normalized title without req numbers like `#26-21440` / `- 2522`). Dropped by default; `--allow-reposts` keeps them, flagged with `repostOf`.
- In-batch duplicates are dropped too. Up to 40 recent `Company — Title` pairs (≤2,000 chars) are added to the agent prompt so it looks for new openings.
- Kept items are recorded as `seen`, or `potential` + card id/url when `--trello` creates a card. Automatic writes never downgrade a status (a `dead` job stays dead).
- Stdout gains `dedupe: {db, received, kept, dropped[], flaggedReposts, recorded}`.
- `--no-dedupe` bypasses all of it. `--items-file FILE` replays a saved dig output (JSON or review .md) instead of running the agent, for testing.

```bash
# Deduped job dig (review only)
python3 /workspace/grok-tools/dig.py --schema-file /workspace/tmp/stl-ai-jobs.schema.json \
  --prompt "$(cat /workspace/tmp/stl-ai-jobs.prompt.txt)"
# ...and post survivors to Potential
python3 /workspace/grok-tools/dig.py --preset jobs --trello --prompt "..."

# Ledger CLI
python3 /workspace/grok-tools/job_store.py stats
python3 /workspace/grok-tools/job_store.py list --status potential
python3 /workspace/grok-tools/job_store.py check --url "https://...?..utm_source=x"
python3 /workspace/grok-tools/job_store.py mark --card <trelloCardId> --status applied
python3 /workspace/grok-tools/job_store.py seed-dig /workspace/tmp/dig-*.out /workspace/tmp/dig-*.md
python3 /workspace/grok-tools/job_store.py seed-trello --list Dead --status dead --limit 10   # read-only on Trello

# Tests (temp copy of the ledger; no agent, no Trello)
python3 -m unittest /workspace/grok-tools/tests/test_job_store.py -v
```

## dig_jobs.py (compat wrapper)

Thin wrapper that calls `dig.py --preset jobs --trello` (or `--skip-trello`). Prefer `dig.py` for new use.

```bash
python3 /workspace/grok-tools/dig_jobs.py --prompt "Find open remote Python roles for Nate Haskins"
python3 /workspace/grok-tools/dig_jobs.py --prompt "..." --skip-trello
```

## generate_image.py

Replaces the n8n `generate-image` webhook: build a Cursor agent prompt (optional Nate face refs), generate a PNG, upload to Cloudflare R2, print one JSON object.

Stdout success: `{ok:true, url, path, localArtifactPath, attach:true, attachPath, doc?, usage, ...}`.  
Failure: `{ok:false, error:"..."}`. Logs go to `logs/generate-image.log` and stderr. Secrets are never printed.

### Attach + review doc

On success the script always signals the chat host to show the PNG:

- **`attach`**: always `true`
- **`attachPath`** / **`path`** / **`localArtifactPath`**: absolute path to the local PNG (Grok Bot should `SendToUser` with this file — do not only paste the CDN URL)
- **`doc`**: absolute path to a tiny sidecar markdown under `/workspace/tmp/generate-image-<YYYYMMDD-HHMMSS>.md` (image embedded via CDN URL when uploaded, else the local path)
- Logged as `DOC=...` and `ATTACH=...` on stderr / `logs/generate-image.log`

### Modes

- `normal` (default) — text-only, or caller-supplied style/scene refs
- `ref` — also attach Nate face photo refs from CDN (can combine with caller refs)

### Examples

**Normal (upload to R2):**

```bash
python3 /workspace/grok-tools/generate_image.py \
  --prompt "A large bucket overflowing with shiny arcade game tokens" \
  --artifact artifacts/arcade-token-bucket.png \
  --r2-prefix images
```

**With face refs (`mode=ref`):**

```bash
python3 /workspace/grok-tools/generate_image.py \
  --mode ref \
  --prompt "Bold 16:9 thumbnail: subject holding a glowing token jar" \
  --artifact artifacts/image-with-refs.png
```

**Caller style refs + local only (no R2):**

```bash
python3 /workspace/grok-tools/generate_image.py \
  --prompt "Match this product style" \
  --ref-url "https://example.com/style-reference.png" \
  --skip-r2
```

**Stdin JSON** (old webhook body shape):

```bash
echo '{
  "prompt": "<Image brief>",
  "mode": "ref",
  "artifactPath": "artifacts/image-with-refs.png",
  "r2KeyPrefix": "images",
  "callerReferenceUrls": "[\"https://example.com/style-reference.png\"]"
}' | python3 /workspace/grok-tools/generate_image.py
```

**Stub dry run** (no Cursor agent):

```bash
python3 /workspace/grok-tools/generate_image.py --stub --prompt 'test' --skip-r2
```

### Env

| Variable | Default | Meaning |
|----------|---------|---------|
| `IMAGE_AGENT_MODEL` | `composer-2.5` | Cursor agent model |
| `IMAGE_AGENT_TIMEOUT_SEC` | `7200` | Agent timeout (image gen is slow) |
| `IMAGE_AGENT_WORKSPACE` | `/workspace/grok-tools` | Agent workspace / artifact root |
| `CURSOR_AGENT_BIN` | `agent` | Cursor CLI binary |

Needs `agent` on PATH plus Cursor and R2 secrets in env (or via `export-card-secrets.py`). Shared agent helpers: `agent_run.py`. R2 upload primitive: `upload_r2.py`.

### upload_r2.py

Standalone R2 upload (S3 SigV4, stdlib). Also used by `generate_image.py`.

```bash
python3 /workspace/grok-tools/upload_r2.py --file /path/to/image.png --key images/demo.png
# or stdin: {"file":"...","key":"...","bucket":"grokbot"}
```

## send_riker.py

POST a message to Captain Riker’s Titan webhook (`RIKER_WEBHOOK_URL` + `RIKER_WEBHOOK_AUTH`).

```bash
python3 send_riker.py --message "Hello Number One"
```

## YouTube (youtube_auth.py + youtube_upload.py)

Schedule uploads to Nate's two channels via the YouTube Data API v3 (stdlib only).
Channel aliases: `main`, `clips`. Refresh tokens live in `data/youtube_tokens.json`
(0600, gitignored) keyed by alias, with the channel id/title recorded at auth time.

### Env

- `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` (preferred), falling back to
  `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. Never printed.
- Google Cloud project must have **YouTube Data API v3** enabled.
- Best client type: **TVs and Limited Input devices** (enables device flow). A
  **Desktop app** client also works via the manual path (`http://localhost` redirect).
- OAuth consent screen: while in *Testing*, add Nate's Google account as a test user,
  and note refresh tokens expire after 7 days. Set it to *In production* for durable tokens.
- Unverified (unaudited) API projects: YouTube locks API-uploaded videos to **private**
  until the project passes the YouTube API compliance audit, so `--publish-at` scheduling
  only goes public on an audited project. Custom thumbnails need a phone-verified channel.

### Auth (once per channel)

Nate approves in his own browser, so there is no localhost callback on the box.

```bash
# Device flow (tried first): prints verification_url + user_code
python3 youtube_auth.py start --alias main
python3 youtube_auth.py poll --alias main --wait     # after Nate approves

# Manual fallback (auto-selected if the client rejects device flow, or --flow manual):
# start prints auth_url; Nate approves, copies the dead http://localhost/?code=... URL
YT_CODE='http://localhost/?state=...&code=...' python3 youtube_auth.py finish --alias main --code-env YT_CODE
# or: printf '%s' "$URL" | python3 youtube_auth.py finish --alias main

python3 youtube_auth.py status    # refreshes each token, shows channel titles
```

In the Google consent screen, pick the right channel (brand account) for each alias.

### Upload

```bash
python3 youtube_upload.py --alias clips --file ep.mp4 --title "The Daily Log" \
  --description "..." --tags "AI,Star Trek" --thumbnail thumb.jpg \
  --publish-at 2026-10-13T08:00:00-05:00 --category 24 --dry-run
```

`--publish-at` (RFC3339 with offset) forces `private` + `status.publishAt`. Defaults:
`--privacy private`, `--category 28`, `--made-for-kids false`. `--dry-run` validates
inputs and auth without uploading. Output: `{ok, video_id, url, studio_url, ...}`.
A thumbnail failure is reported (`thumbnail_error`) without failing the upload.
