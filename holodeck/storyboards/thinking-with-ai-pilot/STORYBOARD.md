# THINKING PARTNER: storyboard (plan of record)
Starship Grokbot pilot that bridges the "Thinking with AI" book and the series. Slug: `thinkingpartner` (demo13). Local pipeline only (rig on box + Chatterbox on Nathan's GPU). No Grok Imagine or API.

**Logline:** The two doodles from the "Thinking with AI" cover hop out of the book onto the Titan bridge. The human asks Grok Bot the meaning of life, and Grok Bot only ever answers with a better question. It works on the human. On Riker, it works a little too well.
**Alt premise (not used):** "Answer Machine": Riker installs an ANSWER button on Grok Bot, and every press returns a question until the Captain asks for a refund.

## Cast + voices
| Who | Look (rig) | Voice |
|---|---|---|
| **The Thinker** (new) | Cover human: `bean` body, tuft, bow tie, shoes; `think` pose | NEW: Kokoro design (am_echo / am_adam / bm_fable blends, warm, curious, thoughtful everyman) → `cast\thinker.json` + `thinker-ref.wav`, then Chatterbox |
| **Grok Bot (book edition)** | Cover robot: `boxbot` + antenna + feet, talking mouth | Existing `grokbot` ref + robot FX (no "warp") |
| **Riker** | Series Riker (beard, badge) | Existing `riker` ref; says "Grock Bott" in TTS text |

## Script (6 lines; gaps 0.25-0.6 s, with the punch-in hold budgeted at the end)
1. RIKER: "Welcome aboard. Grok Bot, give our guest whatever answer he needs."
2. THINKER: "Thank you. So, what is the meaning of life?"
3. GROK BOT: "Great question. What do you think it is?"
4. THINKER: "Hmm. Maybe it's about asking better questions."
5. RIKER: "My turn. Grok Bot, what is the meaning of life?"
6. GROK BOT: "Great question, Commander. What do you think it is?"
Button: Riker's thought cloud pops up with a trombone doodle inside; 2/3 punch-in on Riker plus a beard-stroke, held about 1.3 s.

## Shots
| # | Time | Framing | Action | Line | Gags / screen | SFX |
|---|---|---|---|---|---|---|
| 1 | 0-0.5 (+1 s freeze when branded) | Wide bridge | POSTER: giant book "Thinking with AI" stands on deck with the duo drawn on its cover; title THINKING PARTNER outlined + credit | none | Viewscreen: "QUESTIONS ASKED 0 / ANSWERS GIVEN 0" | none |
| 2 | ~0.5-2.6 | Wide | Ink wipe; sparkles on the book; the duo hop out onto the deck one after the other; the book cover is left blank | none | Sparkles; the cover goes blank | Two pops + a soft whoosh |
| 3 | line 1 | Medium on Riker + duo | Riker walks in, gestures welcome | 1 | none | none |
| 4 | line 2 | Two-shot Thinker/Grok Bot | Thinker steps forward, palm up | 2 | Counter: QUESTIONS 1 | Tick |
| 5 | line 3 | Medium on Grok Bot | Points back at Thinker; antenna wiggle | 3 | QUESTIONS 2, ANSWERS still 0 | Tick |
| 6 | line 4 | Medium on Thinker | Chin-think pose; a thought cloud scribbles in above him with a lightbulb | 4 | Lightbulb + sparkle | Ding |
| 7 | line 5 | Wide 3-shot | Riker steps in, hands on hips | 5 | QUESTIONS 3 | Tick |
| 8 | line 6 | Medium on Grok Bot | Same gesture as shot 5 (callback) | 6 | QUESTIONS 4, ANSWERS 0 flashes | Tick |
| 9 | ~1.6 s button | 2/3 punch-in on Riker | His thought cloud pops up with a trombone doodle; beard-stroke; slow 3% push | none | Trombone in the cloud | Pop + low "wah" |

**Poster:** wide bridge with the giant book (duo on the cover, the thought cloud), title THINKING PARTNER in Permanent Marker, credit "a Starship Grokbot short // Thinking with AI". Thumbnail = poster.
**Branding:** plain = poster-first episode; branded = 1 s intro + episode (poster frozen +1 s, about 1.5 s total) + 3 s sting (`make_branded.sh`).
**Runtime:** episode about 22-26 s; branded about 27-31 s.
**Cost (local only):** about 2% of Nathan's usage, no Grok/Imagine credits. GPU: Kokoro design about 1 min, plus 18 Chatterbox takes about 1 min (BelowNormal, one job at a time). Box render about 1 min.
