"""xAI TTS takes for PROCESS AUDIT: takes/<id>_<k>.mp3 (raw) -> takes/<id>_<k>_fin.mp3 (processed, ~-16.5 LUFS)."""
import os, json, subprocess, urllib.request, sys
D = os.path.dirname(os.path.abspath(__file__)); T = f'{D}/takes'; os.makedirs(T, exist_ok=True)
LINES = [  # id, voice, tts text, fx
    ('r1', 'phgklp68e8zm', "Grok Bot, why are there thirty three node processes on my ship?", ''),
    ('g1', 'lumen', "Twenty four are log keepers. Tiny. Harmless. [pause] This big one is the host. It keeps us connected.", 'robot'),
    ('b1', 'orion', "All together, it's only one and a half gigabytes, sir. Totally fine!", ''),
    ('s1', 'iris', "I can save some RAM! I'll just stop the big one!", ''),
    ('g2', 'lumen', "Ensign, no!", 'robot'),
    ('p1', 'rigel', "[sigh] Ensign. We did save the RAM. All of it.", ''),
    ('s2', 'iris', "What did I miss?", ''),
]
def tts(text, voice, out):
    req = urllib.request.Request('https://api.x.ai/v1/tts', json.dumps(dict(text=text, voice_id=voice, language='en')).encode(),
                                 {'Authorization': 'Bearer ' + os.environ['XAI_API_KEY'], 'Content-Type': 'application/json'})
    open(out, 'wb').write(urllib.request.urlopen(req, timeout=120).read())
def sh(*a, cwd=D): subprocess.run(list(a), check=True, cwd=cwd)
if __name__ == '__main__':
  NT = int(sys.argv[1]) if len(sys.argv) > 1 else 3
  for lid, v, txt, fx in LINES:
      for k in range(NT):
          raw = f'{T}/{lid}_{k}.mp3'; fin = f'{T}/{lid}_{k}_fin.mp3'
          if not os.path.exists(raw): tts(txt, v, raw)
          sh('./finalize.sh', raw, fin, *(['robot'] if fx == 'robot' else []))
          print(lid, k, 'ok', flush=True)
