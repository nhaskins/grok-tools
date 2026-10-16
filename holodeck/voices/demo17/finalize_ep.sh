#!/bin/bash
# wrongmonitor-nosfx.mp4 + sfx.wav -> wrongmonitor.mp4 (plain, poster-first) -> wrongmonitor-branded.mp4 (intro + episode + sting)
set -e; cd "$(dirname "$0")"
ffmpeg -y -loglevel error -i wrongmonitor-nosfx.mp4 -i sfx.wav -filter_complex "[0:a]aresample=48000,aformat=channel_layouts=stereo[d];[1:a]volume=0.8[s];[d][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart wrongmonitor.mp4
./brand/make_branded.sh wrongmonitor.mp4 wrongmonitor-branded.mp4 1.0
/workspace/rollcall/venv/bin/python wrongmonitor.py --poster && mv thumbnail.jpg wrongmonitor-thumb.jpg && cp wrongmonitor-thumb.jpg thumbnail.jpg
