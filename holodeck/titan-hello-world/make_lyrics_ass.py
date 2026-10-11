import json,re
L=json.load(open('lyric-timing.json'))
def ts(t):
    t=max(t,0); h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
AMBER='&H0040B0FF&'; BLUE='&H00FFAA50&'; GREEN='&H0060FF70&'; WHITE='&H00FFFFFF&'
hdr=open('titles.ass').read().split('[Events]')[0]
hdr=hdr.replace('[V4+ Styles]','[V4+ Styles]',1)
styles='''Style: Lyric,Exo 2,44,&H0040B0FF,&H70FFFFFF,&H00100810,&H90000000,1,0,0,0,100,100,1,0,1,3,2,2,60,60,52,1
Style: LyricPop,Exo 2,44,&H00FFFFFF,&H00FFFFFF,&H00100810,&H90000000,1,0,0,0,100,100,1,0,1,3,2,2,60,60,52,1
Style: Big,Orbitron,96,&H00FFFFFF,&H00FFFFFF,&H00FFAA50,&H00000000,1,0,0,0,100,100,10,0,1,4,0,5,0,0,0,1
Style: HUD,Rajdhani,30,&H0060FF70,&H0060FF70,&H00000000,&H80000000,1,0,0,0,100,100,4,0,1,1,1,7,40,0,30,1
'''
hdr=hdr.replace('Style: Bar',styles+'Style: Bar')
ev=[]
def D(layer,a,b,style,text): ev.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}")
special={'green':GREEN,'Grok':BLUE,'Bot':BLUE,'Titan':BLUE,"Titan's":BLUE}
for k,o in enumerate(L):
    ws=o['words']; s0=ws[0]['s']; e0=ws[-1]['e']; line=o['line']
    nxt=L[k+1]['words'][0]['s'] if k+1<len(L) else 999
    a=s0-0.3; b=min(e0+0.6,nxt-0.05)
    if line.startswith('Titan, engage') or line.startswith('Engage'):
        # big centered punch, word by word, with a shake on ENGAGE
        for w in ws:
            word=w['w'].strip(',!').upper()
            if word=='ENGAGE':
                for j,(dx,dy) in enumerate([(8,-5),(-7,6),(5,4),(-4,-3),(0,0)]):
                    D(2,w['s']+j*0.05,w['s']+j*0.05+0.05 if j<4 else b+0.8,'Big',
                      f"{{\\pos({640+dx},{430+dy})\\blur1\\fscx{150-j*12}\\fscy{150-j*12}\\fad(0,{500 if j==4 else 0})}}{word}!")
                D(1,w['s'],b+0.8,'Big',f"{{\\pos(640,430)\\blur14\\3c{BLUE}\\bord14\\alpha&H50&\\fad(80,500)}}{word}!")
            else:
                D(2,w['s'],ws[-1]['s'],'Big',f"{{\\pos(640,300)\\fscx60\\fscy60\\t(0,150,\\fscx100\\fscy100)\\fad(60,200)\\fs70}}{word}")
        continue
    if 'Warp the signal' in line:
        txt=''.join(f"{{\\alpha&HFF&\\t({int((w['s']-a)*1000)},{int((w['s']-a)*1000)+60},\\alpha&H00&)}}{w['w']} " for w in ws)
        D(1,a,b,'Lyric',f"{{\\fad(100,250)\\1c{WHITE}\\fscx70\\t(0,{int((e0-a)*1000)},\\fscx115)\\t({int((e0-a)*1000)},{int((b-a)*1000)},\\fscx300\\alpha&HFF&)}}"+txt.strip())
        continue
    if 'Titan rising' in line:
        txt=''.join(f"{{\\alpha&HFF&\\t({int((w['s']-a)*1000)},{int((w['s']-a)*1000)+60},\\alpha&H00&)}}{w['w']} " for w in ws)
        D(1,a,b+0.4,'Lyric',f"{{\\an2\\move(640,656,640,470,0,{int((b+0.4-a)*1000)})\\fad(100,400)\\1c{BLUE}\\t(0,{int((b-a)*1000)},\\fscx125\\fscy125)}}"+txt.strip())
        continue
    chorus = line.startswith(('We pull','We draft','Grok Bot','Captain'))
    if chorus:
        # words pop in white and cool to amber (or their accent colour)
        parts=[]
        for w in ws:
            t0=int((w['s']-a)*1000); col=special.get(w['w'].strip(','),AMBER)
            parts.append(f"{{\\alpha&HFF&\\1c{WHITE}\\t({t0},{t0+60},\\alpha&H00&)\\t({t0},{t0+350},\\1c{col})}}{w['w']}")
        D(1,a,b,'LyricPop',"{\\fad(0,250)}"+' '.join(parts))
        if line.startswith('Captain'):
            hud="CAPTAIN'S LOG  //  STARDATE 04:45"
            dur=e0-s0; n=len(hud)
            typ=''.join(f"{{\\alpha&HFF&\\t({int(i*dur*1000/n)},{int(i*dur*1000/n)+1},\\alpha&H00&)}}{c}" for i,c in enumerate(hud))
            D(1,s0,min(e0+3.5,L[k+1]['words'][-1]['e']),'HUD',"{\\fad(0,400)}"+typ)
        continue
    # verse / pre-chorus: karaoke sweep
    kt=[]; prev=a
    lead=int((s0-a)*100); kt.append(f"{{\\k{lead}}}")
    for j,w in enumerate(ws):
        end=ws[j+1]['s'] if j+1<len(ws) else w['e']
        d=max(int((end-w['s'])*100),1); col=special.get(w['w'].strip(','),None)
        kt.append(f"{{\\kf{d}{('\\1c'+col) if col else ''}}}{w['w']} ")
    D(1,a,b,'Lyric',"{\\fad(150,250)\\move(640,670,640,656,0,200)}"+''.join(kt).strip())
open('lyrics.ass','w').write(hdr+'[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'+'\n'.join(ev)+'\n')
print(len(ev),'events')
