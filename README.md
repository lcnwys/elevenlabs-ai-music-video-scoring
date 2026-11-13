# ElevenLabs AI Music & Video Scoring

**Turn “I want this feeling” into a musical direction you can hear and refine.**

English · [简体中文](README.zh-CN.md) · Originally Eleven Music Director v0.1

MusePilot is a locally hosted AI music workbench for video creators. Describe an emotion and a pace, develop a musical brief, and generate audio with ElevenLabs. Start with a prompt, edit a structured composition plan, or score an existing video.

## Creative starting points

| Need | Suggested workflow |
|---|---|
| A motion-comic character entrance | Develop instrumentation, tempo, and direction from character and story context |
| A short-drama teaser / design reel | Audition multiple directions before choosing one |
| A product film / spoken advertisement | Create an instrumental bed with space for speech |
| An existing video edit | Upload footage with description, tags, SFX, and stem options |
| More arrangement control | Inspect and edit Composition Plan JSON before generation |

## Three routes to music

| Route | Input → output | Service |
|---|---|---|
| Quick music | Prompt → generated audio | ElevenLabs Music |
| Structured plan | Prompt → Composition Plan → manual edits → audio | ElevenLabs Music Plan + Music |
| Video soundtrack | 1–10 videos + settings → audio or stem ZIP | ElevenLabs Video-to-Music |

An optional **AI music director** uses OpenAI to turn your idea and explicitly supplied context into structured suggestions. It does not read your ChatGPT conversations automatically. Without an OpenAI key, standard music, official plan generation, and video scoring remain available. Offline templates are preset drafts rather than LLM reasoning.

> The application UI is currently primarily in Chinese; this README provides English setup and workflow instructions.

## Stack & requirements

| Layer | Implementation |
|---|---|
| Frontend | Single-file vanilla HTML / CSS / JavaScript, localStorage draft library |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| API client | HTTPX; ElevenLabs Music; optional OpenAI Responses API |
| Video validation | ffprobe duration checks; FFmpeg tools recommended |
| Storage | System temporary files for uploads; current-browser storage for drafts and feedback |
| Recommended setup | Python 3.11 / 3.12, desktop browser; no external database |

## Quick start

Download or clone the repository and enter its root, containing `server.py` and `requirements.txt`. The existing folder is named `eleven-music-director-v1`.

### Install dependencies

