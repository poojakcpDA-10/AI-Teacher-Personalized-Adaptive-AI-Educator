# AI Teacher

A full-stack, adaptive AI teaching platform: upload learning material or name a
topic, get a personalized structured lesson, taught through an AI-narrated
video with subject-aware visuals, that asks questions, detects
misconceptions, adapts on the fly, and produces a scored learning report.

```
ai-teacher/
├── backend/     FastAPI + SQLAlchemy + ChromaDB (RAG) + LLM orchestration
├── frontend/    React (Vite) app — light, learner-friendly UI
└── docker-compose.yml
```

---

## 1. What's actually running out of the box vs. what needs setup

This matters, so it's worth being precise about it up front.

**Works immediately, no downloads or GPU required:**
- Full backend API, database, lesson planning, teaching loop, RAG pipeline
- Document upload & retrieval (PDF/DOCX/PPTX/TXT) — uses a lightweight,
  offline embedding function, no model download needed
- Question generation, answer evaluation, misconception detection,
  subject-aware visual selection and rendering (Matplotlib/Pillow)
- Video assembly pipeline (avatar placeholder + visuals + captions, via
  MoviePy/FFmpeg) and offline TTS (`pyttsx3`)
- The full React frontend

**Needs one piece of setup for real (non-placeholder) answers:**
- An LLM. Without one, the backend runs in `mock` mode: it returns
  clearly-labeled placeholder text so you can see the whole system work
  end-to-end, but the "teaching" isn't real. Point it at Ollama + Qwen 3
  (free, local, private — see §3) or any OpenAI-compatible API in 5 minutes.

**Needs additional infrastructure for production-grade video/voice:**
- A human-like **lip-synced avatar** (SadTalker/Wav2Lip) needs a GPU and
  several GB of model weights that cannot be bundled in this repo.
- **Expressive, multilingual TTS** (Piper/XTTS-v2) similarly needs a local
  model server.
- The app ships with clean adapter interfaces for both (see
  `backend/app/services/avatar_service.py` and `tts_service.py`) and a
  working, no-GPU placeholder (a simple animated avatar card with captions
  and OS-level TTS) so the product is fully demoable today. §5 below is a
  step-by-step guide to swapping in the real thing.

None of this is hidden behind extra flags — `backend/.env` has one setting
per component (`LLM_PROVIDER`, `TTS_PROVIDER`, `AVATAR_PROVIDER`) and the
code path for each is a single, documented file.

---

## 2. Quick start (Docker)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

By default `docker-compose.yml` also starts an `ollama` container. After
first boot, pull the model once:

```bash
docker compose exec ollama ollama pull qwen3:8b
```

Until you do that, `backend/.env`'s `LLM_PROVIDER=mock` setting (or Ollama
simply being unreachable) makes the backend fall back to labeled mock
responses automatically — nothing crashes, you just see placeholder text.

If you don't want to run Ollama in Docker at all, delete the `ollama`
service and its `depends_on` line from `docker-compose.yml` and either run
Ollama on your host machine, or set `LLM_PROVIDER=openai_compatible` and
point at a hosted API (see §3.2).

---

## 3. Running locally without Docker

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Requires **ffmpeg** on your PATH for video assembly
(`apt install ffmpeg` / `brew install ffmpeg` / winget/choco on Windows).
Without it, video generation degrades gracefully to text-only turns.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173.

### 3.1 Connecting the recommended LLM: Qwen 3 via Ollama

This matches the stack most naturally suited to this project — free,
runs entirely on your machine, keeps student conversations private.

1. Install Ollama: https://ollama.com/download
2. Pull the model: `ollama pull qwen3:8b` (a `qwen3:4b` variant exists for
   machines with less RAM/VRAM; a larger `qwen3:14b`/`qwen3:32b` if you have
   the hardware and want stronger reasoning)
