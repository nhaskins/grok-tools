#!/bin/bash
# finalize.sh <in.wav> <out.mp3> [robot]
in="$1"; out="$2"; tmp=$(mktemp --suffix=.wav)
trim="silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.15,areverse"
if [ "$3" = robot ]; then ffmpeg -y -loglevel error -i "$in" -af "$trim" "$tmp" && ./robot.sh "$tmp" "$tmp.r.wav" && mv "$tmp.r.wav" "$tmp"
else ffmpeg -y -loglevel error -i "$in" -af "$trim,highpass=f=60,loudnorm=I=-16:TP=-1.5:LRA=11" -ar 44100 "$tmp"; fi
ffmpeg -y -loglevel error -i "$tmp" -ar 44100 -ac 1 -c:a libmp3lame -b:a 192k "$out"; rm -f "$tmp"
