"""xAI TTS takes for WARP NINE RENDER: takes/<id>_<k>.mp3 (raw) -> takes/<id>_<k>_fin.mp3 (processed)."""
import os, json, subprocess, urllib.request, sys
D = os.path.dirname(os.path.abspath(__file__)); T = f'{D}/takes'; os.makedirs(T, exist_ok=True)
LINES = [  # id, voice, tts text, fx
    ('r1', 'phgklp68e8zm', "Mister Barclay, how fast are we rendering?", ''),
    ('b1', 'orion', "Seven hundred percent, sir! We're at warp nine!", ''),
    ('g1', 'lumen', "Caution. Memory is at ninety percent. [pause] There is no swap.", 'robot'),
    ('s1', 'iris', "Is everyone okay? I felt that in my context window!", ''),
    ('r2', 'phgklp68e8zm', "[laugh] Turbulence. Everybody lean left.", ''),
    ('p1', 'rigel', "[sigh] Number One. It's a video render. Sit down.", ''),
]
def tts(text, voice, out):
    req = urllib.request.Request('https://api.x.ai/v1/tts', json.dumps(dict(text=text, voice_id=voice, language='en')).encode(),
                                 {'Authorization': 'Bearer ' + os.environ['XAI_API_KEY'], 'Content-Type': 'application/json'})
    open(out, 'wb').write(urllib.request.urlopen(req, timeout=120).read())
def sh(*a, cwd=D): subprocess.run(list(a), check=True, cwd=cwd)
if __name__ != "__main__": LINES = LINES
if __name__ == '__main__':
  NT = int(sys.argv[1]) if len(sys.argv) > 1 else 3
  for lid, v, txt, fx in LINES:
      for k in range(NT):
          raw = f'{T}/{lid}_{k}.mp3'; fin = f'{T}/{lid}_{k}_fin.mp3'
          if not os.path.exists(raw): tts(txt, v, raw)
          src = raw
          if 'pitch' in fx:
              src = f'{T}/{lid}_{k}_p.wav'; sh('ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', 'rubberband=pitch=0.890899:formant=preserved', src)
          if fx == 'robot': sh('./finalize.sh', src, fin, 'robot', cwd='/workspace/grok-tools/holodeck/voices/demo7')
          elif fx == 'pitchfizz':
              w = f'{T}/{lid}_{k}_t.wav'; sh('./finalize.sh', src, w.replace('.wav', '.mp3'))   # trim + norm
              sh('./fizz.sh', w.replace('.wav', '.mp3'), w); sh('ffmpeg', '-y', '-loglevel', 'error', '-i', w, '-ac', '1', '-b:a', '192k', fin)
          else: sh('./finalize.sh', src, fin)
          print(lid, k, 'ok', flush=True)
