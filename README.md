# Campus Customs

A customer website for Campus Customs, the officially licensed Yale merchandise
shop at 57 Broadway, New Haven. React + Vite + TypeScript front end, FastAPI
back end, and a PydanticAI shop assistant that answers from the live database
instead of guessing.

Shoppers can browse 102 products, create an account, and chat with an assistant
that gives honest prices, honest stock counts per size, and puts matching items
on the page as product cards.

---

## 1. Place the data pack (do this first)

The database and the product images are **not in this repository** by design.
Nothing will run until you put them in place.

Copy the local-only data pack into a `data/` folder at the root of this project:

```
hw4/
└── data/
    ├── campus_customs.db      # SQLite: catalogue, inventory, users, chat_messages
    └── products/              # product images referenced by the catalogue
        ├── basic-hoodie-big-yale.jpg
        └── … 101 more
```

The image filenames must match `catalogue.image_file_path`, which is always
`products/<product_id>.jpg`.

Once the back end is running you can confirm it found the database:

```bash
curl http://127.0.0.1:8000/api/health
# {"status":"ok","database_found":true}
```

If `database_found` is `false`, `data/campus_customs.db` is not where the back
end expects it.

---

## 2. Configure the environment

The assistant calls its model through the Portkey gateway. Copy the template and
fill in real values:

```bash
cp .env.example backend/.env
```

```
SESSION_SECRET=...        # python3 -c "import secrets; print(secrets.token_hex(32))"
PORTKEY_API_KEY=...       # your key
PORTKEY_BASE_URL=https://api.portkey.ai/v1
PORTKEY_MODEL=gpt-5.6-luna
```

`backend/.env` is gitignored and must never be committed.

---

## 3. Run the back end

From the `backend/` folder:

```bash
cd backend
python3 -m venv .venv
./.venv/bin/pip install -r ../requirements.txt
./.venv/bin/uvicorn main:app --reload --port 8000
```

Leave it running. It serves the catalogue, images, accounts and the chat
endpoint on <http://127.0.0.1:8000>.

---

## 4. Run the front end

In a second terminal, from the `frontend/` folder:

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints — <http://localhost:5173> by default. Vite proxies
`/api` to port 8000, so no CORS setup is needed.

> **If port 8000 is already in use**, run the back end on another port
> (`--port 8010`) and create `frontend/.env.local` containing
> `VITE_API_TARGET=http://127.0.0.1:8010`.

### Signing in

The seeded test account is `test@campuscustoms.yale.edu` / `password`, or create
a new account from the Create Account page.

### Talking to the agent from a terminal

```bash
cd backend
./.venv/bin/python agent.py "do you have a navy hoodie in medium?"
```

---

## Project layout

```
hw4/
├── AI_prompts.md          # prompt log for the assignment
├── requirements.txt       # Python dependencies
├── .env.example           # config template, placeholders only
├── .gitignore
├── README.md
├── frontend/              # Vite React TypeScript app
├── backend/
│   ├── main.py            # FastAPI app — run with: uvicorn main:app --reload --port 8000
│   ├── agent.py           # agent wiring: prompt + model + tools
│   ├── models.py          # Pydantic structured types
│   ├── tools.py           # tools the agent can call
│   ├── db.py              # SQLite access, category normalization, caching
│   ├── auth.py            # password hashing and session tokens
│   ├── audit.py           # append-only audit trail
│   └── prompts/
│       └── prompt.md      # system prompt: voice, honesty rules, safety
└── output/
    ├── harness.md         # how the system works: models, tools, safety, specs
    ├── design.md          # design decisions
    ├── usability.md       # usability improvements
    ├── app_check.html     # tested-site report — open in a browser
    ├── app_check_images/  # screenshots linked from app_check.html
    └── audit_trail.json   # append-only agent activity log
```

The agent itself is the four files `backend/prompts/prompt.md`, `backend/agent.py`,
`backend/tools.py` and `backend/models.py`. `main.py` is the FastAPI app that
serves it; `db.py`, `auth.py` and `audit.py` are supporting modules it depends on.

---

## API

| Route | Purpose |
|---|---|
| `GET /api/health` | Liveness, and whether the database file was found |
| `GET /api/products` | Catalogue; optional `category`, `search`, `size`, `in_stock` |
| `GET /api/products/{id}` | One product with per-size stock |
| `GET /api/categories` | Normalized categories with counts |
| `GET /api/images/{filename}` | Product image from `data/products/` |
| `POST /api/auth/register` | Create an account |
| `POST /api/auth/login` | Sign in, returns a session token |
| `GET /api/auth/me` | The current session's user |
| `POST /api/chat` | Shop assistant — reply plus matching products |
| `GET /api/chat/history` | A signed-in shopper's saved conversation |

---

## Notes on the data

`catalogue.garment_type` holds 22 free-text variants (including a case-only
duplicate pair) that `db.normalize_category` collapses into six shopper-facing
categories. `colors` and `search_tags` are JSON array strings, not native
columns, so they are parsed on read. Sizes sort XS→XXL by an explicit rank rather
than alphabetically.

Only `users` and `chat_messages` are written at runtime — the catalogue and
inventory are read-only, which is why the catalogue is safely cached in process.
