#!/bin/bash
# Grok Bot robot FX: dry + ring-mod (110 Hz) + fifth-up pitch layer, light flanger + bitcrush, then loudness normalize.
in="$1"; out="$2"
ffmpeg -y -loglevel error -i "$in" -filter_complex "\
[0:a]aresample=24000,aformat=sample_fmts=fltp:channel_layouts=mono,asplit=3[a][b][c];\
[b]aeval='val(0)*sin(2*PI*110*t)':c=same[rm];\
[c]asetrate=36000,aresample=24000,atempo=0.6667,volume=1[hi];\
[a][rm][hi]amix=inputs=3:weights='1 0.5 0.22':normalize=0,\
flanger=delay=1.5:depth=1.5:speed=0.4:width=60,\
acrusher=bits=9:mix=0.18:mode=log:aa=1,\
highpass=f=100,lowpass=f=9000,\
loudnorm=I=-16:TP=-1.5:LRA=11[o]" -map "[o]" -ar 44100 "$out"
