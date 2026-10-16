# How HoloDeck draws its videos

Every frame is drawn from scratch in code: no image files, no AI-generated art. NumPy does the math, OpenCV (`cv2`) rasterizes lines and fills, Pillow renders handwriting fonts, and ffmpeg encodes. It is a small hand-built vector animation system that imitates ink on paper.

## Canvas
Each frame is a 1920x1080 NumPy array (BGR) filled with an off-white `PAPER` color; everything is drawn in a near-black `INK` color.

## The Pen (`stickfig.py`)
- `Pen` holds a camera `(cx, cy, zoom)` and maps scene coordinates to screen pixels (`S()`), so pans and zooms are just math.
- Lines, arcs, circles and rects all become point lists passed to `cv2.polylines` / `cv2.fillPoly` with anti-aliasing. Coordinates are multiplied by 16 with `shift=4`, giving sub-pixel precision so thin lines stay smooth.

## Hand-drawn wobble
`_wobble()` resamples each stroke every ~14 px, then offsets each point along the line's normal by two summed sine waves (one long and gentle, one shorter) plus a tiny whole-stroke shift. Closed shapes get the offset bent back so the ends meet.

## The "boil"
Each stroke's random generator is seeded from a CRC of its stroke id plus a boil counter that ticks 12 times per second (`BOIL_FPS = 12`). The wobble holds steady briefly, then redraws slightly differently, like hand animation retraced each drawing. Seeded, not truly random, so any frame renders identically every time.

## Figures and poses
- A figure is a skeleton of segment lengths (`SEG`: head radius, neck, torso, upper/forearm, thigh, shin).
- A pose is a dict of joint angles (shoulders, elbows, hips, knees, lean, tilt, look). Named poses (`shrug`, `facepalm`, Barclay's `nervous`, ...) live in `POSES` and combine with `+` (e.g. `sit+thumbs`, inline params like `scrib=1.8`).
- `Figure.key(t, pose, dur)` adds keyframes; `pose_at()` blends every angle with a smoothstep ease. `move()` / `pos_at()` do the same for position (walking, entrances).
- A slow sine on `lean` makes characters breathe.

## Faces and props
Eyes are two dots shifted by look direction. Mouth opening (`talk`) is driven per frame by the voice RMS envelopes in `timeline.json`, so lips follow the audio. Grok Bot (`robot` prop) gets square eyes and an LED grill mouth whose bars jump like a level meter. Props (beard, cap, PADD, badge...) are drawn on top by flag.

## Sets (`sets.py`, `inkset.py`)
Ship, consoles, chairs, starfields and scenes (bridge, warp, poker, disco...) each have `bg` and `fg` layers. The starfield fakes 3D by dividing star positions by a depth value that moves toward the camera over time. `RevealPen` draws strokes progressively so drawings appear to be inked on screen.

## Frame engine (`engine.py`)
Per frame:
1. Pick the active shot from the cue file.
2. Compute the camera, including zoom kicks and shakes timed to music beats and bars, plus beat bounce and jumps.
3. Draw set background, figures (optionally with a halo outline for busy backgrounds), set foreground, then transitions (e.g. an ink splat built from a wavy circle).
4. `finish()` applies the paper look: a vignette plus fibrous grain, cycling 4 grain textures with the boil, plus fades in and out.
5. Raw frames stream through a pipe into ffmpeg (`libx264`, `-tune animation`).

## Why this approach
Everything is math plus seeded randomness, so it is repeatable, tiny enough to commit to git, and runs on CPU with no GPU or image model. Animating means editing keyframes and cues, not redrawing, and the wobble and boil give the hand-drawn feel for free.
