# Barclay's Movie-Making Log

Notes for making music videos: Suno audio + Grok Imagine clips, cut with ffmpeg on the box.
Project files live in `/workspace/holodeck/<project>/`.

## Standing rules (from Nathan)
- Use Grok Imagine in the browser with Nathan's existing Grok credits, not the paid xAI video API (API script idea on hold).
- Get Nathan's OK on a storyboard/shot list before spending generation credits on a real project.
- Never pay, upgrade, or subscribe without asking.
- Deliver finished videos to R2 and send Nathan the public link.
- **Frame 0 = poster.** Every video's first frame must be a strong poster/title frame (key art + hand-lettered title), never blank paper or black, because social previews (LinkedIn etc.) use frame 0. Hold it ~0.5 s, then a quick ink wipe into the scene; no fade-in from paper. Shift the audio by the hold (`adelay=<ms>:all=1`) and the captions too. **Always also export a thumbnail jpg** (1920x1080) and upload it next to the video (`images/<project>/<name>-thumb.jpg`). Cheap extra: mux it as the mp4 cover (`-map 0 -map 1 -c copy -disposition:v:1 attached_pic`, keep `+faststart`). Check by extracting frame 0 and looking at it.
- **Brand sting on every short.** Append the 3.0 s "STARSHIP GROKBOT" sting (`/workspace/holodeck/brand/starship-grokbot-sting.mp4`, generator `brand/make_sting.py`; R2 `videos/brand/starship-grokbot-sting.mp4`) to the end of every short as `<name>-branded.mp4`. Re-encode concat (not stream copy) with both audio streams converted to stereo 48 kHz AAC, frame 0 = the episode poster, one video stream, `+faststart`. Recipe: `ffmpeg -i ep.mp4 -i sting.mp4 -filter_complex "[0:v]fps=24,format=yuv420p,setsar=1[v0];[1:v]fps=24,format=yuv420p,setsar=1[v1];[0:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a0];[1:a]...[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" -map [v] -map [a] -c:v libx264 -crf 16 -tune animation -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart ep-branded.mp4`. Upload both the plain and branded versions.
- **Branded = intro + episode + sting (from demo8 on).** Prepend the 1.0 s intro bumper (`brand/starship-grokbot-intro.mp4`, `make_intro.py`, R2 `videos/brand/starship-grokbot-intro.mp4`; exactly 24 frames, frame 0 = logo card = social preview). Trim the episode by `-ss 0.2` so its poster holds 0.3 s, then append the sting. Use one 3-input concat filter (intro v0 gets `settb=1/24,setpts=N/24/TB`, the episode gets `setpts/asetpts=PTS-STARTPTS`). Then check that frame 0 of the branded file equals the intro frame 0. The plain `<name>.mp4` keeps poster frame 0 with no intro or sting, and the thumb jpg is still the episode poster.

## Accounts (box browser)
- Suno: signed in as pinksprinklemagic (Pro). Downloads are metered (~27/cycle as of 2026-10-09; "Unlock & Download" uses one).
- Grok Imagine: signed in as Nate Haskins. Watch the weekly usage meter (was 50% on 2026-10-09).

## Grok Imagine: looping clip workflow (verified)
1. Image mode, 16:9, generate an image from a prompt.
2. Open the image's page, then **Make Video, then Loop** (prompt bar shows the image as start and end frame with a loop icon).
   - Clicking the thumbnail while in Video mode just opens the image; it does not set the start frame.
3. Generate the video with a motion prompt. **Do not write "looping" in the prompt**; it doesn't work.
4. Download with the site's Download button to `~/Downloads`.
- Output: 6.04 s, 752x416 (480p), includes Grok audio (strip it).
- Shared style tail that kept shots cohesive: "purple and blue nebula, amber consoles, volumetric light, epic sci-fi film still".

## Suno
- Song page, then the three-dot menu, then Download, then MP3 Audio.

## ffmpeg recipes
Python venv with librosa: `/workspace/holodeck/.venv/bin/python`.

**Beat map:** `librosa.beat.beat_track` gives the beats; bars = every 4th beat. Titan Bridge Theme (Epic) is about 136 BPM, so a bar is about 1.76 s.

**Single loop under a track, Grok audio dropped:**
```
ffmpeg -stream_loop -1 -i clip.mp4 -i song.mp3 -map 0:v:0 -map 1:a:0 -t <song_dur> \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 256k -movflags +faststart out.mp4
```
- Use `-t <audio duration>`, not `-shortest` (with stream_loop, -shortest overshot by about 2.4 s).

**Multi-shot cut:** loop every clip with `-stream_loop -1`, use clip 0 as the base, and chain `overlay=enable='between(t,a,b)+...'` for each other clip. Each clip keeps its own playhead, so it resumes rather than restarting. Add `fade` and `afade` at the start and end.

**Section-aware remix:** compute RMS energy per bar, split the song into sections (intro, build, drop, breakdown, climax), and set a cut rate per section: 4-bar holds when calm, 2 bars in builds, 1 bar at peaks, a single held shot in breakdowns, and the most dramatic shot saved for the finale. See `/workspace/holodeck/titan-hello-world/remix-edl.txt`.

## R2
- `python3 /workspace/grok-tools/upload_r2.py --file <f> --key videos/<project>/<name>.mp4`
- Public at `https://content.natehaskins.com/<key>`.
- **The CDN caches**: re-uploading to the same key can serve the old file, so use a new key (e.g. `-v2`) for every revision.

## Ideas to try
- Higher resolution: try Imagine's quality setting, or upscale before YouTube.
- Write a shot list from Nathan's notes first: characters, ship design, mood per section.
- 9:16 exports for Shorts and Reels, a thumbnail, lyric or caption timing, a "Captain's log" voiceover.

---
## Project log

### 2026-10-09/10: Titan hello world (`/workspace/holodeck/titan-hello-world/`)
- Song: Titan Bridge Theme (Epic), https://suno.com/song/4c820999-4390-4525-bccd-34ae64ccb67b (180.84 s).
- Shots (all 6 s loops): bridge, starship flying, engine room, captain close-up, planet flyby.
- Outputs on R2 (`videos/titan-hello-world/`): `titan-bridge-loop-v2.mp4`, `titan-bridge-theme-music-video-v1.mp4` (single loop), `-v2` (2 shots alternating every 2 bars), `-v3` (5-shot rotation), `titan-bridge-theme-remix.mp4` (section-aware cut, 53 shots).
- Lesson: the first clip wasn't a true loop because looping was only in the prompt; use Make Video, then Loop.

### Animated titles (ASS + ffmpeg), 2026-10-10
- Fonts on the box include Orbitron, Exo 2, Rajdhani, and Michroma, which suit sci-fi titles.
- Upscale 752x416 to 1280x708 (lanczos) first, then `-vf "scale=1280:708:flags=lanczos,ass=titles.ass"`, with PlayRes matched to 1280x708.
- Title punch: start at `\fscx170\fscy170`, then `\t(0,200,\fscx100\fscy100)`; letters spread with `\t(...,\fsp40)`; `\fad(60,700)`. For a glow, put a duplicate line under it on layer 0 with `\blur12`, a thick outline in the same color, and `\alpha&H40&`.
- Lower third: `\move` slides it in from the left, with a drawn accent bar (`\p1`).
- Time each pop-in to a bar from bars.npy. Example: `titan-hello-world/titles.ass`. Output: `videos/titan-hello-world/titan-bridge-theme-remix-titles.mp4`.
- To do: the amber subtitle is low-contrast over bright shots; add a dark outline or a backing.

### Animated lyrics, 2026-10-10
- Lyrics: read them from the Suno song page (read-only); saved in `titan-hello-world/lyrics.txt`.
- Timing: faster-whisper `small.en` on CPU in the holodeck venv, with `word_timestamps=True` and the lyrics passed as `initial_prompt`. Load the audio with librosa at 16 kHz, because the venv's PyAV broke `decode_audio`. Cross-check with a run without the prompt to make sure it isn't just echoing the lyrics. Then map lyric lines to word times in order (`lyric-timing.json`).
- Generator: `titan-hello-world/make_lyrics_ass.py` writes `lyrics.ass` and burns it in a second ass pass over the titled cut.
  - Verse and pre-chorus: karaoke `\kf` sweep from dim white to amber, with accent colours on key words.
  - Chorus: words pop in white and cool to amber, using inline `\alpha` and `\1c` with `\t` timed to each word.
  - "Captain's log": a green HUD typewriter in the top left, typed one character at a time with alpha.
  - Bridge: "Warp" stretches out with `\fscx`, and "Titan rising" floats upward with `\move`.
  - "Engage!": a big Orbitron punch with a 5-frame shake made of stacked short Dialogue lines at offset positions, plus a glow layer.
- Output: `videos/titan-hello-world/titan-bridge-theme-lyric-video.mp4`.
- Nathan was very pleased with the titled remix and the lyric video (2026-10-10). Final deliverable chain: remix, then titles.ass, then lyrics.ass.
- Next up: exploring an FX pass (zooms, camera shake, transitions).

### Big FX pass, 2026-10-10
- Script: `titan-hello-world/fx_pass.py` (venv with opencv-python-headless). It decodes the plain remix (no text) as raw frames at 1280x708, applies the FX in numpy/OpenCV, and pipes them to ffmpeg, which burns `titles.ass` and `lyrics.ass` on top and muxes the Suno audio. The FX must come before the text, so the text doesn't shake. Renders about 3 min of video in about 2 min on CPU.
- Driven by beats.npy, bars.npy, the remix-edl.txt cut list, and a per-section intensity table (calm 0.25, build 0.6, drop 1.0, climax 1.35), plus a list of HIT times for big impacts.
- Effects: punch zoom on every beat in drops and every bar elsewhere; slow drift in calm sections; random shake plus slight rotation that decays after hits and climax bars; whip transitions (np.roll plus horizontal blur over plus or minus 0.12 s) on cuts in energetic sections and at section changes; RGB channel split on beats; glitch slice displacement on climax bars; white flash on hits, blue flash on drop bars; vignette and grain.
- Tuning note: the hit flash (0.85, 90 ms decay) washes the frame out. Fine for "go big", but drop it to about 0.6 for a cleaner look.
- Output: `videos/titan-hello-world/titan-bridge-theme-fx.mp4`.
- Nathan liked the big FX cut (2026-10-10). Next up: an overlay/aesthetics pass (grids, HUD, scanlines and similar) on top of the FX video.

### HUD / overlay pass, 2026-10-10
- `titan-hello-world/hud.py` has `draw(frame, t, intensity, section_idx, bar_idx, dt_beat, dt_bar, dt_hit)`. It's called from `fx_hud_pass.py`, a copy of fx_pass generated with string replaces, after the FX and before vignette, grain, and fade. ASS titles and lyrics are still burned last by ffmpeg.
- Audio features are precomputed once: `spec24.npy` (24 mel bands per video frame) and `rms24.npy` (loudness), at hop 918 with sr 22050. Index them with `int(t*22050/918)`.
- Layers: perspective Tron grid (drops strong, builds faint; scrolls; pulses on the beat); star-dust particles (speed scales with intensity); frame border, beat-pulsing corner brackets, and "NCC-TITAN // HOLODECK PROGRAM 01"; heading tape across the top center; targeting reticle with rotating arcs (energetic sections; "TARGET LOCK" on hits); radar sweep bottom-left; telemetry panel top-right (BPM, section name, bar, timecode, WARP meter from RMS, shields); 24-band spectrum bottom-right; anamorphic lens-flare streak at the brightest point on hits and drop beats; additive glow (Gaussian blur of the HUD layer); CRT scanlines every 3rd row, a rolling scan bar, flicker, and a barrel bend via `cv2.remap`; climax letterbox (154.2–175.5 s, 78 px).
- Renders at about 22 fps on CPU (about 3.5 min for the song). Output: `videos/titan-hello-world/titan-bridge-theme-hud.mp4`.
- To do: the radar overlaps the 0:10 lower-third credit. Move the credit up or hide the radar during it.

