# Holodeck Shorts: Series Style Guide
*Stick-figure Trek comedy for the U.S.S. Titan crew. Made by Lt. Barclay (Grok Bot's movie pipeline) for Nathan.*

## The look
- **Ink on paper, strictly monochrome:** ink `RGB(20,22,26)` on off-white paper `RGB(243,238,230)`. Screens are solid ink with paper strokes. No colour and no gradients.
- **Line boil:** every stroke wobbles and re-seeds 12×/s, like redrawn-on-twos animation. Anti-aliased lines, round-ish 5–8 px.
- **Finish:** paper grain plus fibre texture (4 layers cycled at 12 fps) and a soft vignette.
- **Hand-lettering:** Permanent Marker for titles, stamps and labels; Patrick Hand for UI text and notes. Captions use Exo 2 Bold with a paper outline.
- **Doodled graphics carry the jokes:** checkmarks, stamps, counters, bells, bolts, sweat drops, "!", music notes and speed lines.

## Cast
| Character | Look | Voice (local: Kokoro design → Chatterbox performance) | Comic role |
|---|---|---|---|
| **Captain** | Peaked cap, badge; usually in the chair | Kokoro `am_onyx .5 + bm_lewis .3 + am_fenrir .2`, speed .88; deep, ~97 Hz | Calm authority, "Engage!" |
| **Riker** | Beard (visible even from behind), badge; sits on chairs backwards | `am_fenrir .5 + am_michael .3 + am_puck .2`, speed 1.0; warm, smirking | Charming instigator; deadpan reactions; beard-stroke |
| **Picard** | Bald head with shine, collar, badge. Seen on the viewscreen behind a desk with "ADM. PICARD // U.S.S. ENTERPRISE", plus tea | British (`lang b`): `bm_lewis .5 + bm_george .3 + bm_daniel .2`, speed .88; ~122 Hz, measured | The long-suffering grown-up; facepalms; final verdict |
| **Grok Bot** | Boxy head, antenna ball, square eyes. Grill mouth that becomes an LED level meter when he talks | `am_puck`, speed 1.1, then robot FX (110 Hz ring-mod, fifth-up layer, flanger, 9-bit crush) | Hyper-literal and over-productive; ships it, retries it, wants screen time |
| **Ensign** | Ponytail, badge; at OPS | (not voiced yet) | Eager background crew |
| **Lt. Barclay** | Curly scribble hair, hunched nervous posture, PADD + stylus, sweat drop when anxious. "LT. BARCLAY // HOLODECK" | American: `am_liam .5 + am_eric .5`, speed 1.1; ~144 Hz, quick and earnest. Stammer is written into the script as commas ("I, I'd…") | The nervous creator; defends his art; faints from joy |
| **Ens. Red Shirt** (#46, #47, …) | Solid ink-filled tunic (ink can't do red) with a paper delta badge. Arms get a paper halo so they read over the tunic. Name plate "ENS. RED SHIRT #46 // JOBS" plus a wall generation counter | Kokoro `af_heart .5 + af_bella .5`, speed 1.1; ~211 Hz, bright and eager (the cast's only higher voice). Chatterbox 0.7/0.45, excited 0.8/0.4, then atempo 1.08 | The cheerful, expendable bot. Loads huge context, gets DELETE & RECREATE'd (a transporter shimmer, never a death), and the next generation beams in asking what it missed |
| **Daimon Grubb // Ferengi** (non-canon) | Huge fan ears (smoothed ink shapes), bald with three forehead ridges, sly grin; drawn in paper ink on the black viewscreen. Gold bars on his desk, plus a "TRADE AGREEMENT" card | Kokoro `am_santa .4 + am_eric .3 + am_liam .3`, speed 1.08; ~155 Hz, nasal and bright. Chatterbox 0.7/0.4 | The hailing trader. Hides prompt injections in the fine print, and gives up hiding them when caught |
| **The Thinker** (from the "Thinking with AI" cover) | Cover human: `bean` body, hair tuft, bow tie, shoes; chin-think pose with arm IK; appears with Grok Bot's "book edition" (cover robot: `boxbot` + antenna) | Kokoro `am_adam .5 + bm_fable .5`, speed .95; ~117 Hz, warm and curious. Chatterbox 0.6/0.5 | The everyman who asks; reaches the insight himself while Grok Bot answers with a better question |

## Sets
- **Titan bridge:** viewscreen 700×360 with mini-content, OPS/HELM/SCI consoles, PWR gauge, station minis, rail and the "U.S.S. TITAN" sign.
- **Enterprise-D viewscreen (full frame):** an ink screen in a paper margin, kept above the caption band. Picard at his desk, a notification or review panel on the right, and a counter badge.
- **Holodeck:** a perspective grid on paper, the arch, and floating program windows.
- **Song sets:** warp sky, chorus line, disco, poker, planet away-mission, sunrise lineup and the end card.

## Format rules
- **Format:** 1920×1080 at 24 fps. Shorts run ≤ ~20 s, made of 5–6 full-sentence lines across 2–4 speakers.
- **Frame 0 is the poster:** key art plus an outlined title and a small credit line. Hold it 0.5 s, then a dry-brush ink wipe. Never start on blank paper or black. Always export `thumbnail.jpg` and upload it.
- **Captions and lip-sync:** karaoke `\kf` captions (word times from faster-whisper) with the speaker's name above in marker font. Mouths follow the per-frame RMS of the voice, with head bobs on syllable onsets and listener nods.
- **Audio:** dialogue only, loudness-normalised to −16 LUFS, over a very quiet 55/110 Hz hum plus brown-noise air. Gaps between lines are 0.25–0.6 s.
- **Brand sting (every short):** end on the 3.0 s "STARSHIP GROKBOT" sting. Ink draws a starship with Grok Bot's head as the bridge; it zips off with a whoosh, and the title stamps in with an ink splat and a ding before fading back to paper. It lives at `/workspace/holodeck/brand/starship-grokbot-sting.mp4` (generator `make_sting.py`). Publish `<name>-branded.mp4` = **intro + episode + sting** (see the intro bumper rule below), re-encoded to AAC stereo 48 kHz.
- **No tagline (since 2026-10-11):** the STARSHIP GROKBOT logo card (intro frame 0 and the end sting) shows only the logo, underline, ship and stars. The "ink-on-paper adventures of a boxy little bot" subtitle was removed; intro title/underline moved down 25 px. Old assets are in `brand/backup-tagline/`.
- **Credit line (since 2026-10-13):** the intro card shows "by Grok Bot & Nate Haskins" (Patrick Hand, 46 px, y=905) under the underline. The pre-credit intro is in `brand/backup-tagline/starship-grokbot-intro-nocredit.mp4`.
- **Intro bumper (every branded short, since demo8):** open on the 1.0 s (exactly 24 frames) "STARSHIP GROKBOT" intro, `/workspace/holodeck/brand/starship-grokbot-intro.mp4` (generator `make_intro.py`, R2 `videos/brand/starship-grokbot-intro.mp4`). Frame 0 is the finished logo card (saluting Grok-Bot-head starship, hand-lettered title, doodled frame and stars), and it is the social preview. The ship zips off with speed lines and a whoosh, a tiny splat lands with a ding, and a fast ink wipe ends on solid ink. Branded order (since 2026-10-11): intro (1.0 s) → episode with its poster frame frozen +1.0 s (`tpad=start_mode=clone` as the FIRST filter on the episode video, with the audio `adelay`ed by the same amount, so the poster holds about 1.5 s and the scene audio still starts with the scene) → 3.0 s sting. Build with `/workspace/holodeck/brand/make_branded.sh ep.mp4 out.mp4 [extra=1.0]`. Older branded files used `-ss 0.2` (0.3 s hold), which turned out to be too fast to read the title. The plain `<name>.mp4` stays poster-first with no intro or sting, and the episode poster is still exported as `<name>-thumb.jpg` for manual covers. Verify that frame 0 of the branded file is the intro logo card.
- **Delivery:** a LinkedIn-safe mp4 with one H.264 stream plus AAC, `+faststart`, and no attached cover. Check frame 0 and a contact sheet before uploading. Use a new R2 key for every revision.

## Box-only voices (Piper, no GPU)
- Cast (since 2026-10-11): Grok Bot `en_US-ryan-low` (length-scale .85 for rapid chatter) + `finalize.sh robot`; Picard `en_GB-alan-medium` (atempo 1.08); Riker `en_US-hfc_male-medium`; Barclay `en_US-bryce-medium` (length-scale .85). Models live in `/workspace/holodeck/piper/` (from huggingface.co/rhasspy/piper-voices).
- Piper is stochastic: render 4+ takes per line, check them with whisper and `vowelcheck.py`, and gain-normalize each line to -16 LUFS (single-pass loudnorm leaves short lines at -17 to -22). Piper is flat, so carry the comedy with visuals, timing and SFX.

## Pronunciation rules (TTS text only; captions keep the real spelling)
- **"Grok Bot":** Chatterbox can say "Grok boat". For the **Captain**, write **"Grock Bott"** in the TTS text (3/3 takes heard as "bot", vowel F1 about 670-714 Hz with no glide). "Grockbot" is the runner-up. "Grok, Bot" also works but adds a pause. Avoid "Grahk-bot" and "Grok bawt" (each gave one "boat"), and "Grok Baht" (heard as "Grotbot"). The captions come from the `LINES` text, so keep "Grok Bot" there and put the phonetic spelling only in the Chatterbox job text.
- **Other voices:** for Riker, Picard, Barclay, Red Shirt and Ferengi, start with "Grock Bott". Check every take with `voices/vowelcheck.py`: whisper should hear "bot", and the second word's vowel should have F1 above about 600 Hz and an F2 drop under 50 Hz. A "boat" sounds like F1 about 450 Hz with F2 falling.
- **"Risa" (RISE-uh):** Chatterbox (Picard) says "REE-sa". Write **"Rye-sa"** in the TTS text: 3/3 takes have the /aI/ F1 peak (600-660 Hz), and whisper hears "Reiser". Avoid "Rise-uh" (it splits into "Rise, uh"), "Rise a" (heard as the letter A), and "Rysa"/"Ryza" (only 1/3 each). Check with `vowelcheck.py --after for`: /aI/ gives an F1 peak above 550 Hz and F2 rising; /i:/ (the bad one) gives F1 around 250 Hz. General tip: spell names phonetically with an English word inside ("Rye", "Bott").
- **Grok Bot's own voice:** keep "warp" out of his lines (it comes out as "war core").

## Reaction gags
- **Big reaction gags** (facepalms, sweat drops, faints, spit-takes) get a **punch-in close-up with the character filling about 2/3 of the frame height**, plus a **hold of about 1.2-1.5 s** on the finished pose (0.76 s read as too quick; RATE LIMITED v3 holds 1.36 s) before the next line. Add a slow push (about 3%) during the hold. Cut on the end of the line that triggers it and budget the hold into the gap before the next line. Keep the figure above the caption band. First used in RATE LIMITED v2/v3 (Picard facepalm).
- **Physical gags get a sound effect:** button slaps, beam-outs, bonks and stamps get a short ffmpeg-synthesized SFX (no copyrighted audio), aligned to the frame and kept about 7 LU under the dialogue (momentary max around -20 LUFS vs dialogue around -14). Example: `voices/demo4/add_sfx.sh` (clunk + transporter shimmer).

## Comedy formula (what has landed)
**Tech joke + Trek trope + an on-screen doodled graphic + an escalating counter + a one-line punchline + a visual button after the last line.**
- *The Daily Log:* the stats row ends on "300 bugs created", then the PERFECTLY BALANCED stamp, then REDACTED.
- *The Webhook:* the notification feed runs from 1 to 400 to 9999+, Picard facepalms, Grok Bot replies with "exponential backoff", and an avalanche of alerts buries Picard.
- Keep it good-natured. Picard is exasperated, never mean, and everyone is competent but a bit ridiculous.

## Pipeline, cost and time
1. Write the script (full sentences, no one-word lines).
2. Design any new voice with Kokoro: 6 blends, picked by transcript and pitch. Save `cast/<name>.json` and `-ref.wav`.
3. Perform each line with Chatterbox, 3 seeds per line, on Nathan's PC (BelowNormal priority, one job at a time). About 1 minute of GPU time.
4. On the box: run `finalize.sh` (plus the robot FX for Grok Bot), then `build_audio.py`, which writes the timeline, word times and RMS envelope, and the mix.
5. Write the cue table in `<episode>.py`, check frames with `chk.sh`, render in 6 parallel parts (~25 s), burn the captions, mux the audio, and check the contact sheet.
- **Cost:** about 2% of Nathan's usage per short and about 3% for a full 3-minute song video. No Imagine credits.
- **Time:** about 30–45 min per short, including script and checks.

## 10 episode ideas
1. **Merge Conflict:** Riker and Grok Bot both edit the Captain's log; it diffs into chaos and Picard picks "theirs".
2. **Ship It Friday:** a 4:59 pm deploy to the warp core; the counter is "minutes until weekend".
3. **Prompt Injection:** a Ferengi hides "ignore previous orders, sell the ship" in a hail; Grok Bot almost complies.
4. **The Standup:** a 15-minute meeting that lasts a stardate; the clock spins out of control. **DONE (demo14, 2026-10-11, box-only Piper voices):** Grok Bot reports every subtask; clock blur + BOING, stardate climbs, calendar pages fly, Riker's beard reaches the floor (punch-in + bird), Picard faints. `voices/demo14/standup.py`, R2 `videos/voices/standup-local(-branded).mp4`.
5. **Hallucination:** Grok Bot confidently reports a nebula that isn't there, and Barclay's holodeck makes it real.
6. **Rate Limited:** Picard's "Make it so" returns 429; "Make it so" goes into a retry queue.
7. **Dark Mode:** Barclay switches the series to ink-on-black; everyone vanishes, and only the outlined text survives. **DONE (demo15, 2026-10-11, box-only Piper):** an untested theme toggle; contrast ratio 1:1; Grok Bot adds outlined alt-text labels; the switch back is a flashbang (Picard punch-in); Grok Bot puts on shades at BRIGHTNESS 110%. `voices/demo15/darkmode.py`, R2 `videos/voices/darkmode-local(-branded).mp4`.
8. **Technical Debt:** Riker's IOU stack of "deals" towers over the bridge until the Captain asks for a refactor.
9. **CAPTCHA:** the Enterprise-D asks the Titan to prove it isn't a robot; Grok Bot fails, and Riker passes by sitting backwards.
10. **Context Window:** Grok Bot forgets the start of the mission at the end of a long briefing; Barclay draws him a bigger head.
