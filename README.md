# Personalized AI Journal (RAG MVP)

Full-stack journaling app where each user can write private notes and chat with an AI
assistant that answers strictly from their own entries using Retrieval-Augmented
Generation (RAG).

- **Frontend**: React (Vite), classy dark "ink & gold" theme — chat-first interface with login/signup
- **Streaming**: LLM answers stream token-by-token over a **WebSocket** (Django Channels + Daphne)
- **Session memory**: LangChain **ConversationBufferMemory** keeps the conversation history per user session, so follow-ups like "who was I with?" work
- **Backend**: Django REST Framework (DRF) + JWT auth (SimpleJWT)
- **Vector DB**: Qdrant Cloud (hosted)
- **LLM layer**: provider-agnostic OpenAI-compatible client switching between **OpenRouter**, **Gemini**, **OpenAI**, and **Ollama** via environment variables

## Features

| Requirement | Where it lives |
| --- | --- |
| Sign up / log in / secure session (JWT) | `backend/accounts/`, React `AuthPage` |
| Notes CRUD (multi-tenant, scoped to `request.user`) | `backend/notes/`, React `NotesSidebar` |
| Embedding + ingestion into hosted vector DB on note create | `backend/ai/services.py` → `ingest_note` |
| Update/Delete sync with the vector DB | `backend/notes/views.py` → `perform_update` / `perform_destroy` |
| Semantic retrieval filtered by `user_id` | `backend/ai/vector_store.py` → `VectorStore.search` |
| Provider abstraction (OpenRouter / Gemini / OpenAI / Ollama) | `backend/ai/clients.py` |
| Token-by-token WebSocket streaming + source citations | `backend/chat/consumers.py`, React `Chat` |
| Session chat history (LangChain `ConversationBufferMemory`) | `backend/chat/memory.py` |
| Chunking strategy for long entries | `backend/ai/chunking.py` |

## Architecture

```
React (Vite) ── REST /api (JWT bearer) ──► DRF (auth, notes CRUD)
     │
     └─ WebSocket /ws/chat/?token=<jwt> ──► Channels (Daphne/ASGI)
                                                │
                                                ├── LangChain ConversationBufferMemory (session history)
                                                ├── Qdrant Cloud (embeddings + user_id payload filter)
                                                └── LLM Provider via OpenAI-compatible client
                                                    (OpenRouter / Gemini / OpenAI / Ollama)
```

### Why this LLM abstraction

`ai/clients.py` defines a registry of provider settings (`OPENROUTER_*`, `GEMINI_*`,
`OPENAI_*`, `OLLAMA_*`), each entry mapping role-specific env vars to `BASE_URL`,
`API_KEY` and `MODEL_NAME`. Because all of them expose OpenAI-compatible endpoints, a
single `openai.OpenAI(base_url=..., api_key=...)` instance serves every vendor — switching
provider is pure configuration, zero code changes. Chat and embedding roles resolve
providers independently (`CHAT_PROVIDER`, `EMBED_PROVIDER`), because OpenRouter does not
expose an embeddings endpoint, so the natural free setup is chat on OpenRouter and
embeddings on Gemini. Views and the WebSocket consumer only ever see two verbs —
`chat(messages, stream=...)` and `embed(texts)`; adding a vendor (Groq, Together, vLLM)
means adding one registry entry.

### Session memory

`chat/memory.py` keeps one LangChain `ConversationBufferMemory` per authenticated user
(`human_prefix="User"`, `ai_prefix="Assistant"`). Before each RAG call the buffered
history is injected into the prompt so anaphora like "that place" or "she" resolves against
the conversation; after the answer finishes streaming, the exchange is saved back into the
buffer. Memory lives in-process for the server session and can be reset from the UI with
"New conversation" (which sends a `reset` frame to the consumer). The retrieval step is
still executed on every turn — memory changes what the model reads, never what it may
search.

### Multi-tenancy & data isolation

Isolation is enforced at three independent layers:

1. **API layer** — every endpoint and the WebSocket handshake require a valid JWT
   (the WS token is validated in `chat/ws_auth.py`; unauthenticated sockets are closed
   with code 4401). `NoteViewSet.get_queryset()` is `Note.objects.filter(user=request.user)`,
   so list/retrieve/update/delete are all automatically scoped and 404 for foreign objects.
2. **Vector DB layer** — every Qdrant point stores `user_id` in its payload, both fields
   (`user_id`, `note_id`) carry keyword payload indexes, and every search runs with a
   mandatory server-side
   `Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))])`.
   A user's query is never compared against another user's vectors.
