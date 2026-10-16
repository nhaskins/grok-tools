"""xAI TTS takes for VOICE CLONE: takes/<id>_<k>.mp3 (raw) -> takes/<id>_<k>_fin.mp3 (processed)."""
import os, json, subprocess, urllib.request, sys
D = os.path.dirname(os.path.abspath(__file__)); T = f'{D}/takes'; os.makedirs(T, exist_ok=True)
LINES = [  # id, voice, tts text, fx
    ('g1', 'lumen', "Commander, I have cloned your voice. I can now attend your meetings for you.", 'robot'),
    ('r1', 'phgklp68e8zm', "[laugh] Grok Bot, nobody sounds like me. It takes years of practice.", 'pitch'),
    ('g2', 'phgklp68e8zm', "Make it so... but with more swagger. [laugh]", 'pitchfizz'),
    ('s1', 'iris', "<whisper>Sirs? There are four of you on the comm now.</whisper>", ''),
    ('p1', 'rigel', "[sigh] Number One. Which one of you is the real one?", ''),
    ('b1', 'orion', "I, I can tell, sir! The real one sits on his chair backwards!", ''),
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