3. In `backend/.env`:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=qwen3:8b
   ```
4. Restart the backend.

**Hardware guide (rule of thumb):** `qwen3:4b` runs on most modern laptops
with 8GB+ RAM (CPU-only, slower); `qwen3:8b` is comfortable with a 8GB+ GPU
or 16GB+ RAM; larger variants want a dedicated 16GB+ GPU for good latency.

### 3.2 Alternative: a hosted OpenAI-compatible API

If you don't have a GPU and want low-latency responses without local
inference, point at any OpenAI-chat-compatible endpoint (Groq, Together,
OpenRouter, Fireworks, self-hosted vLLM, LM Studio's local server, etc.):

```
LLM_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_BASE_URL=https://api.groq.com/openai/v1
OPENAI_COMPATIBLE_API_KEY=sk-...
OPENAI_COMPATIBLE_MODEL=qwen/qwen3-32b
```

---

## 4. Environment variables (`backend/.env`)

| Variable | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `mock` | `ollama` \| `openai_compatible` \| `mock` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | |
| `OLLAMA_MODEL` | `qwen3:8b` | |
| `OPENAI_COMPATIBLE_BASE_URL` / `_API_KEY` / `_MODEL` | empty | for hosted LLM APIs |
| `DATABASE_URL` | local SQLite file | swap for `postgresql://...` in production (see §6) |
| `CHROMA_DIR` | `./data/chroma` | vector store location |
| `TTS_PROVIDER` | `pyttsx3` | `pyttsx3` (offline dev) \| `piper` \| `xtts` |
| `AVATAR_PROVIDER` | `static` | `static` (dev placeholder) \| `sadtalker` \| `wav2lip` |
| `CORS_ORIGINS` | `localhost:5173` | add your deployed frontend origin |
| `MAX_UPLOAD_MB` | `50` | |

Full list with defaults: `backend/app/config.py`.

---

## 5. Production upgrades: real avatar + voice

The app is architected so these are drop-in swaps — one function each,
same input/output contract, nothing else in the codebase changes.

### 5.1 Lip-synced avatar (SadTalker or Wav2Lip)

Both require a CUDA GPU (8GB+ VRAM recommended) and are not pip-installable
as simple libraries — you run their inference scripts as a local service.

1. Clone and set up either project's inference environment:
   - SadTalker: https://github.com/OpenTalker/SadTalker
   - Wav2Lip: https://github.com/Rudrabha/Wav2Lip
2. Download their pretrained checkpoints (instructions in their repos).
3. Implement `_sadtalker_generate()` / `_wav2lip_generate()` in
   `backend/app/services/avatar_service.py` — the stub already shows the
   expected call shape (`subprocess.run([...])` against their inference
   script, given an audio file + your avatar source image, producing an
   mp4).
4. Set `AVATAR_PROVIDER=sadtalker` (or `wav2lip`) and
   `AVATAR_IMAGE_PATH=/path/to/your/avatar.png` in `.env`.

### 5.2 Expressive multilingual TTS (Piper or Coqui XTTS-v2)

1. Piper (lightweight, many languages, CPU-friendly):
   https://github.com/rhasspy/piper — download a voice model per language.
2. XTTS-v2 (higher quality, voice cloning, heavier):
   https://github.com/coqui-ai/TTS — run as a local server.
3. Implement `_synthesize_piper()` / `_synthesize_xtts()` in
   `backend/app/services/tts_service.py`.
4. Set `TTS_PROVIDER=piper` (or `xtts`) in `.env`.

### 5.3 Stronger multilingual embeddings for RAG

The bundled embedding function (`backend/app/services/embeddings.py`) is a
deterministic, offline hashing scheme chosen so RAG works with zero
downloads on any machine, including fully offline ones. For meaningfully
better multilingual semantic retrieval (recommended for production):

```python
from sentence_transformers import SentenceTransformer
class BGEEmbeddingFunction:
    def __init__(self):
        self.model = SentenceTransformer("BAAI/bge-m3")
    def __call__(self, input):
        return self.model.encode(list(input), normalize_embeddings=True).tolist()
```

