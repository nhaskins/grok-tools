#!/bin/bash
# Red Shirts v2: button CLUNK on Grok Bot's slap + transporter shimmer on #46's beam-out (and a softer one on #47's beam-in).
# All ffmpeg-synthesized. Times are episode times (scene + 0.5 s poster hold).
set -e
SLAP=${SLAP:-13.94}; OUT=${OUT:-14.09}; IN=${IN:-14.72}
ms() { python3 -c "print(int($1*1000))"; }
CL="aevalsrc='0.9*sin(2*PI*(70-15*t)*t)*exp(-22*t)+0.35*sin(2*PI*140*t)*exp(-30*t)':s=48000:d=0.25"
CK="anoisesrc=d=0.03:c=white:r=48000:a=0.6,highpass=f=1500"
SH="aevalsrc='(0.16*sin(2*PI*2093*t)+0.14*sin(2*PI*2637*t+1)+0.12*sin(2*PI*3136*t+2)+0.1*sin(2*PI*3951*t+3))*(0.55+0.45*sin(2*PI*17*t))*sin(PI*t/0.62)':s=48000:d=0.62"
SN="anoisesrc=d=0.62:c=pink:r=48000:a=0.35,highpass=f=2500,lowpass=f=9000,aeval='val(0)*sin(PI*t/0.62)'"
SI="aevalsrc='(0.12*sin(2*PI*(1800+900*t)*t)+0.1*sin(2*PI*(2700+1200*t)*t+1))*(0.55+0.45*sin(2*PI*21*t))*sin(PI*t/0.5)':s=48000:d=0.5"
ffmpeg -nostdin -v error -y -filter_complex "\
$CL,adelay=$(ms $SLAP)[c];$CK,adelay=$(ms $SLAP)[k];\
$SH,adelay=$(ms $OUT)[s];$SN,adelay=$(ms $OUT)[n];$SI,adelay=$(ms $IN)[i];\
[c][k][s][n][i]amix=inputs=5:normalize=0:duration=longest,volume=-6dB,aformat=channel_layouts=mono[a]" -map "[a]" -c:a pcm_s16le sfx.wav
ffmpeg -nostdin -v error -y -i redshirts.mp4 -i sfx.wav -filter_complex \
 "[0:a:0]aresample=48000,aformat=channel_layouts=mono[d];[1:a]aresample=48000[s];[d][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]" \
 -map 0:v:0 -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart redshirts-v2.mp4
echo done
