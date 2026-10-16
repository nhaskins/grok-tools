#!/bin/bash
# processaudit-nosfx.mp4 + sfx.wav -> processaudit.mp4 (plain, poster-first) -> processaudit-branded.mp4 (intro + episode + sting)
set -e; cd "$(dirname "$0")"
nice -n 10 ffmpeg -threads 4 -y -loglevel error -i processaudit-nosfx.mp4 -i sfx.wav -filter_complex "[0:a]aresample=48000,aformat=channel_layouts=stereo[d];[1:a]volume=0.8[s];[d][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart processaudit.mp4
nice -n 10 ./brand/make_branded.sh processaudit.mp4 processaudit-branded.mp4 1.0
/workspace/rollcall/venv/bin/python processaudit.py --poster && mv thumbnail.jpg processaudit-thumb.jpg && cp processaudit-thumb.jpg thumbnail.jpg
