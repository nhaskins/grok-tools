# DARK MODE: storyboard (plan of record, as built)
Style-guide idea #7, with an AI/UX angle: a theme toggle nobody tested (contrast ratio 1:1), "fixed" with alt text, and switching back is a flashbang. Slug `darkmode` (demo15). **Box-only**: Piper voices, rig rendered on the box.

## Cast and voices (Piper)
| Who | Rig | Voice |
|---|---|---|
| Barclay | curly, badge; PADD | NEW: en_US-bryce-medium, length-scale .85 (highest, most animated: F0 ~149 Hz, sd 59; nervous and eager) |
| Riker | beard, badge | en_US-hfc_male-medium |
| Grok Bot | robot (+ doodled shades in the button) | en_US-ryan-low + robot chain |
| Picard | shine, badge, collar | en_GB-alan-medium, atempo 1.05 |

## Script
1. BARCLAY: "I, I gave the bridge a dark mode. It's easier on the eyes!" (flips the THEME switch: CLICK, fluorescent flicker, then black)
2. RIKER: "Barclay, I can't see anything. Where did everyone go?" (in the dark: Riker shuffles into Grok Bot, "BONK!" "ow.")
3. GROK BOT: "Contrast ratio, one to one. Now adding alt text." (outlined alt-text labels pop: [GROK BOT, HELPFUL] [RIKER, LOST] [BARCLAY, SWEATING] [FLOOR] [VIEWSCREEN, ALSO DARK] [CAPTAIN, NOT AMUSED])
4. PICARD: "Mister Barclay. Turn it off. Now." (Barclay flips back: CLICK, white-out flashbang, "FZZT!")
   - 2/3 punch-in on Picard shielding his eyes (everyone squints, sizzle marks), held about 1.7 s.
5. GROK BOT: "Light mode restored. Brightness, one hundred and ten percent." (viewscreen BRIGHTNESS 100% → 110%; Grok Bot's shades drop in with a "ting")

## Dark-mode rule
In the dark the whole frame is ink. Figures, set and props are not drawn (ink on ink); only `SETS.outlined` text survives as hollow paper outlines: the sign, the switch labels, BONK, the alt text, and the burned captions (ink fill + paper outline = hollow letters, still legible).

## Poster
Split key art: left = light bridge (Barclay at the switch), right = dark with only the alt-text labels, on a wavy diagonal edge. Title DARK MODE + credit.
