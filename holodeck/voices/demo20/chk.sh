#!/bin/bash
# chk.sh tag t1 ... t10 -> /tmp/chk_<tag>.png (2-col grid of raw frames)
tag=$1; shift; P=/workspace/rollcall/venv/bin/python
$P processaudit.py --frames "$@" && $P -c "
import cv2,numpy as np,sys
ts=sys.argv[1:]; ims=[cv2.resize(cv2.imread(f'raw_{t}.png'),(960,540)) for t in ts]
for im,t in zip(ims,ts): cv2.putText(im,t,(10,30),0,1,(0,0,255),2)
if len(ims)%2: ims.append(np.zeros_like(ims[0]))
g=np.vstack([np.hstack(ims[i:i+2]) for i in range(0,len(ims),2)]); cv2.imwrite('/tmp/chk_$tag.png',g)" "$@" && rm -f raw_*.png
