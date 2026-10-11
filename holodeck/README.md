# Holodeck — Starship Grokbot pipeline

Code and docs for the Starship Grokbot stick-figure shorts and the Titan Bridge
music video. Rendered media, voice takes, voice models (.onnx) and Python envs
are NOT committed (see `.gitignore`); they are regenerated or re-downloaded.
Working copy lives at `/workspace/holodeck` on the Grok Bot box.

| Path | Purpose |
|---|---|
| `STYLE-GUIDE.md` | Series look, cast, rules, episode idea list |
| `QUICKSTART.md` | How to request/build a new episode end to end |
| `storyboards/*/STORYBOARD.md` | Plan of record per episode |
| `brand/make_intro.py`, `make_sting.py` | 1 s intro and 3 s outro sting (logo card, no tagline) |
| `brand/make_branded.sh` | Wraps an episode with intro + sting |
| `brand/backup-tagline/` | Older logo cards that still had the tagline |
| `titan-hello-world/stick-poc/stickfig.py` | Stick-figure rig (poses, walk, faces) |
| `titan-hello-world/stick-poc/inkset.py`, `sets.py` | Ink-on-paper drawing helpers and bridge sets |
| `titan-hello-world/stick-poc/engine.py`, `render.py` | Frame engine and ffmpeg render driver |
| `titan-hello-world/stick-poc/make_captions.py`, `cues/` | Lyric captions and per-section cues for the song video |
| `titan-hello-world/*.py`, `*.ass`, `*.json`, `*.txt` | Original Grok Imagine music video: remix EDL, FX/HUD passes, lyrics/titles |
| `voices/demoN/` | One folder per episode: `<episode>.py` renderer, `build_audio.py`, `timeline.json`, `captions.ass`, `robot.sh`, `finalize.sh`, `sfx.py` |
| `voices/demo12-local/`, `demo14/`, `demo15/` | Piper (box-only, CPU) episodes: Rate Limited local, The Standup, Dark Mode |
| `voices/cast/*.json` | Per-character voice settings |
| `voices/cast/robot.sh`, `voices/robot.sh` | Grok Bot metallic robot filter |
| `voices/finalize.sh`, `cast/finalize.sh` | Loudness/finishing pass for dialogue |
| `voices/analyze.py`, `words.py`, `vowelcheck.py` | Take QA: word-check, timing, pronunciation ("bot" not "boat") |
| `piper/*.onnx.json` | Piper voice configs (download matching `.onnx` from rhasspy/piper-voices) |
| `cover-chars/` | "Thinking with AI" cover characters and robot hello tests |
| `season1/` | Season One compilation build (`build_season.py`, chapters, card, thumbnail) |

Related docs at repo root: `barclay-movie-log.md` (production log + costs),
`local-music-gen-research.md` (Suno replacement research).
