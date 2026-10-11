import sys, cv2, numpy as np
fs=sys.argv[2:]; out=sys.argv[1]; cols=2
ims=[cv2.resize(cv2.imread(f),(960,540),interpolation=cv2.INTER_AREA) for f in fs]
for im,f in zip(ims,fs): cv2.putText(im,f.split('/')[-1],(10,30),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255),2)
while len(ims)%cols: ims.append(np.full_like(ims[0],255))
rows=[np.hstack(ims[i:i+cols]) for i in range(0,len(ims),cols)]
cv2.imwrite(out,np.vstack(rows))
