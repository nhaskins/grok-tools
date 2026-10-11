#!/bin/bash
# THINKING PARTNER SFX (ffmpeg-synthesized, no copyrighted audio). Episode times = scene time + 0.5 s poster hold.
set -e; cd "$(dirname "$0")"
ms() { python3 -c "print(int(round(($1 + 0.5) * 1000)))"; }
WH="anoisesrc=d=0.4:c=pink:r=48000:a=0.5,highpass=f=800,lowpass=f=6000,aeval='val(0)*sin(PI*t/0.4)*(0.3+t)'"
POP="aevalsrc='0.8*sin(2*PI*(420-300*t)*t)*exp(-28*t)':s=48000:d=0.18"
TICK="aevalsrc='0.45*sin(2*PI*1800*t)*exp(-60*t)+0.25*sin(2*PI*2700*t)*exp(-80*t)':s=48000:d=0.08"
DING="aevalsrc='0.45*sin(2*PI*1568*t)*exp(-4*t)+0.25*sin(2*PI*2349*t)*exp(-5*t)+0.12*sin(2*PI*3136*t)*exp(-7*t)':s=48000:d=1.0"
WAH="aevalsrc='0.5*(sin(2*PI*(233-40*t)*t)+0.5*sin(4*PI*(233-40*t)*t)+0.3*sin(6*PI*(233-40*t)*t))*(1+0.25*sin(2*PI*6*t))*(if(lt(t,0.45),sin(PI*t/0.45),0)+if(gte(t,0.5),sin(PI*(t-0.5)/0.7)*0.9,0))':s=48000:d=1.2,lowpass=f=1800"
ffmpeg -nostdin -v error -y -filter_complex "\
$WH,adelay=$(ms 0.72)[w1];$WH,adelay=$(ms 1.17)[w2];$POP,adelay=$(ms 1.30)[p1];$POP,adelay=$(ms 1.75)[p2];\
$TICK,adelay=$(ms 8.67)[t1];$TICK,adelay=$(ms 11.47)[t2];$TICK,adelay=$(ms 17.67)[t3];$TICK,adelay=$(ms 20.57)[t4];\
$DING,adelay=$(ms 13.97)[d];$POP,adelay=$(ms 21.68)[p3];$WAH,adelay=$(ms 21.85)[wa];\
[w1][w2][p1][p2][t1][t2][t3][t4][d][p3][wa]amix=inputs=11:normalize=0:duration=longest,volume=-10dB,aformat=channel_layouts=stereo[a]" \
 -map "[a]" -c:a pcm_s16le sfx.wav
ffmpeg -nostdin -v error -y -i thinkingpartner-nosfx.mp4 -i sfx.wav -filter_complex \
 "[0:a:0]aresample=48000,aformat=channel_layouts=stereo[d];[1:a]aresample=48000[s];[d][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]" \
 -map 0:v:0 -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart thinkingpartner.mp4
