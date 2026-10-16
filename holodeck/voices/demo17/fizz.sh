#!/bin/bash
# LIGHT robot fizz for Grok Bot's Riker copy: mostly dry, faint 110 Hz ring-mod, light flanger + crush, then -16 LUFS.
ffmpeg -y -loglevel error -i "$1" -filter_complex "\
[0:a]aresample=24000,aformat=sample_fmts=fltp:channel_layouts=mono,asplit=2[a][b];\
[b]aeval='val(0)*sin(2*PI*110*t)':c=same[rm];\
[a][rm]amix=inputs=2:weights='1 0.16':normalize=0,flanger=delay=1.2:depth=1:speed=0.5:width=40,\
acrusher=bits=10:mix=0.08:mode=log:aa=1,highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11[o]" -map "[o]" -ar 44100 "$2"