3. **Point identity layer** — each chunk's point ID is `uuid5("note:{note_id}:chunk:{i}")`,
   deterministic per note, so updates overwrite exactly their own points and deletes use a
   `note_id` filter (the note ID is always paired with the authenticated owner at the API
   layer before any vector operation).

### Chunking strategy

Journal entries are usually short, so text under 800 characters is stored as a single
chunk (no information loss). Longer entries are split paragraph-first, then by sentence
boundaries with a 120-character overlap, preserving context across chunk edges. Deterministic
IDs per (note, chunk index) keep Qdrant in sync with edits without read-before-write.

## Run locally

### 1. Prerequisites

- Python 3.11+ and Node.js 18+
- A free [Qdrant Cloud](https://cloud.qdrant.io/) cluster (URL + API key)
- A free [Google AI Studio](https://aistudio.google.com/apikey) key (embeddings), and a free
  [OpenRouter](https://openrouter.ai/keys) key for chat (`:free` models). Fully local
  alternative: Ollama for both roles.

### 2. Backend

```bash
python -m venv venv
venv\Scripts\activate
pip install -r backend/requirements.txt
cd backend
copy .env.example .env          # fill in QDRANT_URL, QDRANT_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY
python manage.py migrate
python manage.py runserver 8001
```

Django runs under Daphne (ASGI) because `daphne` is the first app in `INSTALLED_APPS`, so
HTTP and the WebSocket share port 8001.

### 3. Frontend (development)

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173/> — Vite proxies `/api` and `/ws` to the Django server, so
HTTP auth and WebSocket streaming work on one origin. Sign up, write an entry, ask
*"What did I eat on Tuesday?"*, then a follow-up like *"Who was I with?"* to see the
session memory at work.

### 4. Frontend (production build, served by Django)

```bash
cd frontend
npm run build
```

Then open <http://127.0.0.1:8001/> — Django serves the compiled app from `frontend/dist`.

The RAG retrieval behind the scenes is visible in the runserver terminal:

```
RAG retrieval user=3 question='What did I eat for breakfast on Tuesday?' hits=1
  [1] note=3 score=0.7470 created_at=2026-09-02T19:52:37 preview='Had pancakes with maple syrup...'
Generation starting provider=openrouter model=nvidia/nemotron-3-super-120b-a12b:free (history turns=1)
```

### 5. Switching providers (free tiers)

Everything is changed in `.env` (restart to apply):

- **OpenRouter** hosts ~20 free models (IDs ending in `:free`, browse
  [openrouter.ai/models?max_price=0](https://openrouter.ai/models?max_price=0)). Free tier is
  20 requests/minute and 50 requests/day (1000/day once your account has $10 in credits).
  Free-model availability churns — if a slug 404s ("no longer free") or 429s (shared free
  pool is busy), pick another from the live list. OpenRouter does **not** offer an
  embeddings endpoint, so pair it with `EMBED_PROVIDER=gemini` or `ollama`.
- **Gemini** free tier covers both chat and embeddings via its
  [OpenAI compatibility layer](https://ai.google.dev/gemini-api/docs/openai); grab a key at
  [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
- **Ollama** is fully local and offline; good for the privacy story in your demo.

`EMBEDDING_DIMENSION` must match the embedding model — `3072` for `gemini-embedding-001`,
`768` for Ollama's `nomic-embed-text`. If you change the embedding model after notes exist,
delete the Qdrant collection (or change `QDRANT_COLLECTION`) or upserts will fail on
dimension mismatch.

## API

| Method/Channel | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/api/auth/register/` | — | Create user, returns JWT pair |
| POST | `/api/auth/login/` | — | Returns JWT pair |
| POST | `/api/auth/refresh/` | — | Refresh access token |
| GET/POST | `/api/notes/` | JWT | List own notes / create (triggers ingestion) |
| GET/PATCH/DELETE | `/api/notes/{id}/` | JWT | Retrieve / edit (re-syncs vectors) / delete (removes vectors) |
| WebSocket | `/ws/chat/?token=<jwt>` | JWT | RAG Q&A. Frames in: `{"question"}` or `{"type":"reset"}`. Frames out: `sources` → `token`* → `done` (or `error`) |

## Project layout

```
backend/
  config/        settings, urls, asgi (Channels routing), wsgi
  accounts/      registration + JWT login
  notes/         Note model, serializer, ViewSet, vector-sync services
  chat/          ChatConsumer (WS streaming), ws_auth (JWT handshake),
                 memory.py (LangChain session buffers), prompts.py
  ai/            clients.py (provider registry), vector_store.py (Qdrant),
                 chunking.py, services.py (ingest / retrieve / remove)
frontend/        React (Vite): src/components (AuthPage, Journal, Chat,
                 NotesSidebar), src/hooks/useChatSocket, src/lib/api
```