Use Python **3.11 or 3.12** and a separate virtual environment for this project. This is a Python application: **Node.js, npm, and an external database are not required**. Use a recent Chrome, Edge, Firefox, or Safari; media decoding depends on the browser.

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` directly and use that Python executable for subsequent commands.

Install FFmpeg, for example:

```bash
# macOS with Homebrew
brew install ffmpeg
# Ubuntu / Debian
sudo apt-get update
sudo apt-get install ffmpeg
```

On Windows, install FFmpeg and add its `bin` directory to PATH. Open a new terminal and check:

```bash
ffmpeg -version
ffprobe -version
```

### Configure `.env`

macOS / Linux: `cp .env.example .env`. PowerShell: `Copy-Item .env.example .env`. Edit locally:

```dotenv
ELEVENLABS_API_KEY=<your-elevenlabs-api-key>
# Optional: only needed for the AI director
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_MODEL=gpt-5.4-mini
```

Leave `OPENAI_API_KEY` empty if you only need ElevenLabs. `OPENAI_MODEL` must be available to your account and support the structured-output request used here; adjust it for your account. Existing environment variables take precedence over `.env`.

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

Open **http://127.0.0.1:8765**. Opening `index.html` directly provides offline templates, plan examples, and draft records, but cannot make live AI generation requests.

## A first session

1. Describe a 30-second suspense score for a motion-comic reveal.
2. Optionally ask the AI director for a brief; review mood, instruments, rhythm, and duration.
3. Edit the final prompt or Composition Plan, generate, and listen.
4. Save your feedback and creative version in the draft library; download audio separately.
5. Export draft JSON for your records. Video scoring returns audio or a stem ZIP, **not a soundtrack-composited MP4**.

Example prompt:

> Cinematic instrumental for a 30-second motion-comic teaser. Sparse piano and restrained low strings under dialogue. A short pause before the reveal, then a tense final rise. No vocals; keep the midrange open for speech.

## Configuration, limits & data flow

| Item | Current behavior |
|---|---|
| Prompt-based music duration | Application validates 3–600 seconds; API/account restrictions may further limit it |
| Video uploads | 1–10 videos, up to 200 MB combined; ffprobe enforces a combined 600-second limit when installed |
| Without ffprobe | Duration validation relies on the upstream service; install it for real footage |
| Video formats | MP4 / MOV / WebM / M4V / MKV |
| Draft persistence | Latest 100 records in current-browser localStorage; export before clearing browser data |
| Temporary videos | Removed after a request; abrupt process termination can leave files behind |

Music prompts, plans, and video-scoring inputs go to ElevenLabs. Your idea and supplied context go to OpenAI only when you use the AI director. Keys are read on the backend from the environment / local `.env` and sent in HTTPS authentication headers to the relevant provider; they are not returned to the browser or stored in drafts. Live generation can incur separate ElevenLabs and OpenAI charges. No upstream zero-retention guarantee is made.

This is a music ideation and generation workbench, not a complete DAW. It does not provide automatic speech ducking, frame-accurate music alignment, finished-video rendering, voice cloning, or team accounts. Check applicable terms and rights for lyrics, inputs, and outputs.

## Development & endpoints

| Path | Role |
|---|---|
| `server.py` | Local service, upload checks, and Music API proxy |
| `director.py` | Optional OpenAI creative brief |
| `music_core.py` | Model, duration, prompt, and plan validation |
| `index.html` | Workbench and local draft library |
| `skill/` | Director prompts, skill definition, and recipes |

| Local endpoint | Purpose |
|---|---|
| `GET /api/status` | Configuration status without keys |
| `POST /api/brief` | Optional AI director brief |
| `POST /api/plan` | Official structured music plan |
| `POST /api/compose` | Audio from a prompt or plan |
| `POST /api/video` | Multipart video-scoring request |

Developer checks: `python -m pytest -q`. Tests do not establish live-account access to every model.

## References

- [ElevenLabs Composition Plans](https://elevenlabs.io/docs/eleven-api/guides/how-to/music/composition-plans)
- [ElevenLabs Video-to-Music](https://elevenlabs.io/docs/api-reference/music/video-to-music)
- Local [setup and capability notes](START_HERE.html)

## Local deployment & development

The commands above start a **single-user service on your own machine**. Leave the terminal running and press `Ctrl+C` to stop it. To restart, enter the same directory, activate the same environment, and run the start command again. If another project uses the port, stop it or choose a different `--port`.

A process manager can keep the same Uvicorn command running. Before offering this service to a team or the public, add authentication, user isolation, a job queue, usage limits, redacted logs, and file cleanup. These production deployment features are not implemented here.

## Troubleshooting

| Symptom | What to check |
|---|---|
| Missing `uvicorn` or Python module | Activate the virtual environment; run `python -m pip install -r requirements.txt` from the project root |
| FFmpeg missing / media probe fails | Check `ffmpeg -version` and `ffprobe -version`; reopen the terminal after installation |
| API returns 401 / 403 | Check the local key, product permissions, and account status; never paste a full key into an issue |
| API returns 429 / generation times out | Check quota, concurrency, and network access; start with a short clip and inspect upstream job state before resubmitting |
| Preview does not play | Check browser codec support; download the result and try a local player |
| Environment changes do not take effect | Restart Uvicorn from the terminal where the variables are configured |

## Contributing

Reproduction steps, sanitized errors, and feature suggestions are welcome. A concrete case—music masking comic dialogue, subtitle drift after dubbing, or an unsuitable musical mood—is especially useful. Include OS, Python / FFmpeg versions, media format, and a minimal workflow. Confirm sharing rights before providing real media.

Code is provided under the [MIT License](LICENSE). API terms, generated-content rights, media-asset rights, and dependency licenses apply separately.

## ElevenLabs integration & pricing inquiries

Maintained by an independent developer, this project gives motion-comic teams, video creators, and builders a practical way to explore ElevenLabs.

Working on **motion-comic dubbing, short-drama localization, video soundtracks, sound effects, voice products, or batch API integration**? Get in touch to discuss product fit, workflow design, and integration. I can also offer **competitively priced ElevenLabs solutions**; availability, terms, and pricing depend on your requirements and an individual quotation.

**Email: [lcnwys@gmail.com](mailto:lcnwys@gmail.com)**

For a useful first conversation, include:

- Your content or product type and a short, sanitized description of the requirement.
- Estimated monthly audio/video minutes, target languages, team size, and API needs.
- Whether you are testing a pilot or preparing a launch.

Do not send API keys, passwords, or unauthorized customer media by email or in public issues. Use issues for product feedback and email for commercial inquiries.

> An independent community project, not an official ElevenLabs product. Inquiries and quotations do not imply official endorsement. ElevenLabs names and trademarks belong to their respective owners.
