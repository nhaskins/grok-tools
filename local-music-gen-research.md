# Local music gen to replace Suno: Starship Grokbot (research 2026-10-11)
Target: RTX 5070 Ti 16 GB (Blackwell sm_120, cu128), ComfyUI at C:\AI\ComfyUI. Nothing installed.

## Recommendation
**Top pick: ACE-Step 1.5 (2B turbo/sft; XL 4B with offload).** MIT license, and the vendor says outputs are OK for commercial use (trained on licensed, royalty-free, and synthetic data). It is natively supported in ComfyUI (Templates > Audio). It makes instrumental beds or full songs with vocals, 10 s to 10 min. It accepts explicit `bpm` (30-300), `keyscale`, `timesignature`, and `duration` settings, plus `[Instrumental]`, structure tags, and lyrics. Repaint/cover/extend and vocal-to-BGM are available in the Gradio/API app, but ComfyUI's 1.5 templates don't expose them yet. Speed: under 10 s per full song on a 3090 per the vendor, so a 5070 Ti should take seconds. One RTX 5080 ComfyUI run of 120 s took 215 s *including model load*. VRAM: 2B fits easily; XL needs offload on 16 GB (about 12 GB peak). Community view: it lands between Suno v4.5 and v5. Vocals are weaker than Suno (artifacts, skipped words), but beds are its strength.
**Pipeline fit:** pass `bpm` and `duration` directly, then just verify with librosa (beats.npy/bars.npy should land on a known grid). It can render a 30-60 s bed at, say, 100 BPM 4/4 and trim on bar lines for looping. Output is WAV/FLAC, so the ffmpeg mux is unchanged. LoRA training lets us lock in a "Starship Grokbot" sound.

**Runner-up (instrumental beds only): Stable Audio 3 Medium** (Mar 2026). 1.4B parameters, about 5.5 GB at 30 s, up to 380 s, sub-second on an H200. It does text-to-audio, audio-to-audio, inpainting, and continuation. It's very good for ambient hums and SFX, but has no vocals. License: Stability Community License (free commercial use under $1M revenue, registration required). Gotcha: it needs Flash Attention 2, and without it the output is garbage rather than an error, which is risky on Windows/Blackwell. ComfyUI support is unverified (Stable Audio Open 1.0 is native).
**Vocal alternative:** HeartMuLa-oss-3B (Apache-2.0). Reported as more Suno-like for songs. A community 4-bit ComfyUI node was tested on a 5070 Ti at about 76 s per 60 s of audio. No BPM parameter.

## Comparison
| Model | VRAM (16 GB fit) | Speed | Max len | Vocals | License (commercial?) | Quality vs Suno |
|---|---|---|---|---|---|---|
| ACE-Step 1.5 | <4-8 GB (2B); ~12 GB XL+offload | seconds/song (3090 <10 s) | 10 min | Yes | MIT: yes | Near v4.5; best open all-rounder |
| Stable Audio 3 Medium | ~5-6.5 GB | <1.5 s (H200) | 380 s | No | Community: yes <$1M | Strong instrumental |
| Stable Audio Open 1.0/Small | ~5 GB / ~2 GB | fast | 47 s / 11 s | No | Community: yes <$1M | Superseded |
| HeartMuLa 3B | 8 GB lazy; ~5 GB NF4 | ~76 s per 60 s (5070 Ti) | 4 min | Yes | Apache-2.0: yes | Best open vocals |
| YuE | 24 GB+ (2 sessions) | ~360 s per 30 s (4090) | full song w/ 80 GB | Yes | Apache-2.0: yes | Good, too slow |
| DiffRhythm 1.2 | 8 GB (chunked) | fast | 4m45 | Yes | Apache-2.0: yes | Mid |
| LeVo/SongGeneration (Tencent) | 10-16 GB base | RTF ~0.7 | 2m30-4m30 | Yes | **Research only, no commercial** | Good |
| SongBloom (Tencent) | 6-8 GB | n/a | 150-240 s | Yes | **Changed to non-commercial** | Good |
| MusicGen / MAGNeT | 4-16 GB | slow-ish | ~30 s | No | **Weights CC-BY-NC** | Dated |
| InspireMusic | ~8-16 GB | n/a | 30 s (Long: minutes) | No | Apache-2.0 (check weights) | Mid |

## Caveats
- Blackwell needs PyTorch cu128 wheels. flash-attn/vLLM on Windows is the usual pain point; the ACE-Step `pt` backend avoids vLLM.
- I found no reliable 5070 Ti ACE-Step speed benchmark; the speeds above are the vendors' own numbers.
- Suno still leads on vocals and lyric clarity; for quiet hum beds the gap barely matters.
- Licenses for Tencent and Meta weights rule them out for LinkedIn/commercial posting.

## Sources
- https://github.com/ace-step/ACE-Step-1.5 ; https://huggingface.co/ACE-Step/Ace-Step1.5 ; https://ace-step.github.io/ACE-Step-1.5/en/API
- https://docs.comfy.org/tutorials/audio/ace-step/ace-step-v1-5 ; https://techtactician.com/local-ai-generated-music-comfyui-ace-step-setup-tutorial/
- https://smeltcore.com/recipes/ace-step-1-5-xl-on-rtx-5070-ti-text-to-music-generation-in-comfyui/ ; https://neuraldrift.io/workflows/43
- https://github.com/Stability-AI/stable-audio-3/ ; https://stability.ai/explainers/self-hosted-vs-api-generative-audio-choosing-a-deployment-model ; https://huggingface.co/stabilityai/stable-audio-open-small/blob/main/LICENSE
- https://github.com/HeartMuLa/heartlib ; https://huggingface.co/HeartMuLa/HeartMuLa-oss-3B/discussions/6
- https://github.com/multimodal-art-projection/yue ; https://github.com/ASLP-lab/DiffRhythm
- https://github.com/tencent-ailab/SongGeneration ; https://huggingface.co/tencent/SongGeneration/raw/main/LICENSE
- https://www.reddit.com/r/LocalLLaMA/comments/1nlbqfs/music_generator_songblooms_license_changed_to/
- https://huggingface.co/facebook/musicgen-small ; https://github.com/FunAudioLLM/InspireMusic
- https://www.reddit.com/r/SunoAI/comments/1qx7y1f/suno_v5_is_light_years_ahead_of_acestep_15/ ; https://heart-mula.com/ace-step