Swap this in for `HashingEmbeddingFunction()` in `rag_service.py`
(`pip install sentence-transformers`; first run downloads the model from
Hugging Face, so you'll need outbound internet access at least once).

### 5.4 Speech-to-text for spoken student input

Not wired up yet. Add a `whisper` branch: `pip install openai-whisper` (or
`faster-whisper` for speed) and a new endpoint that accepts an audio
upload, transcribes it, and forwards the text into the existing
`POST /api/sessions/answer` / `POST /api/sessions/chat` flow — no change
needed downstream since both already just take text.

### 5.5 Real math/physics animation (Manim)

`visual_service.py`'s `render_graph`/`render_force_diagram` use
Matplotlib for speed and zero extra dependencies. For animated (not just
static) explanations, `pip install manim` and add a renderer that shells
out to a Manim scene script, writing an mp4 instead of a png — the
`RENDERERS` dict in that file is the only place that needs a new entry.

---

## 6. Taking this to production

- **Database:** switch `DATABASE_URL` to PostgreSQL for concurrent users
  (`postgresql://user:pass@host/db`); the SQLAlchemy models don't change.
- **Auth:** there's no login system yet — `LessonRequest`/`StudentCreate`
  trust the caller. Add real auth (e.g. an OAuth provider or your own
  JWT layer using the already-installed `python-jose`/`passlib`) before
  exposing this beyond a local demo.
- **File storage:** uploads and generated video/audio currently live on
  local disk (`backend/data/`). For multi-instance deployments, move these
  to object storage (S3-compatible) and store URLs instead of local paths.
- **Background jobs:** document ingestion uses FastAPI `BackgroundTasks`,
  which runs in-process. For heavier load, move to a real task queue
  (Celery/RQ + Redis) so a slow PDF or a video render doesn't block the
  API worker.
- **Secrets:** set a real `SECRET_KEY`, and put API keys in your
  deployment platform's secret manager, not in a committed `.env`.
- **CORS:** set `CORS_ORIGINS` to your actual deployed frontend domain.

---

## 7. Architecture notes

**Teaching loop.** `backend/app/agents/teacher_controller.py` is the single
place that drives a live session:
`Explain → (visual + video) → Question → Evaluate → Misconception detect →
Adapt → Continue`, walking through the structured lesson plan one section
at a time and tracking a small piece of state (pending question, running
Q&A log) directly on the `TeachingSession` row.

**Lesson planning is time-shaped, not just topic-shaped.**
`backend/app/agents/lesson_planner.py` produces structurally different
plans for 5-minute / 20-minute / 60-minute / multi-day requests — this was
a specific, non-negotiable requirement, not left to prompt luck.

**RAG is per-student.** Each student gets their own Chroma collection, so
retrieval never crosses between learners, and a lesson can be explicitly
grounded in one uploaded document (`document_id`) or search across
everything they've uploaded.

**Score is computed, not asked of the LLM.** `progress_service.py`
computes the assessment percentage from the actual correct/incorrect
record; the LLM only writes the qualitative summary (strong/weak areas,
misconceptions, recommended revision) — matching the explicit guidance
against trusting an LLM to grade itself.

**Everything degrades gracefully.** No LLM reachable → mock responses. No
ffmpeg/TTS/avatar backend reachable → the lesson still proceeds as text
with whatever media *did* render. This was a deliberate choice so a
missing piece of infrastructure never breaks the teaching loop.

---

## 8. API reference

Full interactive docs (request/response schemas, "try it out") are
auto-generated at **http://localhost:8000/docs** once the backend is
running. Key endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /api/students` | create a learner profile |
| `POST /api/documents/upload` | upload & ingest a textbook/notes/slides |
| `POST /api/lessons` | generate a structured lesson plan |
| `POST /api/lessons/learning-path` | generate a broad-topic learning path |
| `POST /api/sessions/start` | begin a live teaching session for a lesson |
| `POST /api/sessions/{id}/next` | advance to the next teaching turn |
| `POST /api/sessions/answer` | submit the student's answer to a pending question |
| `POST /api/sessions/chat` | grounded follow-up Q&A mid-lesson |
| `GET /api/sessions/{id}/assessment` | final scored learning report |
| `GET /api/students/{id}/profile` | mastered/weak concepts, learning path |

---

## 9. Known limitations

- Avatar is a static placeholder card, not a lip-synced human, until you
  wire up SadTalker/Wav2Lip (§5.1).
- TTS uses the OS speech engine by default — functional but robotic;
  swap in Piper/XTTS for natural, expressive, multilingual voices (§5.2).
- RAG retrieval quality is good-not-great out of the box (offline hashing
  embeddings); swap in BGE-M3 for real semantic multilingual retrieval (§5.3).
- No speech-to-text yet — students type answers rather than speak them (§5.4).
- No authentication — intended for local/trusted deployment as shipped.
- Single-server design; see §6 before scaling to concurrent multi-user load.
