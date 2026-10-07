# grok-tools

Python scripts Grok Bot writes and runs. Logs go in `logs/` (not committed). Secrets come from env, never files.

## dig.py

General Cursor-CLI digger: pass a **research prompt** and the **shape of results** to return. Different tasks use different schemas (job cards, calendar events, food events, …).

Stdout is one JSON object: `{ok, statusCode, items, trello?, usage?, error?}`. Progress logs go to `logs/dig.log` and stderr. Secrets are never printed.

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
