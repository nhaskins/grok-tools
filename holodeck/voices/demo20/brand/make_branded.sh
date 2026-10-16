#!/bin/bash
# Branded single episode: 1 s intro + episode (poster frame 0 frozen to ~1.5 s total hold; audio padded with silence so the
# scene audio still starts with the scene) + 3 s sting. Usage: make_branded.sh episode.mp4 out.mp4 [extra_hold_s=1.0]
set -e
EP=$1; OUT=$2; X=${3:-1.0}; B=$(dirname "$(readlink -f "$0")")
MS=$(python3 -c "print(int($X*1000))")
ffmpeg -nostdin -v error -y -i $B/starship-grokbot-intro.mp4 -i "$EP" -i $B/starship-grokbot-sting.mp4 -filter_complex "\
[0:v]setpts=PTS-STARTPTS,format=yuv420p[v0];\
[1:v:0]tpad=start_mode=clone:start_duration=$X,setpts=PTS-STARTPTS,format=yuv420p[v1];\
[2:v]setpts=PTS-STARTPTS,format=yuv420p[v2];\
[0:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a0];\
[1:a:0]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS,adelay=$MS|$MS[a1];\
[2:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a2];\
[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -r 24 -c:v libx264 -crf 18 -preset medium -threads 4 \
 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT"
echo "$OUT $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")"
