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
