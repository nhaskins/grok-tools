# THE STANDUP: storyboard (plan of record)
Style-guide idea #4 plus an AI angle: the over-chatty agent. Slug `standup` (demo14). **Box-only**: Piper voices on the box CPU, rig rendered on the box. No PC/GPU, no Grok Imagine or API.

**Logline:** Picard calls a 15-minute standup. Grok Bot gives a status update on every subtask he has ever run, and time-lapses the bridge into next season.

## Cast and voices (Piper, box CPU)
| Who | Rig | Voice |
|---|---|---|
| Picard | shine, badge, collar | en_GB-alan-medium, atempo 1.08 |
| Riker | beard, badge | en_US-hfc_male-medium |
| Grok Bot | robot | en_US-ryan-low (length-scale .85 on the chatter) + episode robot chain |

## Script (TTS text says "Grock Bott"; captions say "Grok Bot")
1. PICARD: "Quick standup, everyone. Fifteen minutes, tops."
2. RIKER: "Nothing blocking me. Grok Bot, you're up."
3. GROK BOT: "Status update. Subtask one, I opened a file. Subtask two, I read the file."
4. GROK BOT: "Subtask three, I closed the file. Subtask four, I opened it again."
   - 2/3 punch-in on Riker: his beard now reaches the floor; he looks down at it, and a doodle bird pops out ("tweet"). Held about 1.5 s.
5. PICARD: "Grok Bot, please, just the summary."
6. GROK BOT: "Of course. Summary, part one of forty thousand."
   - Button: the wall clock springs off the wall (BOING), Picard faints (thud), and a "STANDUP: DAY 92" stamp lands on the viewscreen.

## Visual system (the comedy is visual; the voices are flat)
- **Wall clock** (left wall, "TIMEBOX: 15 MIN"): real-time ticking, then exponential spin from Grok's first "Subtask", with motion blur and a shake.
- **Viewscreen:** DAILY STANDUP, then STARDATE (climbs with elapsed time: 1 unit = 525.6 min), ELAPSED (min → h → days → weeks), and SUBTASKS REPORTED n / 48,112. During line 6 it shows SUMMARY: PART 1 / 40,000.
- **Wall calendar** (right): months flip, pages fly off.
- **Grok Bot's report scroll:** a paper strip from his hand that piles on the floor and grows while he talks.
- **Beards:** Riker's grows to the floor (ink). Picard grows a white (outline) beard.

## Shots
| # | When | Framing |
|---|---|---|
| 0 | 0–0.5 s | POSTER: late-time wide (beards, scroll pile, spinning clock), title THE STANDUP, credit line |
| 1 | p1 | wide bridge, slow push |
| 2 | r1 | medium on Riker + Grok Bot |
| 3 | g1–g2 | medium on Grok Bot, pulls out to wide as the time-lapse kicks in |
| 4 | after g2 | 2/3 punch-in on Riker (beard + bird), hold about 1.5 s, 3% push |
| 5 | p2 | medium on Picard (white beard) |
| 6 | g3 + button | wide: clock BOING, Picard faints, stamp |

## SFX (synthesized with numpy, about 7 LU under the dialogue)
Clock ticks (real time) that accelerate into a whirr; calendar page flutters; bird chirp; BOING spring; faint thud; stamp thump.
