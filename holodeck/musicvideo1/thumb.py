import sys; sys.argv=['x','none']
from render import *
def notes(p, pts):
    for j,(x,y) in enumerate(pts): SETS.note(p,(x,y),60,1,f'tn{j}',double=j%2)
def finish(img):
    h,w=img.shape[:2]; x0=(1920-w)//2
    return np.clip(img.astype(np.float32)*VIG[:h,x0:x0+w]+GR[0][:h,x0:x0+w],0,255).astype(np.uint8)
# wide
img=np.full((1080,1920,3),PAPER,np.uint8); p=Pen(img,(960,540,1.0),3)
SETS.outlined(p,'STARSHIP GROKBOT',(960,120),150,8); p.line([(260,215),(960,208),(1660,216)],8,INK,'ul')
for j in range(9): p.line([(120+j*12,330+j*28),(560,330+j*28)],5,INK,f'sl{j}')
ship(p,(1000,450),1.2)
p.rect(1380,250,1860,420,7,INK,'lb',fill=INK); p.text('THE MUSIC',(1620,300),78,PAPER,'marker'); p.text('VIDEO',(1620,375),78,PAPER,'marker')
p.text('"Make It So"',(1620,470),56,INK,'marker')
notes(p,[(1440,600),(1440,740),(110,640),(110,780)])
SETS.floor(p,y=960)
for k,(who,pr,ps,nm) in enumerate(LINE):
    F(who,330+k*315,960-110*1.45,1,pr,[(0,ps,0)],scale=1.45).draw(p,0,w=7)
p.rect(560,990,1360,1060,0,fill=PAPER); p.text('by Grok Bot & Nate Haskins',(960,1022),48,INK,'hand')
cv2.imwrite('musicvideo-social-thumb.jpg',finish(img),[cv2.IMWRITE_JPEG_QUALITY,88])
# square
img=np.full((1080,1080,3),PAPER,np.uint8); p=Pen(img,(540,540,1.0),3)
SETS.outlined(p,'STARSHIP',(540,95),130,8); SETS.outlined(p,'GROKBOT',(540,215),130,8); p.line([(150,285),(540,280),(930,287)],8,INK,'ul')
for j in range(7): p.line([(40+j*10,360+j*26),(260,360+j*26)],5,INK,f'sl{j}')
ship(p,(560,420),.85)
p.rect(210,525,870,615,7,INK,'lb',fill=INK); p.text('THE MUSIC VIDEO',(540,568),72,PAPER,'marker')
p.text('"Make It So"',(540,655),48,INK,'marker')
SETS.floor(p,y=975)
for k,(who,pr,ps,nm) in enumerate(LINE):
    F(who,140+k*200,975-110*.95,1,pr,[(0,ps,0)],scale=.95).draw(p,0,w=6)
p.rect(180,995,900,1065,0,fill=PAPER); p.text('by Grok Bot & Nate Haskins',(540,1028),44,INK,'hand')
cv2.imwrite('musicvideo-social-thumb-square.jpg',finish(img),[cv2.IMWRITE_JPEG_QUALITY,88])