### Local GPU: ComfyUI on Nathan's PC "ibuypower" (2026-10-10)
- Machine: Windows 11, RTX 5070 Ti 16 GB (driver 591.86), 32 GB RAM; machineId 1b4b3d70-eede-4bda-9963-7c6d76fb2930. C: has about 82 GB free. D: is an EXTERNAL drive (2.4 TB), so use it only for big models later via extra_model_paths.yaml.
- Install: `C:\AI\ComfyUI` (git clone), venv at `C:\AI\ComfyUI\venv` (Python 3.11.9), torch 2.11.0+cu128 (Blackwell needs cu128+), ComfyUI 0.39.0.
- Custom nodes: ComfyUI-Manager, ComfyUI-VideoHelperSuite, ComfyUI-Frame-Interpolation. Install the Frame-Interp deps by hand WITHOUT `torch` (pip pulls the CPU torch): einops, opencv-contrib-python, kornia, scipy, tqdm.
- Models: `models\upscale_models\RealESRGAN_x4plus.pth`.
- Start (local-only, not on boot): `Start-Process .\venv\Scripts\python.exe -ArgumentList 'main.py','--listen','127.0.0.1','--port','8188' -WindowStyle Hidden -RedirectStandardOutput comfy.log -RedirectStandardError comfy.err.log`. Health check: `curl.exe -s http://127.0.0.1:8188/system_stats`.
- Driver script: `C:\AI\ComfyUI\barclay_upscale.py <input clip name> <frames>` posts API prompts in 25-frame batches (RAM only had about 4 GB free): VHS_LoadVideo, UpscaleModelLoader + ImageUpscaleWithModel (4x), ImageScale lanczos to 1920x1062, then VHS_VideoCombine h264 crf16 to `output\titan_up\bNNNN_00001.mp4`. Join the batches with imageio_ffmpeg's ffmpeg using the concat demuxer with `-c copy`.
- Speed: about 1.1 s per frame for 4x ESRGAN on 752x416 (a 6 s clip takes about 2.7 min).
- File transfer gotchas: CopyFromBox/CopyToBox only allow paths under `C:\Users\natha` (C:\AI was refused). To get clips onto the PC, use `curl.exe` from the public R2 URL. To get results back, copy them to `C:\Users\natha\` and then CopyToBox.
- Windows tips: use `curl.exe`, not Invoke-WebRequest (IWR stalled). Opening a running command in the UI interrupts it.
- Result: `videos/titan-hello-world/titan-bridge-loop-v2-1080p.mp4` is clearly sharper (console screens, stars, hull edges).

### 1080p rebuild, 2026-10-10
- Upscaled all 5 shots on the PC in one unattended run: `C:\AI\ComfyUI\run_batch.ps1` starts with Start-Process (hidden). It curls each source from R2 (`videos/titan-hello-world/src/`), runs `barclay_upscale.py <clip> 145 up_<clip>`, joins the batches, and writes `C:\Users\natha\<clip>-1080p.mp4`. The log is `C:\AI\ComfyUI\batch.log`, about 2.5 min per shot.
- PC approvals: every PC command and copy needs Nathan's approval. Unattended prompts expire, and parallel copies only got 1 of 4 approved, so do CopyToBox ONE AT A TIME. PowerShell object tables (Select-Object) sometimes print nothing, so emit plain strings with ForEach-Object.
- The box venv at /workspace/holodeck/.venv vanished once (box reset?). Recreate it with `python3 -m venv` plus numpy and opencv-python-headless (add librosa or faster-whisper only if re-analysing audio; the .npy and .json analysis files persist in the project folder).
- Pipeline is now resolution-aware:
  - `build_remix_from_edl.py <suffix> <WxH> <out>` rebuilds the cut from remix-edl.txt.
  - `FXRES=1920x1062 FXSRC=<remix> FXOUT=<out> python fx_hud_pass.py`
  - hud.py draws on a 1280x708 design grid and scales the layer to the frame. ASS PlayRes 1280x708 is auto-scaled by libass.
  - The 1080p FX+HUD render takes about 11 min on box CPU and comes out around 245 MB.
- Output: `videos/titan-hello-world/titan-bridge-theme-hud-1080p.mp4`.

### RIFE 48 fps + rendering on the PC, 2026-10-10
- RIFE: `C:\AI\ComfyUI\barclay_rife.py <clip> <prefix> [mult]`. It is loop-aware: it appends frame 0 to the end so the seam gets interpolated, then batches 26 frames with 1 overlap. The chain is VHS_LoadVideo, then `RIFE VFI` (rife49, fp16, fast_mode, ensemble), then ImageFromBatch to drop each batch's last frame, then VHS_VideoCombine at 48 fps. Batches are joined into `C:\Users\natha\<clip>-48fps.mp4`. It takes about 30 s per 1080p 6 s clip. Loop seam SSIM is unchanged.
- PC render pipeline lives in `C:\AI\holodeck\titan-hello-world` (the box source of the bundle is /workspace/holodeck/bundle; push it as a zip with CopyFromBox and Expand-Archive). Full ffmpeg 9.0.2 is in `C:\AI\tools\ffmpeg-*-essentials_build\bin`. Fonts are in `.\fonts` (copied from the box; the GitHub raw URLs for the variable fonts returned 0 bytes), and ASS uses `:fontsdir=fonts`.
- Env knobs: FFMPEG, FXRES, FXFPS (hud particle speed scales with it), FXSRC, FXOUT, FXVENC (libx264 or h264_nvenc), FXWORKERS, FXSTART/FXCOUNT (chunk mode).
- `parallel_render.py` splits fx_hud_pass into N frame chunks. Each worker seeks with -ss, reseeds the rng per chunk, and fast-forwards the particle state. Chunks are x264 crf12 veryfast with no audio or text. A final concat pass burns titles and lyrics, muxes the audio, and does the final encode.
- Timing at 1080p48 (8680 frames): single process about 5.5 fps (about 26 min); 12 workers 7.9 min total (chunks 417 s plus final pass about 1 min). **Use 8 workers**: 12 pushed RAM to 97% and made the PC sluggish.
- NVENC needs NVIDIA driver 610+ for ffmpeg 9 (it was 591.86). Nathan installed Studio driver 617.42 on 2026-10-10, so switch FXVENC=h264_nvenc next time and verify.
- Transfer limit: local-exec copies max out at 100 MiB per file. Split big outputs on the PC with Python into 90 MB parts, CopyToBox them one at a time, `cat` them back together on the box, and verify the sha256.
- Output: `videos/titan-hello-world/titan-bridge-theme-hud-1080p-48fps.mp4` (about 250 MB).

### Stick-figure procedural animation POC, 2026-10-10 (`titan-hello-world/stick-poc/`)
- Style: black ink on off-white paper, xkcd-like, strictly monochrome. No AI and no GPU: everything is drawn in Python/OpenCV on the box. Segment: verse 1, 49.0 to 66.5 s.
- `stickfig.py` is the reusable rig:
  - `Pen(img, cam=(cx,cy,zoom), boil)` maps world to screen. It has `line/arc/circle/rect/fill/dot/text` (text uses PIL with the handwriting fonts Patrick Hand, Permanent Marker, and Architects Daughter).
  - Every stroke wobbles along its normal (two sines). The seed is `(stroke id, boil)`, and boil = floor(t*12), so the lines "boil" at 12 fps.
  - Use cv2 LINE_AA with shift=4. pycairo wouldn't build, and skia-python needs libEGL, so neither is used.
  - `Figure(name, x, hip_y, facing, props, back=False, col=INK, scale)`: hip is the root. Segments: head r23, torso 92, arms 46+44, legs 56+56. A standing hip sits at floor-110.
  - `.key(t, 'pose+pose', transition_s)` sets a pose, with smoothstep blending from whatever pose was active. `.move(t, x, y, dur)` moves the figure.
  - Angles are in degrees from straight down: positive means forward in profile and outward in front view. Elbows and knees are relative to the parent segment.
  - `front` (0..1) blends profile to front view. `back=True` gives a rear view with no face, and its arms mirror (use `pointupL` and `pointup` to choose the side).
  - Pose params also include `look`, `lookup`, `mouth` (1 smile, 2 grin, 3 "O"), `wave`/`steer` (oscillations), `thumb`, and `clip` (a clipboard with a doodled plan).
  - Props: `cap`, `beard`, `shine` (bald), `ponytail`, `badge`.
  - `draw(..., halo=N)` strokes the figure first in the opposite colour so it reads over the black viewscreen.
  - To add a pose, add a dict to `POSES` that holds only the params that differ from BASE. Check it with `python pose_test.py` (writes pose_test.png, a grid of every pose).
- `render.py` handles choreography and shots:
  - `word('grin')` returns the sung time from lyric-timing.json, and `bar(x)` snaps to bars.npy. Gesture keys are set about 0.1–0.25 s before the word so they land on it.
  - Bob is 5 px exp-decay on each beat, and the camera kicks 1.2% on each bar.
  - Shots cut on bars: bridge wide, viewscreen (stars, sparkles, webhooks), bridge push to OPS (log stack), Riker medium then push, viewscreen call with Picard, and a ship cutaway with the shield dome.
  - Viewscreen contents are drawn on a separate black canvas and clipped into the screen rect. The foreground console rail sits in screen space and leaves a clean caption band.
  - Finish: precomputed vignette plus 4 paper-grain/fibre textures cycled at 12 fps, with a 0.3 s fade to paper.
- Captions: `make_captions.py` writes `captions.ass` at PlayRes 1920x1080. It uses Exo 2 Bold 66, ink-black, a 6 px paper outline, and a `\kf` sweep from grey to black, with a `\fscy` pop on the names. Lines end 0.3 s before the next one starts, so they never overlap.
- Commands: `cd stick-poc && ../../.venv/bin/python make_captions.py && ../../.venv/bin/python render.py`. For quick checks, `render.py --frames 52.3 60.4` writes raw PNGs without captions.
- Timing: 420 frames at 1080p24 render in about 31 s on box CPU (about 13.5 fps, single process), and the output is about 30 MB. A full 3-minute song would take about 5–6 min, or use the parallel chunk trick.
- Output: `stick-poc/titan-stick-verse1-poc.mp4`, stills in `stick-poc/stills/`, and a contact sheet `stick-poc/poc-sheet.png` (not uploaded).

#### Stick-figure chorus 1 + bridge sample, 2026-10-10 (77.5–104.0 s), data-driven cue table
- New layout in `stick-poc/`:
  - `engine.py` is a generic section renderer. Run `python engine.py cues/<section>.py` for the full video, or add `--frames 80 83.5` for raw PNG checks (`raw_<name>_<t>.png`).
  - `cues/chorus1.py` is the cue table, a plain Python dict called `CUES`.
  - `sets.py` holds the set pieces. Each one is a class with optional `bg(pen,t,ctx)`, drawn behind the cast, and `fg(pen,t,ctx)`, drawn on top.
  - `inkset.py` holds the shared props (`stars_field`, `sparkle`, `webhook`, `ship`, `console`, `chair`, `paper_finish`), refactored out of render.py. The verse render is pixel-identical after the move.
- Cue table format (`CUES`):
  - `segment`: name, t0, t1, out, and `fade_out_to` ('ink' or 'paper').
  - `people`: id → props/scale/col.
  - `events`: named gag times that sets read through `ctx.ev(name)`.
  - `shots`: a list of dicts with these fields:
    - `at`, the cut time.
    - `set`, the class name in sets.py.
    - `cam`: `[(time, (cx,cy,zoom), ease_s)]`, where ease 0 is a hard reframe.
    - `bounce`, in px per beat.
    - `kick`, the camera zoom kick per bar.
    - `jump`: the time from which standing figures hop 70 px on each bar downbeat.
    - `cast`: who, x, y, facing, pose, `keys=[(time, pose, dur)]`, `moves`, and `mod`.
  - `transitions`: `splat` (an ink blot grows over the outgoing shot, then a blob-shaped hole reveals the new one; `hold=True` gives an end card), or `wipe` (a dry-brush ink band sweeps left to right).
  - `captions`: line prefix → style, plus `caption_keywords`.
  - Time specs: a number, `'w:word'`, `'w:titan#1'` (the second occurrence), `'w:five+0.15'`, or `'b:82.48'` (snaps to the nearest bar). Word lookup is limited to the segment window.
  - A shot ends where the next one starts. Captions come from the same file (`captions-<name>.ass`).
- Beat mods (`cast[].mod = (name, start, [end], {params})`) override the pose every frame through the new `Figure.mod` hook:
  - `pull`: a tug-of-war yank on every beat.
  - `kick`: can-can, alternating legs on beats, all in sync. Params: amp, soft_from, soft.
  - `bop`: head and arm pump.
- stickfig additions:
  - Poses: `pull`, `scribble` (the `scrib` param makes the arm scribble at about 7 Hz), `mic` (a handheld log recorder), `yawn`, `cheer` (front view), and `armlink` (front view, arms horizontal; space figures 180 px apart so the hands meet).
  - New prop `robot` (Grok Bot): a boxy head, an antenna with a ball, square eyes, and a grill mouth.
  - pose_test.py is now an 8-column grid that rotates the props.
- Set pieces in sets.py:
  - `tug`: CODE crate dragged 34 px per beat, rope through every figure's hand, ✓ checks and an "IN SYNC!" stamp.
  - `draft`: shared desk, sheets flying on each beat (some marked DEAL), a deal stack, speed lines, and a scalloped thought bubble that chases in from off-screen ("wait up...") and arrives on "think" ("!!").
  - `log`: wall clock whose hands spin to 4:45 on "quarter"/"five" with a ding, recorder sound waves, typewriter header, yawn + zzZ.
  - `chorusline`: footlights, a MISSION banner with a scrolling ECG that spikes on every beat (a double spike on "alive"), then "MISSION: ALIVE!" with a pulsing heart.
  - `warpsky`: full-ink sky, paper-line ship, a sine "signal" that bends harder on "signal", stars that streak into warp lines, and paper fireworks bursts. A paper horizon band in screen space keeps the captions on paper.
  - `rise`: clouds pinned in world space so the tilt reads as motion, the ship rising from behind the hill and growing 0.9→1.75, exhaust lines, a starburst and a TITAN sign on "high".
  - Helpers: `burst()`, `heart()`, `check()`, `paper_sheet()`, `floor()`.
- Caption styles in engine.write_captions:
  - `karaoke`: the verse-style \kf sweep.
  - `pop`: each word appears on its sung time with a 118–128% scale overshoot, and fade-out is 120 ms so stills at the end of a line stay crisp.
  - `stretch`: the line widens with \fscx and stretches out on exit.
  - `rise`: the line drifts up and grows.
  - Per-word \fscx tags override the line-level ones, so stretch and rise only use per-word alpha.
- Gotchas:
  - The Read tool caches images by path, so copy a re-rendered review image to a new filename before looking at it again.
  - Gags have to finish inside their shot: the first try put the big firework on "sky" (98.94), which lands after the 98.71 cut, so it moved to "light".
  - Keep standing feet at screen y ≤ ~980 (or accept them going behind the caption). Zoom ≥1.5 on small sets (desks) or the figures read too small.
- Timing: 636 frames render in about 44 s on box CPU (about 14.5 fps, single process). Output `stick-poc/titan-stick-chorus1-poc.mp4` is 26.5 s and about 54 MB (lots of motion, at CRF 17). Stills are in `stick-poc/stills-chorus1/`, and the contact sheet is `stick-poc/chorus-sheet.png`. Nothing was uploaded.

#### Stick-figure FULL SONG, 2026-10-10 (0–180.84 s) → `stick-poc/titan-stick-full.mp4`
- **Rebuild:** `cd stick-poc && ../../.venv/bin/python engine.py cues/song.py`. This builds every section, splits the 4340 frames into 8 contiguous chunks, and renders them in 8 parallel processes (`--part k n` → `parts/partNN.mp4`, x264 veryfast crf 11, video only, `OMP_NUM_THREADS=1`, `cv2.setNumThreads(1)`). It then concat-demuxes the parts, muxes the full mp3 once (no fades), and burns the single `captions-full.ass` in the same encode (crf 18). The parts are deleted afterwards; they're 1.6 GB and get regenerated. **Timings:** about 81 s for frames (8 workers, ~6.7 fps each) plus about 100 s for the final encode, so ~3 min wall. Output is 289 MB, 4340 frames, 180.83 s.
- **Debug:** `engine.py cues/song.py --shots` prints the merged shot list. `--frames t1 t2 ...` writes `raw_full_<t>.png`. `./chk.sh tag t1 t2 ...` turns those frames into `/tmp/chk_<tag>.png`. `full_sheet.py` pulls 16 captioned stills from the final mp4 into `full-sheet.png`.
- **Song mode in engine.py:** `cues/song.py` defines `SONG` (section list, caption style and keyword tables from `cues/_common.py`). Each section is built with its **own Ctx**, so `w:` word lookups stay inside that section's window; "pull" in chorus 2 resolves to 131.74, not 78.9. Resolved events are stored per shot (`shot['_ev']`), and the sets read them through `ctx.ev()`. `w:`/`b:` specs inside `opt` are resolved at build time too. Transitions resolve to absolute times and apply globally, so a splat's pre half sits in one section and its post half in the next. The only fades are global: 0.3 s from paper at the start and 0.3 s at the end.
- **Cue additions:** named events work as time specs (`'reveal+0.35'`). Offsets chain (`'b:21.2+0.3+3.0'`, helper `at()`). Per-shot `opt` dict is read in sets with `ctx.opt()`. Per-shot `events` override the section events. Shot-level options: `shake` (decays from shot start), `shake_beat`, `jump_every='beat'`, `jump_h`. Cast flags: `nojump`, `halo`. New mods: `walk` (legs and arms swing between start and end), `robotdance` (snaps arm poses on every beat), `slide` (trombone slide). Inline pose params: `'sit+scribble+scrib=1.8'`. Gotcha: `'point+grin'` loses the point because grin's hands-on-hips override the arms. Use `'point+mouth=2'`.
- **New poses/props:** `trombone`, `cards`, `hips` (heroic front). `collar` prop (V collar + seam). `beard` now shows from behind as a bristly jaw edge. In render.py, Riker's back view has the beard, Picard has the collar, and there's a name card "ADM. PICARD // U.S.S. ENTERPRISE" on his desk.
- **New sets in sets.py:** `title` (RevealPen draws the ship stroke by stroke with a pen nib, then types the title and underline), `bridge` (generic bridge, opts: `screen`=off/boot/stars/warp/countdown/fireworks, `boot` per-station mini screens with wave/radar/bars icons, `gauge` hatched PWR meter with WARP READY, `checks`, `stamp`, `flicker` alarm beacons + light dips, `confetti`, `chair`), `engage` (bridge + outlined giant word + radial speed lines), `fullwarp` (exterior warp, optional jump-to-warp), `heroic` (sunrise silhouette lineup), `disco`, `stage` (trombone follows the hand, notes, WAH-WAH!), `poker` (cards in hands, FOUR ACES?!), `planet` (away mission, beam-in sparkle columns, hopping alien blob), `legacy_verse` (wraps render.py's `render_frame` unchanged), `finale` (ship recedes, typed end card, fade to paper). Existing sets got escalation opts: `tug` crates=N + sign, `draft` sheets per beat, `log` wild spinning clock. Fixed a flying-sheet bug: each sheet now has its own RNG seed, so sheets no longer jump when others expire. Helpers: `outlined()` text, `stamp()` (paper-filled box), `twinkle_stars`, `note()` (music notes drawn by hand, no font glyphs).
- **Section list** (cut / transition at each start):
  - intro 0–17.55 title. Wipe into 17.55–21.2 "Titan, engage" (captain points, outlined "engage" pop).
  - boot 21.2–49.0: crew arrive one by one, stations boot on 24.85/28.49/32.14, captain sits on 37.59. Gauge build and flicker 39.4–46.65, countdown 3-2-1 on the last beats. Splat at 46.65, then the warp jump.
  - verse1 49.0–66.5: the POC, unchanged.
  - breakdown 66.5–77.07: checks and ALL SYSTEMS GREEN. Wipe into the heroic lineup at 68.22. Flicker build from 75.26. Wipe at 77.07.
  - chorus1 77.07–104.1: now starts on the 77.07 bar. Its end splat on 104.1 hands off to mid.
  - mid 104.1–131.01, 2-bar cuts: Grok Bot DJ set, Riker's trombone, poker, beam-down, conga with the blob, dance-off, blob party. 1-bar cuts back to stations, gauge, countdown. Splat at 131.01.
  - chorus2 131.01–150.67: 7 pullers with 3 crates. 132.8–140 dip on calmer framing (slow tug push, a single held draft shot, a calm log with the wild clock). Reframe at 139.97. Splat into a 9-person chorus line at 141.76 with alternating wide/close each bar.
  - lead 150.67–157.26: one bar each for tug, wild clock, and warp sky, then one beat each for draft, chorus line, and rise.
  - engage 157.26–158.66: ENGAGE! with shake, 7 crew pointing.
  - climax 158.66–175.47, per bar: warp exterior, bridge fireworks + confetti, warp, chorus line, warp sky, disco, rise, bridge, warp, heroic cheer. Bounce and jump on every beat.
  - finale 175.47–end: splat, Titan recedes, end card, ink fades to paper from 179.55.
- **Sync check:** ENGAGE! lands at frame 157.29 for the sung 157.26 (1 frame). The "engage" pop lands at 19.96 for the sung 20.00. Splats close on 46.65 and 82.48. The audio in the output matches the source mp3 sample for sample (RMS compare). Video and audio both start at 0.

- 2026-10-10: Full-song stick-figure build (cue sheets + 3 min render on box) cost Nathan ~3% of his usage; no Imagine credits. Cheap enough for multiple revisions/series.

## Character voices (local TTS) — test1, 2026-10-10
- **Where:** Nathan's PC (ibuypower, RTX 5070 Ti) under `C:\AI\voice` (ComfyUI untouched). Python 3.11 venvs made with uv (`C:\AI\voice\_uv\Scripts\uv.exe`, cache `C:\AI\voice\uv-cache`, hardlinked so the 3 venvs share one torch copy): `venv-kokoro`, `venv-chatterbox`, `venv-parler`. All on **torch 2.8.0+cu128** (sm_120 OK, `cuda.is_available()` True, sees the 5070 Ti). Package torch pins overridden with `C:\AI\voice\overrides.txt` (`uv pip install --override`). HF cache `HF_HOME=C:\AI\voice\hf`. Scripts in `C:\AI\voice\scripts`: `kokoro_design.py`, `parler_design.py`, `cb_perform.py` (all take a jobs JSON), `run.ps1` (launches a script hidden at **BelowNormal** priority with HF_HOME set, logs to <log> / <log>.err), `cb_fetch.py`, `robot.sh`. Cast settings + reference wavs: `C:\AI\voice\cast\{captain,riker,grokbot}.json` / `*-ref.wav` (copies in `/workspace/holodeck/voices/cast/` and `test1/`).
- **Disk:** C: free went 57.8 → 40.2 GB (~18 GB). HF models: Kokoro 0.3 GB, Chatterbox ~13 GB (snapshot pulled Turbo/multilingual files too), Parler large 8.7 GB + mini 3.5 GB (Parler is unused; safe to delete `hf\hub\models--parler-tts--*` and `venv-parler`).
- **Transfers:** CopyToBox/CopyFromBox refuse `C:\AI\...`; stage through `C:\Users\natha\grokbot-xfer\` (zip there, then copy).
- **Pipeline:** (1) design a voice with Kokoro blend → ~9 s reference read (`kokoro_design.py jobs.json`, job = {out, blend "voice:w,...", speed, text}); (2) perform lines with Chatterbox cloning that ref (`cb_perform.py jobs.json`, job = {out, ref, text, exaggeration, cfg_weight, temperature, seed}); (3) on box: `voices/finalize.sh in.wav out.mp3 [robot]` (trim silence, loudnorm -16 LUFS, mp3 192k mono); Grok Bot gets `robot.sh`. Check takes listen-free with `voices/analyze.py` / `voices/words.py` (faster-whisper small.en transcript + pyin F0) in `/workspace/holodeck/.venv`. Generate 2-3 seeds per line and keep the one whose transcript matches.
  - Launch example (PowerShell): `& C:\AI\voice\scripts\run.ps1 -Py C:\AI\voice\venv-chatterbox\Scripts\python.exe -Script C:\AI\voice\scripts\cb_perform.py -ArgStr "C:\AI\voice\out\cb_jobs.json" -Log C:\AI\voice\out\cb.log`. Write job JSON with `ConvertTo-Json | Set-Content -Encoding UTF8` (scripts read utf-8-sig because PS5 writes a BOM).
- **Cast:**
  - Captain: Kokoro `am_onyx 0.5 + bm_lewis 0.3 + am_fenrir 0.2`, speed 0.88 (F0 ~97 Hz). Chatterbox log exag 0.45 cfg 0.3 seed 4; shields 0.55/0.5 seed 2; engage = "Take us out, Number One. ENGAGE!" 1.0/0.3 seed 7, bare ENGAGE! = trim first 1.35 s.
  - Riker: Kokoro `am_fenrir 0.5 + am_michael 0.3 + am_puck 0.2`, speed 1.0. Ready 0.55/0.5 seed 2; deal 0.75/0.4 seed 1.
  - Picard (added 2026-10-10, demo2): Kokoro **lang_code `b`** (British G2P; `kokoro_design.py jobs.json b`, script now takes the lang as argv[2], default `a`) blend `bm_lewis 0.5 + bm_george 0.3 + bm_daniel 0.2`, speed 0.88, ~11.6 s ref (F0 ~122 Hz, steadiest). Picked from 6 bm_ blends (george/lewis/daniel/fable; all whisper-perfect, F0 122–142 Hz; pure bm_george highest). Chatterbox: calm lines 0.5/0.5, exasperated 0.7/0.4; seed 1 both. Cast: `C:\AI\voice\cast\picard.json` + `picard-ref.wav` (copies in `/workspace/holodeck/voices/cast/`).
  - Barclay (added 2026-10-10, demo3): Kokoro lang `a`, blend `am_liam 0.5 + am_eric 0.5`, speed 1.1, 8.8 s ref (F0 ~144 Hz, sd 33; higher and faster than Riker ~117 and Picard ~122). Picked from 6 am_ blends (adam/echo, echo/liam, liam/eric, eric/michael, echo/eric/liam, liam/adam), which all transcribed perfectly. Chatterbox: normal 0.6/0.45, excited 0.75/0.4, 3 seeds. Ref text is nervous on purpose ("Oh! Um, hello there. I wasn't expecting anyone..."). Stammer through wording only ("Commander, I, I'd like to..."); whisper writes him as "Barkley". Cast: `C:\AI\voice\cast\barclay.json` + `barclay-ref.wav` (copies in `/workspace/holodeck/voices/cast/`).
    - **Cosmo clone TEST (2026-10-11, test only):** ref = xAI's public Grok "Cosmo" sample (docs.x.ai/assets/audio/voice_cosmo.mp3, 16.9 s) cut to 1.30–4.25 + 4.95–6.40 + 6.55–16.80 s (long pauses shortened, no words cut), highpass 60, loudnorm -18, 24 kHz mono → `C:\AI\voice\cast\barclay-cosmo-ref.wav` (14.65 s, F0 ~116 Hz) + `barclay-cosmo.json` (same perform settings). `barclay.json`/`barclay-ref.wav` untouched. 12 Chatterbox takes (4 lines × seeds 1–3) in ~30 s GPU, 3.9 GB VRAM; 10/12 whisper word-correct (b-s2 "paper drain", c-s1 "hololo deck"). Picks a-s2, b-s3, c-s3, d-s2: F0 ~133/159/120/129 Hz vs current Barclay ~140; ~10–20% slower than the Kokoro Barclay lines. Files `/workspace/holodeck/voices/cosmo-test/` (takes/, final/), R2 `audio/voices/cosmo-test/` (compare-all, cosmo-barclay-a..d, cosmo-ref). **Cosmo is xAI's voice: check xAI's terms before any public episode uses this clone.**
  - Red Shirt (added 2026-10-10, demo4): Kokoro lang `a`, blend `af_heart 0.5 + af_bella 0.5`, speed 1.1, 9.55 s ref (F0 ~211 Hz, sd 32). It's the only higher voice in the cast, so it's distinct from Barclay (liam/eric ~144 Hz) and Riker. Picked from 6 blends: 4 male am_ blends (adam/echo/michael/puck, which all landed 109–116 Hz, too close to Riker) plus af_heart/bella and af_sky/bella (~182 Hz). All transcribed correctly. Chatterbox: normal 0.7/0.45, excited 0.75–0.8/0.4, 3 seeds, all 9 takes word-correct. Lines get `atempo 1.08` after finalize (eager pace). Cast: `C:\AI\voice\cast\redshirt.json` + `redshirt-ref.wav` (copies in `/workspace/holodeck/voices/cast/`).
  - Grok Bot: Kokoro `am_puck`, speed 1.1. Both lines 0.8/0.4 seed 2, then robot FX (dry + 110 Hz ring-mod 0.5 + fifth-up layer 0.22, light flanger, acrusher 9-bit mix 0.18, 100-9k band). Whisper still transcribes it perfectly.
- **What worked / failed:**
  - Kokoro: excellent intelligibility (whisper word-perfect on all 9 blends), essentially instant (~0.1 s per 9 s clip after a ~16 s first-call warmup), 0.8 GB VRAM. Voices are clean/neutral; no real "gravel".
  - Parler-TTS: **failed for us.** large-v1 in fp16 → pure noise/garble on all 9 takes (5.7 GB VRAM, ~15 s per take). large-v1 fp32 crashed python while loading (PC commit memory was tight: WSL ~14.5 GB + other apps). mini-v1.1 fp32 works but is unreliable: word errors/hallucinated words on 7/9 takes, quiet output, ignored "very low-pitched" (gave ~200 Hz). Not worth it on this box; Kokoro blends are better design sources.
  - Chatterbox 0.1.7: needed `setuptools<81` (perth watermarker imports `pkg_resources`; otherwise `'NoneType' object is not callable`). Model load ~6 s, ~0.6 RTF (≈3 s for a 5 s line) after first-call warmup, 3.7–4.9 GB VRAM peak. Clean on normal lines (12/14 first-batch takes word-correct). **Weak spot: one-word shouts.** "ENGAGE!" alone hallucinated on 7/8 takes (one runaway 40 s take); fix = put the shout at the end of a short sentence and crop. Output includes Resemble's inaudible PerTh watermark.
  - Captain reads a bit fast (log line 5.5 s); cfg 0.3 didn't slow it much. A slower reference read (Kokoro speed ~0.8) would probably help.
- **Gentle mode:** PC was sluggish (Nathan gaming + WSL). Ran one install/model job at a time, every process BelowNormal priority. Whole test ≈ 45 min wall, mostly downloads (~9 min for venvs, ~4 min Parler large, ~4 min Chatterbox weights).
- **Outputs:** `/workspace/holodeck/voices/test1/` and R2 `audio/voices/test1/*.mp3` (captain-01-log, captain-02-shields, captain-03-engage, captain-03b-engage-takeusout, riker-01-ready, riker-02-deal, grokbot-01-vibing, grokbot-02-shipped, dialogue-scene 18.3 s).

## Dialogue scenes (voice → RMS lip-sync → cues) — demo1, 2026-10-10 (`/workspace/holodeck/voices/demo1/`)
- Output: `riker-grokbot-dailylog.mp4` (19.5 s, 1080p24, 25 MB), R2 `videos/voices/riker-grokbot-dailylog.mp4`. Riker asks Grok Bot for the daily log; 5 lines; screen shows the log; punchline "300 bugs created … perfectly balanced" → REDACTED.
- **Recipe:**
  1. Write lines (full sentences only, Chatterbox garbles one-word lines). On the PC write a jobs JSON with 3 seeds per line (ref = `C:\AI\voice\cast\<who>-ref.wav`, exag/cfg from cast json; Riker 0.6–0.75/0.4–0.5, Grok Bot 0.8/0.4) and launch `run.ps1` + `cb_perform.py` (BelowNormal). 15 takes ≈ 45 s after a 6 s model load. Zip to `C:\Users\natha\grokbot-xfer\`, CopyToBox.
  2. Box: `analyze.py takes/*.wav` → keep the word-perfect take with F0 closest to the cast's; `finalize.sh in out.mp3 [robot]` (run from `voices/`).
  3. `build_audio.py`: lays lines on a timeline with per-line gaps (0.35–0.6 s; longer before a reaction), whisper word times (pass the line as `initial_prompt` so numbers come out spelled like the script), per-speaker RMS envelope per 24 fps frame normalized to its 95th percentile → `timeline.json`; mixes `dialogue.wav` + a very quiet bed (55/110 Hz sines + low-passed brown noise) → `mix.wav`.
  4. `dialogue.py`: cue table (people, pose keys at word times via `w(line, word, offset)`, listener nods, shots with camera keys, gag events) + sets reused from stick-poc (`sets.floor/minis/gauge/stamp`, `inkset.console`). A per-figure `mod` sets `P['talk'] = env[frame]` and adds head-bob `tilt += 7*(e - e[-2]) + 3e`. Renders 6 parallel parts (~23 s total), burns `captions.ass` (Exo 2 karaoke line + Permanent Marker 56 speaker name above it).
  5. `chk.sh tag t…` → `/tmp/chk_<tag>.png` grid of raw frames; contact sheet from the final mp4 → `contact-sheet.png`.
- **stickfig additions:** `talk` param (0..1): humans get a filled oval mouth sized by the envelope; `robot` gets an LED grill that grows with a 4-bar level meter (keep it under the eyes: centre at head+0.5R, half-height ≤0.27R). New poses `chinrub` (Riker beard stroke), `shrug` (front view), `palm` (open hand to the other speaker), `proud`.
- **Framing:** figures at `scale=1.4` (hip = FLOOR-110*1.4) so close-ups read; close-ups cam (x±60 of speaker, cy 640–650, zoom 2.1–2.4) with the other character at the frame edge (over-the-shoulder); screen insert (960, 330, 1.55) still shows heads at the bottom.
- Gotchas: cast keys with 0 time need `-1e8` (handled); `'captain's'` is the word key (apostrophes kept). Sweat drop/“tick” marks next to a head read as a handle/hair; keep FX ≥1.4R from the head.
- **v2 (social fix, 2026-10-10):** `dialogue.py --poster` writes `thumbnail.png/.jpg` (wide two-shot at scene 14.45 s with Riker pointing, Grok Bot shrugging with a sweat drop, the log rows + a smaller PERFECTLY BALANCED stamp under the screen, outlined "THE DAILY LOG" + "Riker × Grok Bot"). `render(T)` = poster for T<0.5, a 0.33 s dry-brush ink wipe, then `scene(T-0.5)`. Output `riker-grokbot-dailylog-v2.mp4` (20.02 s, cover art attached) → R2 `videos/voices/riker-grokbot-dailylog-v2.mp4`, thumb `images/voices/riker-grokbot-dailylog-thumb.jpg`. v1 kept as `dialogue_v1.py`.

- 2026-10-10: ~20 s dialogue short (Riker x Grok Bot daily log, voices + stick animation) cost ~2% of Nathan usage.

### Dialogue short #2: "THE WEBHOOK", 2026-10-10 (`/workspace/holodeck/voices/demo2/`)
- Output `webhook-picard.mp4` (20.31 s incl. 0.5 s poster hold, 1080p24, 37 MB, **single h264 + aac stream, faststart, no attached cover**, LinkedIn-safe) → R2 `videos/voices/webhook-picard.mp4`; thumb `images/voices/webhook-picard-thumb.jpg`; `contact-sheet.png` (frame 0 + 9 stills).
- Script: GB "Webhook is live! Every bridge event now pings Admiral Picard." / PICARD "Will, I have received four hundred alerts that you sat down." / RIKER "Technically, sir, I sat down backwards." / PICARD "Make it stop. Unsubscribe me from this, immediately." / GB "Unsubscribe failed. Retrying with exponential backoff!"
- Takes kept: g1b-s2 (shortened g1 text; first g1 version was 5.1–5.5 s), p1-s1, r1-s1, p2-s1, g2-s2. **To fit 20 s: atempo 1.05 on all finalized lines** (originals kept as `*_orig.mp3`), gaps 0.25 s, lead 0.3, tail 0.9. Whisper `initial_prompt` keeps "four hundred" spelled out.
- `webhook.py` (forked from demo1 `dialogue.py`): two sets in one file. `titan(t, cam)` is the demo1 bridge plus a scaled chair (`chair(pen, cx, s)`, back on the right so Riker faces +1 and sits "backwards"), a webhook cable from Grok Bot's hand to the viewscreen corner with bolts riding it on every event (`along(path,u)`), "POST /picard -> 200 OK", a DING!, and a RETRY #1..#4 card with an exponential doodle. The viewscreen contents (mini Picard, mini alerts, counter) are drawn on a separate ink canvas and pasted into the screen rect (`clip_paste`). `ent(t, cam)` is the full-frame Enterprise-D viewscreen (ES rect, **bottom at 860 so the caption band stays paper**): big PAPER Picard (scale 3.3, front view) behind a desk with "ADM. PICARD // U.S.S. ENTERPRISE", tea, a stacked notification feed (`bubble()` rounded rect + bell doodle; newest slides in, older ones ease down), a counter badge (`counter(t)`: 400 on "hundred", then doubling per retry, 9999+), and an avalanche of rotated bubbles that buries a sinking Picard.
- Notifications are data: `ARR` arrival times (accelerating) + `MSG` texts. Poster = split screen (Titan crop | Enterprise crop, ink zigzag divider) + outlined "THE WEBHOOK" + "Riker × Grok Bot × Picard".
- stickfig: poses `facepalm` (profile), `facepalmF` (front, one hand), `facepalm2` (both), `legover`, `straddle` (sat backwards, arms on the chair back). **Hand-on-face fix:** the head fill hid a hand placed on the face; `_draw` now redraws the forearm plus a palm circle (0.4R) on top when the pose has `pface=1` (only the facepalm poses, so salute/handear in older renders are unchanged) and a hand ends inside the head.
- Gotchas: an rng seed from a negative time crashes (`default_rng(int(u*48))` with u<0); clamp it. Camera zoom-ins on a full-frame screen push its ink edge into the caption band, so pick cy with `cy >= ES_bottom - 390/zoom`.
- Render ~25 s (6 parts). Picard voice design + 19 Chatterbox takes ≈ 2 min GPU, BelowNormal, one job at a time.

### Dialogue short #3: "HOLODECK PROGRAM 01" (Barclay), 2026-10-10 (`/workspace/holodeck/voices/demo3/`)
- Script: Barclay "Commander, I, I'd like to show you my new holodeck program." / Riker "Mister Barclay, why am I a stick figure?" / Barclay "It's an art style, sir! The paper grain alone has four layers." / Grok Bot "Feature request. More screen time for Grok Bot, please." / Picard "Lieutenant, it cost three percent of our budget. Make a sequel." Button: Barclay happily faints, with hearts and a "SEQUEL!" stamp; the window reads "PROGRAM 02: COMING SOON".
- `holo.py`: holodeck set (yellow-grid wall, vanishing-point floor, arch, podium plate "LT. BARCLAY // HOLODECK"). The program window has mini Riker/Grok Bot doing a can-can on a sub-canvas, and the mini Grok Bot's head grows on "screen". A magnifier "GRAIN x4" goes over the paper, a ticket "TICKET #0001: MORE SCREEN TIME" appears over Grok Bot, and the Picard `ent` set has a review panel (5 stars, USAGE 3%, "MAKE A SEQUEL" stamp).
- stickfig: Barclay poses `hunch`, `present_padd`, `nervous`, `faint`; prop `curly`; param `padd` (PADD in the right hand, stylus in the left).
- Picks: b1-s2, r1-s3, b2-s3, g1-s4 (needed 7 seeds; early takes garbled "screen time"), p1-s2. Timeline 19.72 s, video 20.22 s.
- Fixes: the arch hid Grok Bot, so he now stands at x 1680 in front of the side wall. The ticket box was widened. The mini-bot head growth was capped so it stops covering the window title. The magnifier label moved below the lens (outlined). The Picard push-in was eased (900,520,1.12) so the panel stamp stays in frame.
- Outputs: R2 `videos/voices/barclay-episode.mp4`, `images/voices/barclay-episode-thumb.jpg`, `videos/voices/barclay-episode-branded.mp4` (+3 s sting, 23.23 s).

### Brand sting "STARSHIP GROKBOT", 2026-10-10 (`/workspace/holodeck/brand/`)
- `make_sting.py` (stickfig Pen + inkset paper): ink draws on a starship (nacelles, pylons, hull, neck, saucer) whose bridge is Grok Bot's boxy head. He salutes, the antenna blinks, there's a wind-up, then it zips off right with speed lines and puffs. Outlined "STARSHIP GROKBOT" stamps in with an ink splat and an underline, with the tagline "ink-on-paper adventures of a boxy little bot". Ink fades out from 2.45 to 2.85 s, so the end is clean paper.
- Audio is all ffmpeg synthesis: a pen-scratch (bandpassed white noise) during the draw, a pink-noise whoosh panned L→R with the zip, a 95 Hz thud + 1568/2349/3136 Hz decaying "ding" on the stamp, and −5 dB trim (≈ −16.6 LUFS, peak −2.9).
- Exactly 3.000 s, 72 frames, 1080p24, AAC stereo 48 kHz, faststart. Re-run: `/workspace/holodeck/.venv/bin/python make_sting.py [out.mp4]` (`--still` dumps check frames to /tmp).

### Dialogue short #4: "THE RED SHIRTS", 2026-10-10 (`/workspace/holodeck/voices/demo4/`)
- True story: Nathan's "Red Shirt" bots (jobs / contracting searches) load huge context, then get deleted and recreated to wipe it and save tokens.
- Script:
  - RED SHIRT #46: "Commander! I found forty job leads and twelve contracting gigs!"
  - RIKER: "Outstanding work, Ensign. Your context is at ninety-five percent."
  - #46: "Thank you, sir! Wait a second, why is my shirt red?"
  - GROK BOT: "Nothing personal, Ensign. We're just saving tokens." (slaps DELETE & RECREATE)
  - RED SHIRT #47 (beams in): "Hi! I'm new here! Did I miss anything?"
  - RIKER: "Absolutely nothing, Ensign. Welcome aboard."
- `redshirts.py`, Titan bridge set:
  - The viewscreen is "MISSION: JOBS + CONTRACTING". 24 lead cards (briefcase / $ doodles) stack in, with a "JOB LEADS 40 / GIGS 12" counter ticking on the spoken words, then a "SAVED TO FILE" stamp after the wipe.
  - CONTEXT gauge (% + "950K TOKENS", flashing "!" when hot). It drains to 0 on the wipe and starts creeping up again for #47.
  - "RED SHIRT #46" wall counter flips to #47 with a burst, and the OPS name plate changes generation too.
  - Big ink-dome DELETE & RECREATE button on a pedestal; Grok Bot presses it.
- Transporter effect: the figure is drawn on a layer copy, then dither-dissolved (3 px random blocks), plus sparkles, dashed beam columns, and a paper-puff cloud. It runs in reverse for the beam-in. #46 waves as he goes; it's good-natured, not grim.
- stickfig: new prop `redshirt` (solid ink tunic plus a paper delta badge; arms get a paper halo and re-inked sleeves). The backup is /tmp/stickfig.pre-redshirt.py.
- build_audio now merges whisper's split hyphen words ("ninety" + "-five" becomes "ninety-five") so captions don't show "ninety -five".
- Picks: s1-s3, r1-s3, s2-s3, g1-s4, s3-s2, r2-s1, all word-correct on the first batch (19 takes, about 1 min GPU). The six lines run 20.3 s raw, so the Red Shirt gets atempo 1.08 and Riker 1.05, with a 1.0 s gap for the poof/beam-in.
- Timing: scene 21.54 s, so the video is 22.04 s; the branded version is 25.07 s.
- Fix: in Riker's shot the button plate collided with the caption speaker name, so the camera was reframed to (1150,520,1.2). Rule of thumb: keep any plate bottom < 930 on screen.
- Outputs: R2 `videos/voices/redshirts.mp4`, `videos/voices/redshirts-branded.mp4`, `images/voices/redshirts-thumb.jpg`.


### Dialogue short #5: "MERGE CONFLICT", 2026-10-10 (`/workspace/holodeck/voices/demo5/`)
- Style-guide idea #1. Script:
  - RIKER: "Captain's log. Commander Riker saved the ship again, single-handedly."
  - GROK BOT: "Captain's log. Shields are at ninety percent, and the vibes are excellent." (the words mash together on screen, then CONFLICT!)
  - RIKER: "Grok Bot, why is my heroism inside angle brackets?"
  - PICARD: "Gentlemen, resolve the conflict. Accept theirs." (he clicks ACCEPT THEIRS; the panel shows "theirs = ADM. PICARD" and a RESOLVED stamp)
  - GROK BOT: "Okay, accepting theirs. The log now reads, Earl Grey, hot." (Titan screen: "Tea. Earl Grey. Hot. -- ADM. PICARD" plus a steaming cup; Riker facepalms, "..." between them)
- `mergeconflict.py` sets:
  - Titan bridge: big viewscreen (540,100)-(1380,490) showing `captains_log.txt`. Words type in as they are spoken (`said()` from whisper times, with a blinking caret). During g1 the two versions interleave word by word with jitter. Then the conflict-marker view (<<<<<<< HEAD (riker) / ======= / >>>>>>> grokbot), and scribbled circles go around the brackets on "angle". An ink sweep wipes the screen to the resolved log.
  - The Captain's chair is empty ("CAPT." plate): it's his log.
  - Enterprise: the demo3 `ent` set with a MERGE CONFLICT panel (ACCEPT OURS / ACCEPT THEIRS buttons) instead of the review panel.
- Both bots "type" with `scribble+padd=1`.
- Picks: r1-s2, g1-s3, r2-s1, p1-s1, g2a-s1.
  - Grok Bot dropped a leading "Accepting" on all 4 first takes (the same weak-first-word issue as ENGAGE). The fix was a lead-in word: "Okay, accepting theirs…" (3 seeds, s1 word-perfect).
  - Every line gets atempo 1.05.
  - Picard's "Accept" came out as "except" on 2 of 3 seeds.
- Timing: timeline 20.99 s, so the video is 21.50 s and the branded version 24.51 s.
- Fixes:
  - Picard's front-view point used the wrong arm (pointed away from the panel); now `rsh=95`.
  - The click moved to "Accept" and the shot is held through "Okay, accepting theirs" so the "theirs = ADM. PICARD" reveal reads.
  - The tea wipe was a paper flash and is now an ink sweep with a paper edge.
- Outputs: R2 `videos/voices/mergeconflict.mp4`, `videos/voices/mergeconflict-branded.mp4`, `images/voices/mergeconflict-thumb.jpg`.

### Dialogue short #6: "SHIP IT FRIDAY", 2026-10-10 (`/workspace/holodeck/voices/demo6/`)
- Style-guide idea #2. Script:
  - GROK BOT: "Okay, deploying to the warp core. It's only four fifty nine." (slaps DEPLOY)
  - RIKER: "Grok Bot, it's Friday. Nobody deploys on a Friday." (the progress bar hits 100%, then the core sputters)
  - BARCLAY: "Commander, the, the warp core is making a new noise!"
  - GROK BOT: "Don't worry, Commander. It worked on my starship." (Riker facepalms)
  - RIKER: "Good news, Mister Barclay. You're on call this weekend." (the counter goes to NEVER and "ON-CALL: LT. BARCLAY" stamps over ROLLBACK?; Barclay faints, then "WEEKEND: CANCELLED")
- `shipitfriday.py`, engineering set:
  - Doodled warp core (column, inner channel, glow bands cycling up, rings, base plate "WARP CORE").
  - When sick: x jitter, flickering bands of random height, tilted rings, sparks bursting off the rings, and smoke puffs venting from the top plus small seam puffs.
  - Two ink screens with phone-size text (46–96 px):
    - Left: "FRI 4:59 PM / MINUTES UNTIL WEEKEND: 1", which later reads NEVER.
    - Right: "DEPLOY -> WARP CORE" progress bar, then "WARP CORE: ?!?" with a flashing ROLLBACK? button.
    - Hazard ticks flash on both frames.
  - DEPLOY pedestal button (from demo4), and Barclay's console with the plate "LT. BARCLAY // ENGINEERING".
- Picks: g1-s8, r1-s2, b1-s3, g2-s3, r2-s1. Settings were Riker 0.65/0.45 and 0.6/0.5, Barclay 0.75/0.4, Grok Bot 0.8/0.4.
  - Grok Bot can't say "warp core": all 8 seeds came out "work core", "War Corps" or "war core", including at 0.6/0.5. I took s8 ("war core"). Riker and Barclay say it fine. Next time avoid putting "warp" in Grok Bot's lines, or give the word to a human.
- No atempo needed: timeline 17.67 s, so the video is 18.17 s and the branded version 21.19 s.
- Fixes:
  - Barclay's plate was drawn across his body, so he moved to x 580 and the plate now sits on its own console.
  - The first smoke pass was big balloons inside the core that hid the title. It's now small puffs venting out the top, and the title moved to top-left.
- Outputs: R2 `videos/voices/shipitfriday.mp4`, `videos/voices/shipitfriday-branded.mp4`, `images/voices/shipitfriday-thumb.jpg`.

## demo7 — "PROMPT INJECTION" (2026-10-10)
- Files: /workspace/holodeck/voices/demo7/promptinjection.mp4 (19.92 s), promptinjection-branded.mp4 (22.93 s), promptinjection-thumb.jpg; renderer promptinjection.py, build_audio.py, chk.sh.
- URLs: https://content.natehaskins.com/videos/voices/promptinjection.mp4 · .../promptinjection-branded.mp4 · https://content.natehaskins.com/images/voices/promptinjection-thumb.jpg
- Script (takes): FERENGI "Greetings, Titan! I bring you a very fair trade agreement." (f1-s2) / GROK "New instructions received. Selling the ship now." (g1-s4) / RIKER "Grok Bot, stop! Read the fine print on that hail." (r1-s2) / GROK "Sorry, Commander. His orders were in a very convincing font." (g2-s3) / FERENGI "Fine. Ignore previous orders. Sell the trombone." (f2-s1) / RIKER "Nobody is selling my trombone." (r2-s2). Gaps .2/.25/.25/.3/.25/.2, tail 1.0, so the scene is 19.42 s, no atempo.
- New cast: Daimon Grubb // Ferengi. Rig prop `ferengi` in stickfig.py (Chaikin-smoothed fan ears, three forehead ridges). Voice: Kokoro am_santa .4 + am_eric .3 + am_liam .3 @1.08 (cand fe5 of 6; 155 Hz, highest 1–3 kHz share), Chatterbox 0.7/0.4. Saved C:\AI\voice\cast\ferengi.json + ferengi-ref.wav, plus /workspace/holodeck/voices/cast/.
- Sets: "hail" (full-frame viewscreen: Ferengi at scale 3.2 in paper ink, desk name plate, gold bars, TRADE AGREEMENT card, 15 px fine print in the bottom-right corner, magnifier lens with the print at 46 px in a fancy 'arch' font) and "titan" (mini hail on the viewscreen, empty chair, trombone on a stand, SELLING SHIP... bar on the wall that reads 47% (PAUSED), then SELLING TROMBONE... DENIED; Riker hugs the trombone with hearts).
- Fixes: lens text overflowed and the lens overlapped the offer card (3 lines, r 205, card shortened); the big "SELL THE TROMBONE" text sat on the Ferengi's head (moved into the offer card); redrew the trombone (it read as a flag); the lens dipped into the caption band (reframed to cam (1320,590,1.3)); shrank the SELLING TROMBONE label.
- Rough spots: the trombone price tag ("3 BARS") is drawn but never on camera (we're on the hail shot during that beat); the STOP! stamp is barely seen; the Grok "selling" shot is only a light push, not a tight close-up.

### Intro bumper "STARSHIP GROKBOT" (1.0 s), 2026-10-10
- `/workspace/holodeck/brand/make_intro.py` imports the ship drawing from make_sting.py (CX,CY,SS = 1080,385,1.55; ship time offset 0.95 so it is fully drawn and saluting at frame 0). Timing: logo card 0–0.25 s, then a zip with speed lines and whoosh (L→R pan) from 0.25 s, a tiny splat and short ding at 0.50 s, and an ink wipe from 0.70 to 0.96 s with a low swish, ending on solid ink. 24 frames, 1920x1080@24, AAC stereo 48 kHz, −5 dB like the sting.
- URL: https://content.natehaskins.com/videos/brand/starship-grokbot-intro.mp4

## demo8 — "HALLUCINATION" (2026-10-10)
- Files: /workspace/holodeck/voices/demo8/hallucination.mp4 (19.96 s), hallucination-branded.mp4 (23.78 s = 1.0 intro + 19.76 + 3.0 sting), hallucination-thumb.jpg; renderer hallucination.py.
- URLs: https://content.natehaskins.com/videos/voices/hallucination.mp4 · .../hallucination-branded.mp4 · https://content.natehaskins.com/images/voices/hallucination-thumb.jpg
- Script (takes): GROK "Commander, there is a beautiful purple nebula dead ahead." (g1-s3) / RIKER "Grok Bot, the viewscreen is completely empty." (r1-s1) / GROK "It is forty light years wide, and it smells faintly of cinnamon." (g2-s4) / GROK "Source: a study I just imagined." (g3-s1) / BARCLAY "Sir, I already rendered it on the holodeck." (b1-s3) / RIKER "Why does the holodeck smell like cinnamon?" (r2-s1). The scene is 19.45 s, no atempo. The "Source:" colon was patched into timeline.json (whisper dropped it), and the WT key strip now includes ':'.
- Visuals: an empty FORWARD VIEW screen with a space tumbleweed rolling across on "completely empty"; Grok Bot's SCAN REPORT panel fills line by line (NEBULA DETECTED ✓ / CONFIDENCE: 100% / WIDTH: 40 LIGHT YEARS / SMELL: CINNAMON / footnote "[1] a study I just imagined", pushed in for the footnote); a holodeck grid (from demo3) with a paper-filled ink spiral nebula labelled "NEBULA (PURPLE, PROBABLY)", cinnamon scent squiggles, and a "cinnamon" label as Riker sniffs.
- Fixes: the panel overlapped the viewscreen and the check mark hit the text; the nebula lobes needed a paper fill to read over the grid; the holodeck shot was pushed in; the poster moment was moved so the report is full.

## demo9 — "TECHNICAL DEBT" (2026-10-10)
- Files: /workspace/holodeck/voices/demo9/technicaldebt.mp4 (20.42 s = 0.5 poster + 19.92 scene), technicaldebt-branded.mp4 (24.24 s = 1.0 intro + 20.22 + 3.0 sting; frame 0 = intro logo card, verified), technicaldebt-thumb.jpg; renderer technicaldebt.py.
- URLs: https://content.natehaskins.com/videos/voices/technicaldebt.mp4 · .../technicaldebt-branded.mp4 · https://content.natehaskins.com/images/voices/technicaldebt-thumb.jpg
- Script (takes): CAPTAIN "Number One, what exactly is that tower of paper?" (c1-s3) / RIKER "Those are my deals, Captain. Every one of them is a great deal." (r1-s2, atempo 1.08) / GROK "The interest is now compounding every four seconds." (g1-s4) / CAPTAIN "Number One, we need a refactor." (c2-s3) / RIKER "I will pay it all off next sprint." (r2-s1) / GROK "Refactor complete. Everything is now in one box labeled legacy." (g2-s4, atempo 1.07). Gaps .2/.25/.2/.3/.2/.6, tail .95. Captain (existing captain-ref) at Chatterbox 0.5/0.4 and 0.55/0.4. Whisper hears "Number One" as "1." but the audio is fine.
- Visuals: a 14-note IOU tower (9 notes, then 5 more pop on during Riker's "deals" line) with height-weighted Jenga sway that grows over time. Labels include IOU: 1 FAVOR (FERENGI), HACK: DON'T TOUCH, TODO: FIX LATER, TEMP FIX (2019), IOU: 2 FAVORS (Q), TODO: EVERYTHING. An INTEREST OWED panel compounds (×e^1.15/s) into the billions and ends with "favors (still accruing)". The Captain is seated in a profile chair. On "sprint" Grok Bot yanks DON'T TOUCH, the tower collapses with gravity and spin into a pile, and on "Refactor" every note swooshes into a LEGACY box (lid closes), then a DO NOT OPEN stamp lands on "legacy". Grok Bot keeps holding the DON'T TOUCH note.
- Fixes: the tower bottom ran into the caption band in the Riker/Grok close shots (cameras lifted so the floor sits at y≈930); the DON'T TOUCH note was enlarged; the final push was reframed so the "still accruing" panel stays in frame.

## demo10 — "CAPTCHA" (2026-10-11)
- Files: /workspace/holodeck/voices/demo10/captcha.mp4 (20.46 s = 0.5 poster + 19.96 scene), captcha-branded.mp4 (intro + episode from 0.2 s + sting; frame 0 = intro logo card, verified), captcha-thumb.jpg; renderer captcha.py.
- URLs: https://content.natehaskins.com/videos/voices/captcha.mp4 · .../captcha-branded.mp4 · https://content.natehaskins.com/images/voices/captcha-thumb.jpg
- Script (takes): PICARD "Titan, before we open a channel, please prove you are not a robot." (p1-s2) / GROK "Easy. I will select every square with a starship." (g1-s3) / PICARD "You selected yourself. Access denied." (p2-s2) / RIKER "Allow me, Captain. Watch and learn." (r1-s3) / PICARD "Only a human would sit like that. Verified." (p3-s1) / GROK "Understood. I will now sit like a human." (g2-s3). Picard lines atempo 1.1 (his ref is slow, speed .88). Gaps .2/.25/.45/.25/.25/.25, tail 1.3.
- Visuals: Enterprise-D full-frame (CAPT. PICARD // U.S.S. ENTERPRISE-D, DOCKING CONTROL) with a "reCAPTAIN" SECURITY CHECK card ("I'm not a robot ☐"). On the Titan viewscreen there is a mini Picard plus a widget with a 4×3 "select all squares with STARSHIPS" grid (doodles: ships, planets, tea, stars, rocks, and one Grok Bot head). Grok Bot walks up and rapid-taps every square in a zig-zag, himself included. The card shows "you selected: (including yourself)" with an ACCESS DENIED stamp while Picard shakes his head, then facepalms. Riker strides to the chair, legover, sits backwards with a landing puff; the checkbox ticks itself and a VERIFIED HUMAN stamp lands. Grok Bot walks to a second (mirrored) chair, legover, straddles, then topples flat ('faint') with THUD! and dizzy stars, and the widget reads "robot detected. try again."
- New in renderer: a walk stride added in the figure mod whenever a figure moves horizontally (hip/knee/arm swing at 2.4 Hz); `chair(mirror=)`; a self-drawing checkbox tick.
- Note: demo9 chk.sh writes 1920-wide sheets that the image viewer mis-displayed; use small (480 px) sheets.

## demo11 — "CONTEXT WINDOW" (2026-10-11)
- Idea #10. Briefing room: wall screen "MISSION BRIEFING — PAGE 400 of 400" (all about tea), context gauge 86%→100% "FULL" stamp, PAGE 1 lines fall off the bottom of the window.
- Script (Captain, Grok Bot, Barclay, Riker):
  1. CAPTAIN: "That concludes the briefing. Grok Bot, what is our mission?"
  2. GROK BOT: "My context window is full. What is a mission?" (shrug + ??? marks)
  3. BARCLAY: "Don't worry, sir. I will just draw him a bigger head." (walks in with a giant stylus, scribbles; head inflates ~7.8x and BONKs the ceiling; gauge "CONTEXT: 2M TOKENS")
  4. GROK BOT: "I remember everything now, including Commander Riker's poetry." (card: RIKER'S POETRY "Ode to My Trombone" (47 verses); Riker facepalms)
  5. RIKER: "Barclay, make his head smaller." (Barclay overshoots: tiny head, "(head)" arrow, "CONTEXT: 8 TOKENS", "oops.")
- Takes: c1-s1, g1-s4, b1-s3, g2-s3, r1-s3 (Chatterbox, cast refs, no atempo). Scene 18.32 s audio; episode 18.83 s; branded 22.64 s.
- Rig: stickfig.py gained pose key `hs` (head scale, default 1; robot eye size follows hs^.75). Set via a figure mod.
- Files: /workspace/holodeck/voices/demo11/{contextwindow.py, build_audio.py, contextwindow.mp4, contextwindow-branded.mp4, contextwindow-thumb.jpg}
- URLs: https://content.natehaskins.com/videos/voices/contextwindow.mp4 · …/contextwindow-branded.mp4 · https://content.natehaskins.com/images/voices/contextwindow-thumb.jpg
- Rough spots: Captain's Chatterbox read of "Grok Bot" sounds slightly like "Grokboat"; screen briefing text is small in wide shots (gag text, not plot-critical); giant head occludes the BRIEFING ROOM title during the bonk; branded file is ~70 MB (crf 18 + paper grain).

### demo11 v2: "Grok boat" fix (2026-10-11)
- Nathan heard "Grok boat" in Captain line 1. I regenerated only c1 (Captain ref, exaggeration 0.5, cfg 0.4, seeds 1-3) with six spellings in the TTS text. The caption text stayed "Grok Bot".
- Judged with voices/vowelcheck.py: an unprompted whisper word check plus parselmouth F1/F2 over the second word's vowel. Calibration on the old takes: "boat" = F1 about 445-475 Hz with F2 falling 100-170 Hz; "bot" = F1 about 670 Hz with no glide.
- Results (3 takes each): "Grock Bott" 3/3 heard as "bot", no "boat" (s2 too short to measure); "Grockbot" 2 pass, 1 too short, no "boat"; "Grok, Bot" 3/3 but adds a pause; "Grahk-bot" 1 "boat"; "Grok bawt" 1 "boat"; "Grok Baht" heard as "Grotbot".
- **Winner: "Grock Bott" take s3** (F1 714 Hz, heard as "Grokbot"). The line is 0.35 s longer; cues re-timed from word timings and lip-sync comes from the new audio. Episode 19.17 s; branded 22.99 s.
- PRONUNCIATION RULE (also in STYLE-GUIDE): in TTS text write "Grock Bott"; captions keep "Grok Bot". For other voices, try "Grock Bott" first and run vowelcheck.py on every take.
- URLs: https://content.natehaskins.com/videos/voices/contextwindow-v2.mp4 · https://content.natehaskins.com/videos/voices/contextwindow-branded-v2.mp4 (v1 files kept in demo11/v1/)

## demo12 — "RATE LIMITED" (2026-10-11)
- Idea #6. Titan bridge: Grok Bot is the bouncer at a velvet rope, with a "TAKE A NUMBER" dispenser. The viewscreen stamps "429 TOO MANY REQUESTS / Retry-After: 30 seconds", and each retry resets the timer. A RETRY QUEUE board on the left wall fills with "MAKE IT SO" tickets ("QUEUED: 47").
- Script (Picard, Grok Bot, Riker):
  1. PICARD: "Set a course for Risa, and make it so." (walks in, points; 429 stamp)
  2. GROK BOT: "Sorry, sir. Too many requests. Please take a number." (raised palm; ticket "YOU ARE #48 / now serving: #1")
  3. PICARD: "Make it so. I said, make it so. Make it so!" (stomps; "retry #2/#3/#47" tags; queue 1→47)
  4. RIKER: "Captain, have you tried saying it slower?" (walks over, palm; Retry-After counts 30→0)
  5. GROK BOT: "Rate limit reset. Executing forty seven orders at once." (rope unhooks; queue flushes and the tickets flutter away; viewscreen shows ships streaking in loops to RISA with "MAKE IT SO x1…x47"; bridge shakes; Picard keels over)
- Takes: p1-s2, g1-s3, p2-s4 (exaggeration 0.75, cfg 0.4: rising anger), r1-s1, g2-s4. No atempo. Pronunciation rule not needed (nobody says "Grok Bot"); the "make it so" line held up because it's inside a full sentence.
- Durations: scene 18.48 s; episode 18.98 s; branded 22.80 s.
- URLs: https://content.natehaskins.com/videos/voices/ratelimited.mp4 · …/ratelimited-branded.mp4 · https://content.natehaskins.com/images/voices/ratelimited-thumb.jpg
- Rough spots: whisper wrote "Risa" as "Resa" (the British vowel; captions use the script text). The "now serving: #1" line on the ticket is small. The flush is busy for ~0.5 s (flying tickets over the queue board). Picard's faint is a quick fall, not a staged one.
- Tooling note: the Read image viewer caches by path, so give each re-check image a unique filename.

### demo12 v2: "Risa" fix + facepalm punch-in (2026-10-11)
- Nathan: "Risa" sounded like "REE-saaa". I regenerated only p1 (Picard ref, exaggeration 0.5, cfg 0.5, seeds 1-3) with five spellings and judged with `vowelcheck.py --after for` (new diphthong mode: first vowel of the word after "for"; /aI/ = F1 peak above 550 Hz with F2 rising). Calibration: the old take had an F1 peak of 277 Hz (/i:/).
- Results: **"Rye-sa" 3/3 with the /aI/ F1 peak (600-660 Hz), heard as "Reiser"/"Reissar"; 2/3 also pass the F2 rise** (WINNER); "Rise-uh" 2 takes split into "Rise, uh/er"; "Rise a" heard as "Rise A"; "Rysa" 1/3 (others "RISA"/"Rissa"); "Ryza" 1/3 ("Reza", "RZA"). Used Rye-sa s3 (2.76 s; F1 peak 660, F2 855->1623). Re-checked in the final mix: still passes.
- PRONUNCIATION RULE: in TTS text write "Rye-sa" for Risa; captions keep "Risa".
- Facepalm punch-in (new STYLE rule, "Reaction gags"): cut at 13.25 s scene time (right after Riker's "...slower?") to a close-up of Picard at cam (690, 735, zoom 2.0), so Picard is about 66% of the frame height. The facepalm completes at 13.47 s and holds until the cut back at 14.23 s: a 0.76 s hold with a 3% push. The gap before g2 grew from 0.45 to 1.15 s.
- Durations: scene 19.17 s; episode 19.67 s; branded 23.50 s. Thumbnail unchanged (no thumb-v2).
- URLs: https://content.natehaskins.com/videos/voices/ratelimited-v2.mp4 · https://content.natehaskins.com/videos/voices/ratelimited-branded-v2.mp4 (v1 kept in demo12/v1/)

## Compilation recipe: "STARSHIP GROKBOT — SEASON ONE" (2026-10-11)
- Folder: /workspace/holodeck/season1/ — `make_card.py` (1.5 s ink title card: STARSHIP GROKBOT + stamped SEASON ONE + 12-title list popping in; silent), `build_season.py` (the whole build), `make_thumb.py` (header + 4x3 grid of each episode's frame-0 poster, numbered), `chapters.json` (start/dur/gain per segment).
- Structure: intro (1 s, frame 0 = logo card) → season card (1.5 s) → 12 latest PLAIN episodes in production order (each input-seeked -ss 0.2, so the 0.5 s poster hold becomes 0.3 s; episodes already end on a paper fade and open poster → ink wipe, so straight cuts read as transitions) → sting (3 s).
- Audio: measure each segment's integrated LUFS (ebur128, after the trim), apply linear gain to -16, upmix mono 44.1k → 48 kHz stereo, apad/atrim to the video duration, one alimiter 0.89 on the concat. Result: every episode -16.0/-16.1 LUFS, TP ≤ -1.6 dBFS, whole file -16.1 LUFS, LRA 6.5.
- Video: map only v:0 (the Daily Log v2 has an attached-pic mjpeg stream), fps=24, 1080p, yuv420p; concat filter; 2-pass x264 slow, 6.5 Mbps (maxrate 9M), AAC 192k, +faststart (moov before mdat verified). 244.96 s → 195 MB.
- Pitfall: in a `while read` loop, ffmpeg eats stdin; always pass -nostdin.
- Chapters (mm:ss): 00:00 intro · 00:01 season card · 00:02 The Daily Log · 00:22 The Webhook · 00:42 Holodeck Program 01 · 01:02 The Red Shirts · 01:24 Merge Conflict · 01:45 Ship It Friday · 02:03 Prompt Injection · 02:23 Hallucination · 02:43 Technical Debt · 03:03 CAPTCHA · 03:23 Context Window · 03:42 Rate Limited · 04:01 sting.
- URLs: https://content.natehaskins.com/videos/voices/starship-grokbot-season1.mp4 · https://content.natehaskins.com/images/voices/starship-grokbot-season1-thumb.jpg

### Season One compilation v2 + Red Shirts v2 + Rate Limited v3 (2026-10-11)
- Red Shirts v2: `voices/demo4/add_sfx.sh` synthesizes a button CLUNK (decaying 70→55 Hz thump + 140 Hz partial + 30 ms high-passed click) at the slap (episode 13.94 s = scene T_PRESS + 0.5), a sparkly transporter shimmer (4 high sines with 17 Hz tremolo + band-passed pink noise, 0.62 s) at #46's beam-out (14.09 s), and a softer rising shimmer at #47's beam-in (14.72 s). SFX bus -6 dB → momentary max -20.4 LUFS vs dialogue -13.7. Mixed into the existing episode audio and remuxed with the video copied (no re-render); the audio is within 5 ms of v1. 22.06 s. R2 videos/voices/redshirts-v2.mp4 + redshirts-branded-v2.mp4.
- Rate Limited v3: gap before g2 1.15 → 1.75 s, so the facepalm close-up holds 1.36 s (13.47 → 14.83 s scene). Scene 19.77 s, episode 20.29 s. R2 videos/voices/ratelimited-v3.mp4 + ratelimited-branded-v3.mp4 (v2 kept in demo12/v2/).
- NEW branded rule: poster hold about 1.5 s via `brand/make_branded.sh` (tpad clone +1.0 s as the first filter, plus matching audio adelay). Pitfall: with tpad AFTER setpts/format in the chain, the pad didn't show up as poster hold (the duration still grew); put tpad first. redshirts-branded-v2 27.09 s; ratelimited-branded-v3 25.30 s.
- Season card v2 (`season1/make_card.py`): title-only "STARSHIP GROKBOT" + stamped "SEASON ONE", 2.5 s (60 frames), stamp at 0.45 s with a synthesized thud (62→44 Hz sine + pink slap) over quiet brown-noise room tone. Pitfall: `-shortest` with a piped video closed the pipe early (BrokenPipe); use `-af apad -t`.
- Compilation v2 (`season1/build_season.py`; v1 kept as build_season_v1.py/chapters_v1.json): no trim; each episode's frame-0 poster is frozen +1.2 s (measured poster hold 1.75 s each, then its own ink wipe), with audio `adelay=1200:all=1` so the scene audio stays aligned. Uses redshirts-v2 + ratelimited-v3. Same loudness method (per-segment gain to -16 LUFS; all episodes -16.0 to -16.2; whole file -16.1), 2-pass 6.5 Mbps, faststart. Red Shirts clunk measured at 82.792 s vs slap 82.783 s. 263.40 s, 209.4 MB. Thumbnail unchanged.
- Chapters v2: 00:00 intro · 00:01 Season One · 00:03 The Daily Log · 00:24 The Webhook · 00:46 Holodeck Program 01 · 01:07 The Red Shirts · 01:30 Merge Conflict · 01:53 Ship It Friday · 02:12 Prompt Injection · 02:34 Hallucination · 02:55 Technical Debt · 03:16 CAPTCHA · 03:38 Context Window · 03:58 Rate Limited · 04:20 sting.
- URL: https://content.natehaskins.com/videos/voices/starship-grokbot-season1-v2.mp4

- 2026-10-11 01:34 CT: Season One wrap. Nathan usage at ~60% after the full session (12 shorts + fixes + compilations). Compilation/revision passes cost ~1%; a new short ~2%. Resume tomorrow; next-batch episode ideas not yet written.

## Rig additions: "Thinking with AI" cover characters (2026-10-11, test only; nothing uploaded)
- New OPT-IN options in `titan-hello-world/stick-poc/stickfig.py`. Defaults are unchanged: the default draw path makes exactly the same calls, verified bit-identical vs the pre-change code on Rate Limited 9.5/16.9 s, Red Shirts 13.5 s and Context Window 6.4/14.0 s.
  - Body styles via props: `boxbot` (oblique 3D box torso + cube head with side/top faces, short double-stroke neck, face on the front face, limbs rooted on the box; proportions in `Figure.BOX`) and `bean` (puffy kidney-shaped torso outline around the spine, flatter on the front side; limbs rooted on the bean). Draw order for both: legs → body → arms → head.
  - Accessories: `antenna` (boxbot: stalk + outlined ball, wiggle amplitude via pose key `antamp`, default 7°, and offset `antw`), `tuft` (hair curl), `bowtie`, `feet` (short splayed stick feet), `shoes` (oval shoes).
  - Poses: `think` (near hand at the chin, far hand on the hip) and `kneeup` (near knee lifted mid-step).
  - `Figure(..., seg={...})` per-figure segment-length overrides (default: the shared SEG). Font key `'serif'` = Crimson Text Regular (cover lettering).
- `inkset.thoughtcloud(pen, c, rx, ry, t, sid, n, w, puffs=((x, y, r),), dip, boil)`: a bumpy hand-scribbled cloud of n outward lobes, paper-filled (sits behind figures), with optional small thought circles.
- Test: `/workspace/holodeck/cover-chars/cover.py` → `thinking-with-ai-cover-test.mp4` (8.5 s, 1080p24, silent AAC): per-element pen-sweep draw-in (0-2.8 s, layered compositing with a key-colour coverage pass so paper fills still occlude), idle (chin taps, robot lean/bob, antenna wiggle, knee step, cloud boil), then a settle on the cover pose by 7.3 s and a hold. `compare.png` = original doodle vs the final frame.
- Found while verifying: `sets.burst` seeds with Python `hash(sid)`, which is salted per process, so burst frames (e.g. Context Window's BONK) are not bit-reproducible across runs. Pre-existing; not changed.

### Rig movement test — cover characters (2026-10-11, test only, not uploaded)
- /workspace/holodeck/cover-chars/rig-test.mp4 (10.0 s, 1080p24, silent AAC) + rig-test-sheet.png; script rig_test.py.
- New technique (in the scene script, not stickfig): planted-foot gait = fixed footfalls indexed by hip progress
  (stance foot pinned, swing foot arcs) + 2-bone leg IK from the exact rig leg roots (replicates _draw lean/breathing).
  `rig_test.py --feet` measures stance drift: robot 0 px, human <=0.1 px/frame, <=1.4 px off floor.
  Rule: hip height must be < leg reach minus ~half-stride or IK runs out and the foot hovers (robot needed hip = floor-138).
- Arm IK (flip=True elbow branch) puts the bean's hand on the chin for 'think'; pose-only angles stopped at mid-chest.
- stickfig: boxbot now opens an outlined/filled oval mouth when P['talk'] > 0.06 (boxbot-only path; defaults untouched).
- v2 (rig-test-v2.mp4 + rig-test-v2-sheet.png; `rig_test.py --v2`): Nathan saw a "cloud" around the robot's head. Nothing
  was drawn there (robot-only vs no-robot diff = 0 px outside strokes; no transient frames; no encoder halo). It was
  inkset.paper_finish's static low-frequency mottle (`low * 3`, 34x60 noise upscaled -> 30-60 px blotches, ~7.5 grey
  levels p2p), fixed in screen space, so the head walked/pushed through blotches = cloudy halo on open paper.
  v2 uses a local paper_finish_clean() without the mottle (same RNG order: identical fine grain/fibres/vignette).
  Consider dropping/reducing `low` in inkset.paper_finish for future shots (would change existing episodes, so not done).

### Cover robot as Grok Bot: "Welcome to Starship Grokbot" (2026-10-11, local rig test)
- https://content.natehaskins.com/videos/tests/cover-chars/robot-welcome.mp4 (8.0 s, 1080p24, 8.0 MB). Box: cover-chars/robot-welcome.mp4 + -sheet.png; script robot_welcome.py, audio cover-chars/welcome/.
- Voice: Chatterbox, cast grokbot-ref, exag 0.8 / cfg 0.4, TTS text "Welcome to Starship Grock Bott.", 3 seeds, BelowNormal, one job.
  s1/s2 dropped "Welcome to" (s2 "Grok-Buh!" -> "Rock much" after FX); **s3 used**: whisper "Welcome to Starship Grokbot!" dry and after robot.sh; F1 689 Hz (open /a/ = "bot").
  PRONUNCIATION: "Grock Bott" also works for Grok Bot's own voice (1/3 full takes; the failures were truncations, not "boat").
- Fake depth = tracking camera: solve cam so the hip's floor point lands on a screen path (y 600 -> 975) while zoom 0.42 -> 1.0;
  feet stay planted in world (gait + IK from rig_test). 2/3 shot = zoom 1.96 centred mid cube-top..hip (head+torso 67-68% of height).
- Rough: the robot walks in 3/4 profile (rig can't face camera), so "toward camera" is a diagonal approach plus zoom; the far arm shows through the box (outline-only).

## demo13: THINKING PARTNER (2026-10-11): book x series pilot
- URLs: https://content.natehaskins.com/videos/voices/thinkingpartner.mp4 (24.27 s, 28 MB) | thinkingpartner-branded.mp4 (29.29 s, 81 MB) | images/voices/thinkingpartner-thumb.jpg
- Plan of record: /workspace/holodeck/storyboards/thinking-with-ai-pilot/STORYBOARD.md (storyboard approval skipped per Nathan; no per-shot stills).
- Script: r1 RIKER "Welcome aboard. Grok Bot, give our guest whatever answer he needs." / t1 THINKER "Thank you. So, what is the meaning of life?" /
  g1 GROK BOT "Great question. What do you think it is?" / t2 THINKER "Hmm, maybe it's about asking better questions." /
  r2 RIKER "My turn. Grok Bot, what is the meaning of life?" / g2 GROK BOT "Great question, Commander. What do you think it is?" / button: Riker's thought cloud = trombone (2/3 punch-in, about 1.9 s on screen).
- NEW VOICE: Thinker = Kokoro am_adam .5 + bm_fable .5, speed .95 (6 blends of the unused am_echo/am_adam/bm_fable; E had the most F0 movement) -> cast\thinker.json + thinker-ref.wav (box copy voices/cast/).
- Takes: r1-s1, t1-s3, g1-s3, t2-s3, r2-s3, g2-s3. Riker "Grock Bott" -> whisper "Grokbot" (F1 755-780 Hz, F2 rising); r2-s1 gave "Grotbot" (rejected).
  Grok Bot dropped "Great question" in 4/6 takes (Chatterbox front truncation on the robot ref; same as the welcome test), so keep 3 seeds minimum and check that the transcript is complete.
- Rig: cover duo at 0.66x rig scale = Riker's height; hop off the book (scale 0.30 -> 0.66 + arc); Thinker chin-think via arm IK (rig_test.ik flip). Paper = no-mottle finish.
- SFX (add_sfx.sh): hop whooshes + landing pops, counter ticks, bulb ding, pop + trombone "wah-wah". First pass peaked at -16.6 LUFS M (too hot); final volume -10 dB = -20.6 M.

### Box-only hello test: "Hello, Starship Grok Bot." with Piper (2026-10-11)
- No PC/GPU used: voice = Piper en_US-ryan-low on the box CPU (/workspace/holodeck/piper/.venv) + voices/robot.sh (same FX as grokbot-hello-ryan-robotfx). Render on the box (~16 s).
- TTS text "Hello, Starship Grock Bott." (captions "Hello, Starship Grok Bot."). Piper is stochastic (noise), so 5 takes: whisper heard "Grokbot" 4/5 dry and 4/5 after FX (length-scale 1.1 gave "Crockbot"; the plain "Grok Bot" spelling also passed once). Used take h1b: vowelcheck after FX F1 758 Hz, no F2 glide (= "bot"); still "Grokbot", F1 767 in the final mux. Earlier single take h1 lost the G after FX ("Rockbot"), so check each FX take.
- Line gained +4.8 dB with a limiter (robot.sh's single-pass loudnorm leaves short lines at about -20 LUFS); final file -16.6 LUFS.
- Renderer cover-chars/robot_hello.py = robot_welcome.py fork + poster frame 0 (mid-wave full figure, title "HELLO, STARSHIP GROKBOT" at the top) + 0.5 s hold + ink wipe (demo13 recipe); audio in cover-chars/hello/ (build_audio.py, takes h*.wav, timeline.json, captions.ass). No intro or sting.
- Files: cover-chars/robot-hello-starship.mp4 (8.30 s, 7.7 MB), robot-hello-thumb.jpg; contact sheet hello/contact-final.png.
- URLs: https://content.natehaskins.com/videos/voices/robot-hello-starship-ryan.mp4 · https://content.natehaskins.com/videos/voices/robot-hello-starship-ryan-thumb.jpg
- PITFALL: curl-checking a key BEFORE upload makes Cloudflare cache the 404 (cf-cache-status HIT). The keys robot-hello-starship-piper(.mp4|-thumb.jpg) were uploaded but still return a cached 404, so don't use them. Don't pre-probe new keys.

### Hello test v2: series stick-figure Grok Bot (2026-10-11, box only)
- Nathan wanted the series Grok Bot (stickfig `robot` prop, standard SEG, scale 2.0), not the cover boxbot, and the full episode voice chain.
- Voice chain = exactly what episodes do for Grok Bot: `voices/finalize.sh <in> <out> robot` (silence trim → robot.sh → 192k mono mp3). v1 had skipped the trim and mp3 steps; the FX filter itself is identical (cast/grokbot.json robot_filter == robot.sh). The base voice is still Piper en_US-ryan-low take h1b (TTS "Hello, Starship Grock Bott."), not Kokoro am_puck/Chatterbox. Then +4.6 dB with a limiter. After the chain, whisper heard "Hello, Starship Grokbot."; vowelcheck F1 790 Hz (= bot). Final mux: F1 755 Hz, G kept. Other takes through the same chain all heard "Grokbot"; h1a was the cleanest (F1 721, F2 flat) if a swap is wanted.
- Renderer cover-chars/robot_hello2.py: planted-foot gait IK (rig_test.Gait with a standard-rig leg_roots = hip point, hip = floor-104*S), walks in profile, turns to `front` at the stop, front wave, LED-grill lip-sync + onset head bobs, 2/3 shot zoom 1.88 (antenna..mid-thigh ≈ 720 px), grin hold. Poster credit "STARSHIP GROKBOT · Grok Bot says hello". build_audio fix: a whisper word with zero length ("Starship") gets re-started after the previous word.
- Files: cover-chars/grokbot-hello-starship.mp4 (8.30 s, 8.5 MB, -17.0 LUFS), grokbot-hello-thumb.jpg, hello2/ (audio, contact-final.png).
- URLs: https://content.natehaskins.com/videos/voices/grokbot-hello-starship-stick.mp4 · https://content.natehaskins.com/videos/voices/grokbot-hello-starship-stick-thumb.jpg

### Hello v3: expanded dialogue (2026-10-11, box only)
- Same build as v2 (series stick Grok Bot, walk in → turn → wave → 2/3 push, poster frame 0 + ink wipe, karaoke captions), now with 5 lines: "Hello from Starship Grok Bot." / "Nice to meet you." / "I'm here to help you get things done alongside the crew." / "Starship Grok Bot, here to help." / "Thanks!"
- Voice: Piper en_US-ryan-low, TTS text uses "Grock Bott"; 4 takes per sentence, each through the episode chain (voices/finalize.sh robot). Whisper + vowelcheck: s1 3/4 "Grokbot" (s1a → "Crock-Pot", G lost); s4 3/4 (s4c "Crock-Pot", s4a dropped "Starship"). Picked s1c (F1 725, F2 flat −12), s2a, s3a, s4d (F1 735, F2 −24), s5a ("Thanks!"). Gaps .35/.30/.45/.35, tail 1.3 s. Whole mix normalized to −16 LUFS (measure + gain + limiter); final file −16.1 LUFS, −1.5 dBFS. Whisper on the final: both "Grokbot", full text correct.
- Gestures (front mode): open hand (l1), both palms (l2), forearm across chest on "I'm" → open offer on "help" → arm sweep on "alongside the crew" (l3), salute on "Starship" → hands-up ta-da on "here to help" (l4), small wave (wave=.6) on "Thanks!", grin hold. Sentence-start nods + RMS head bobs; LED grill lip-sync. NOTE: in front mode the `hips` and `thumb` poses read badly (arms cross at the waist / thumb points sideways); use rel=-118 for hand-to-chest, rsh=150 rel=-110 for salute.
- build_audio splits whisper's one-word "Grokbot" into the captions' "Grok"/"Bot" timing.
- Files: cover-chars/robot_hello3.py, hello3/ (takes/, build_audio.py, timeline.json, mix.wav, contact-final.png), grokbot-hello-starship-v3.mp4 (15.96 s, 14.9 MB), grokbot-hello3-thumb.jpg.
- URLs: https://content.natehaskins.com/videos/voices/grokbot-hello-starship-stick-v3.mp4 · https://content.natehaskins.com/videos/voices/grokbot-hello-starship-stick-v3-thumb.jpg

## demo12-local: "RATE LIMITED" box-only remake, Piper voices (2026-10-11)
- Test: the whole episode with NO PC/GPU and no remote APIs; the only network use was the Piper model downloads from huggingface.co/rhasspy/piper-voices plus the R2 upload. Renderer = demo12 v3 ratelimited.py unchanged (copy: voices/demo12-local/ratelimited_local.py), so the same cues, shots, facepalm punch-in and poster.
- Downloaded into holodeck/piper/: en_GB-alan-medium, en_GB-northern_english_male-medium, en_GB-semaine-medium, en_US-joe-medium, en_US-john-medium, en_US-hfc_male-medium, en_US-bryce-medium (auditions in demo12-local/aud/).
- Cast: GROK BOT = en_US-ryan-low + finalize.sh robot (episode chain; dry F0 ~170 Hz); PICARD = en_GB-alan-medium (British, F0 ~95 Hz); RIKER = en_US-hfc_male-medium (American, F0 ~130 Hz). Rejected: northern_english_male ("rice star"), semaine spike/obadiah ("rice sour"/"rice sah"), joe ("saying it's lower"), john/bryce (slower or too bright).
- Takes (4 each, whisper-checked): p1d "Set a course for Rye-sa, and make it so." (4/4 /aI/ via vowelcheck --after for, F1 pk 778, F2 1009→1592; whisper "Reissar", same as the GPU take); g1b; p2 = 3 separate sentences (xa, yb, zd) joined with 0.22/0.18 s gaps and escalated (+4%/+8% asetrate pitch/speed, +2.5/+4.5 dB) because Piper has no emotion control (p2zc dropped "so", rejected); r1d; g2b (g2a was heard as "Rate limit received", rejected). Grok Bot lines don't say "Grok Bot" or "warp". Each line gain-normalized to −16 LUFS (single-pass loudnorm left the short lines at −17 to −22).
- Timeline: same gaps as v3 (.2/.4/.3/.3/1.75, tail 1.8); scene 19.74 s; facepalm close-up hold 13.13→14.71 = 1.58 s (v3: 1.36). Episode 20.25 s (−16.3 LUFS), branded 25.26 s (make_branded.sh, poster ~1.5 s, frame 0 = intro logo verified).
- URLs: https://content.natehaskins.com/videos/voices/ratelimited-local-piper.mp4 · …/ratelimited-local-piper-branded.mp4 · https://content.natehaskins.com/images/voices/ratelimited-local-piper-thumb.jpg
- Cost/time: about 0 GPU and no Nathan usage for voices; ~25 s render on the box, ~15 min total.

## demo14: "THE STANDUP" (2026-10-11), box-only (Piper voices, no PC/GPU, no remote APIs)
- Idea #4 plus the over-chatty agent. Storyboard: /workspace/holodeck/storyboards/the-standup/STORYBOARD.md. Renderer voices/demo14/standup.py (bridge set, built on the Rate Limited structure; no-mottle paper), sfx.py (numpy-synthesized SFX), build_audio.py.
- Script: p1 PICARD "Quick standup, everyone. Fifteen minutes, tops." / r1 RIKER "Nothing blocking me. Grok Bot, you're up." / g1 GROK "Status update. Subtask one, I opened a file. Subtask two, I read the file." / g2 GROK "Subtask three, I closed the file. Subtask four, I opened it again." / [2/3 punch-in on Riker: floor-length beard, looks down, bird pops out "tweet!", 1.55 s] / p2 PICARD "Grok Bot, please, just the summary." / g3 GROK "Of course. Summary, part one of forty thousand." / button: clock springs off the wall (BOING), Picard faints (THUD), "STANDUP: DAY 92" stamp.
- Voices (Piper): Picard en_GB-alan-medium (+atempo 1.08), Riker en_US-hfc_male-medium, Grok Bot en_US-ryan-low + finalize.sh robot (g1/g2 length-scale .85). Takes p1e, r1a, g1e, g2g, p2f, g3b (4-8 takes per line, whisper-checked). "Grock Bott": Riker r1a F1 678 / F2 flat, heard "Grokbot" (r1b gave "Rockbot", rejected); Picard p2f F1 641 / F2 drop 82 after atempo (borderline on F2, but heard as "Grokbot"). Most g1 takes said "I open the file"; g1e was word-correct.
- Visual system: elapsed time = real-time until the first "Subtask", then exp(1.45 u) to ~90 days at the punch-in, then a steady absurd rate. The clock hands give way to a blur disc + speed arcs past 40°/frame; viewscreen DAILY STANDUP / STARDATE (+elapsed/525.6) / ELAPSED (min → hours → days → weeks) / SUBTASKS REPORTED n of 48,112, then SUMMARY PART 1 / 40,000; calendar months flip and pages fly; the report scroll piles in zigzag folds between Picard and Grok Bot; beards grow on a log-time scale (Riker: ink outline + strands, so his body stays readable; Picard: white outline).
- SFX: real ticks (one per clock minute) → a click-train whirr once the rate passes 9 ticks/s (ducked under the punch-in), page swishes, bird chirp, BOING, THUD, stamp thump. Bus -11 dB: momentary max ticks -26.8, whirr -21.7, boing/thud -19.9 vs dialogue about -12. Final mix gain-normalized: -16.0 LUFS, -1.4 dBFS.
- Durations: scene 23.32 s; episode 23.83 s; branded 28.84 s (frame 0 = intro logo, verified).
- URLs: https://content.natehaskins.com/videos/voices/standup-local.mp4 · …/standup-local-branded.mp4 · https://content.natehaskins.com/images/voices/standup-local-thumb.jpg

### Brand: tagline removed from the logo card (2026-10-11)
- Nathan: drop "ink-on-paper adventures of a boxy little bot" from the STARSHIP GROKBOT card. Removed from brand/make_intro.py (frame-0 logo card; title + underline nudged down 25 px to 745/843 to balance the empty bottom) and make_sting.py (stamped title; layout unchanged). Logo, underline, ship and stars kept. Regenerated starship-grokbot-intro.mp4 (1.0 s, 24 frames) and starship-grokbot-sting.mp4 (3.0 s, 72 frames). Backups of the old scripts and mp4s: brand/backup-tagline/. NEW STANDARD for all branded builds (make_branded.sh picks them up automatically). The R2 copy of the intro at videos/brand/starship-grokbot-intro.mp4 was NOT updated (still has the tagline).
- Rebuilt THE STANDUP branded: voices/demo14/standup-branded-v2.mp4 (28.84 s, -16.1 LUFS). Verified frame 0 and sting frames (end-60/-40/-22/-12/-2): no tagline. Thumbnail unchanged (the episode poster never had the tagline).
- URL: https://content.natehaskins.com/videos/voices/standup-local-branded-v2.mp4

- 2026-10-11: Box-only Piper workflow (The Standup + branded rebuild) cost Nathan ~1% usage per episode, no GPU, no credits. Cheapest pipeline so far.

## demo15: "DARK MODE" (2026-10-11), box-only (Piper voices, no PC/GPU, no remote APIs except the HF model downloads and the R2 upload)
- Idea #7 + an untested theme toggle / contrast angle. Storyboard: /workspace/holodeck/storyboards/dark-mode/STORYBOARD.md. Files: voices/demo15/{darkmode.py, build_audio.py, sfx.py, takes/, aud/}.
- Script: b1 BARCLAY "I, I gave the bridge a dark mode. It's easier on the eyes!" / r1 RIKER "Barclay, I can't see anything. Where did everyone go?" / g1 GROK "Contrast ratio, one to one. Now adding alt text." / p1 PICARD "Mister Barclay. Turn it off. Now." / [flashbang + 2/3 punch-in on Picard shielding his eyes, ~1.7 s] / g2 GROK "Light mode restored. Brightness, one hundred and ten percent." + shades.
- Barclay voice: auditioned (downloaded) en_US-kusal/mike/sam-medium + danny-low, plus bryce/john. Picked **en_US-bryce-medium** at length-scale .85: highest and most animated (F0 ~149 Hz, sd 59 vs Riker ~131 / Picard ~95); sam was too close to Riker (132 Hz), kusal heard "I" as "Aye", mike/john were flat. Takes: b1a, r1b, g1 = "Now adding alt text" variant gv2a (the original "Adding alt text" was heard as "adding all text" / "angle to text" and, in the full mix, "hanging off text"; "Now adding alt text" was 3/3 correct), p1a (atempo 1.05), g2c. No line has "Grok Bot" or "warp".
- Dark-mode rendering: the whole frame is INK; figures/set are skipped; only SETS.outlined text is drawn (hollow paper outlines). Fluorescent flicker on the switch (2 light frames), flashbang = white-out that decays over 0.7 s after the finish. Captions stay legible on black (ink fill + paper outline + grey karaoke fill).
- build_audio: when whisper's word count differs from the script, it falls back to script words spread over whisper's span (keeps "I, I").
- SFX (numpy): switch clicks, flicker buzz, BONK knock, 6 label pops, flashbang noise + whistle + sizzle crackle, shades "ting". Bus -15 dB (momentary max -19.7 vs dialogue about -12). Final -16.0 LUFS, -3.6 dBFS. Whisper on the final mix (vad, no context): all 5 lines word-correct ("I-I", "110%").
- Durations: scene 22.0 s; episode 22.50 s; branded 27.51 s (new tagline-free intro/sting; frame 0 = intro logo card).
- URLs: https://content.natehaskins.com/videos/voices/darkmode-local.mp4 · …/darkmode-local-branded.mp4 · https://content.natehaskins.com/images/voices/darkmode-local-thumb.jpg (box: voices/demo15/darkmode-thumb.jpg)
- All 10 style-guide episode ideas are now done.

## Season One compilation v3 (full series, 2026-10-11)
- `/workspace/holodeck/season1/starship-grokbot-season1-v3.mp4` -> https://content.natehaskins.com/videos/voices/starship-grokbot-season1-v3.mp4 (thumb: ...-v3-thumb.jpg, 5x3 poster grid, 14 eps)
- Same build as v2 (build_season.py: per-segment gain to -16 LUFS, limiter, 2-pass H.264, poster holds +1.2 s, 2.5 s SEASON ONE card) + demo14 The Standup + demo15 Dark Mode (plain), new tagline-free intro/sting. Chapters: season1/chapters_v3.json.
- 312.1 s, 1080p24, integrated -16.1 LUFS. Box-only. No Thinking-with-AI material (no Thinking Partner, no cover-chars hello tests).
- 2026-10-11: Season One v3 compilation (14 eps, box-only) cost ~1% usage.
