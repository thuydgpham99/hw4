# Campus Customs

A storefront for Campus Customs, the officially licensed Yale merchandise shop at
57 Broadway, New Haven. React + Vite + TypeScript frontend, FastAPI backend, with
a PydanticAI shop assistant.

## What's here

```
backend/      FastAPI app — catalogue, accounts and the shop assistant
  main.py     API routes; the file you run with Uvicorn
  db.py       SQLite access, category normalization, size ordering
  auth.py     Password hashing and signed session tokens
  agent.py    PydanticAI agent — prompt + model + tool wiring
  tools.py    The tools the agent can call
  models.py   Pydantic structured types
  prompts/
    prompt.md System prompt: voice, honesty rules, safety
frontend/     React + Vite + TypeScript
  src/pages/        Home, Products, ProductDetail, About, Login, CreateAccount
  src/components/   NavBar, ProductCard, ChatPanel, Footer
  src/auth.tsx      Session state
data/         NOT IN GIT — the database and product images
output/       harness.md, the running build notes
AI_prompts.md The prompt log for this assignment
```

## The data files are not in this repo

`data/campus_customs.db` and `data/products/` are deliberately gitignored. To run
this, place them yourself:

```
data/
  campus_customs.db
  products/*.jpg
```

The backend reports whether it can see the database at `/api/health`.

## Configuration

The agent calls its model through Portkey. Copy `backend/.env.example` to
`backend/.env` and fill in:

```
SESSION_SECRET=<python3 -c "import secrets; print(secrets.token_hex(32))">
PORTKEY_API_KEY=<your key>
PORTKEY_BASE_URL=https://api.portkey.ai/v1
PORTKEY_MODEL=gpt-5.6-luna
```

`backend/.env` is gitignored and must never be committed.

## Running it

Two servers.

Backend, from the `backend/` folder:

```bash
cd backend
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/uvicorn main:app --reload --port 8000
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to port 8000, so the frontend is reached on its own URL
(http://localhost:5173 by default) and no CORS configuration is needed in the
browser.

**If port 8000 is already taken**, run the backend on another port and point the
proxy at it by creating `frontend/.env.local`:

```
VITE_API_TARGET=http://127.0.0.1:8010
```

## API

| Route | Purpose |
|---|---|
| `GET /api/health` | Liveness, plus whether the database file was found |
| `GET /api/products` | Catalogue; optional `?category=` and `?search=` |
| `GET /api/products/{id}` | One product with per-size stock |
| `GET /api/categories` | Normalized categories with counts |
| `GET /api/images/{filename}` | Product image from `data/products/` |
| `POST /api/auth/register` | Create an account |
| `POST /api/auth/login` | Sign in, returns a session token |
| `GET /api/auth/me` | The current session's user |
| `POST /api/chat` | Shop assistant — returns a reply plus matching products |

## Talking to the agent from a terminal

```bash
cd backend
./.venv/bin/python agent.py "do you have a navy hoodie in medium?"
```

## Notes on the data

The catalogue's `garment_type` column holds 22 free-text variants (including a
case-only duplicate pair) that `db.normalize_category` collapses into six
shopper-facing categories. `colors` and `search_tags` are JSON array strings, not
native columns, so they are parsed on read. Sizes are sorted XS→XXL by an explicit
rank rather than alphabetically.
