"""Campus Customs API.

Problem 3 scope: serve the product catalogue and product images to the React
frontend. Problem 5 grows this into the PydanticAI agent backend — the /api/chat
route below is a deliberate stub so the frontend chat panel has something real
to call in the meantime.
"""

from __future__ import annotations

import logging
import secrets
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field, field_validator

# Loaded before auth and the agent are imported, so SESSION_SECRET and the
# Portkey credentials are in the environment by the time they read them.
load_dotenv(Path(__file__).resolve().parent / ".env")

import agent as agent_module  # noqa: E402
import auth  # noqa: E402
from models import ChatReply, ChatRequest  # noqa: E402
from db import (  # noqa: E402
    DB_PATH,
    create_user,
    find_user_by_email,
    find_user_by_id,
    get_product,
    list_categories,
    list_products,
    load_chat_history,
    resolve_image_path,
    save_chat_message,
    update_password_hash,
)

logger = logging.getLogger("campus_customs")

app = FastAPI(
    title="Campus Customs API",
    description="Product catalogue, inventory, accounts and the shop assistant.",
    version="0.2.0",
)

# The Vite dev server runs on a different port, so the browser treats API calls
# as cross-origin. 5173 is Vite's default; 5174 is its fallback when 5173 is busy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    """Confirms the API is up and can actually see the database file."""
    return {"status": "ok", "database_found": DB_PATH.exists()}


@app.get("/api/products")
def products(
    category: str | None = None,
    search: str | None = None,
    size: str | None = None,
    in_stock: bool = False,
) -> dict:
    """The catalogue, filtered by category, free text, size and availability.

    `size` and `in_stock` are evaluated against live inventory rather than the
    cached catalogue, so a shopper filtering to their size never sees something
    that cannot actually be sold to them.
    """
    items = list_products()
    total = len(items)

    if category and category.lower() != "all":
        items = [p for p in items if p["category"].lower() == category.lower()]

    if search:
        # Searching tags and colors as well as the name matters because shopper
        # phrasing ("The Game", "navy") rarely appears in a product title.
        q = search.lower().strip()
        items = [
            p
            for p in items
            if q in p["name"].lower()
            or q in p["description"].lower()
            or any(q in tag.lower() for tag in p["search_tags"])
            or any(q in color.lower() for color in p["colors"])
        ]

    if size or in_stock:
        wanted = size.strip().upper() if size else None
        available = []
        for product in items:
            detail = get_product(product["product_id"])
            if detail is None:
                continue
            if wanted:
                match = next(
                    (s for s in detail["sizes"] if s["size"].upper() == wanted), None
                )
                if match and match["in_stock"]:
                    available.append(product)
            elif detail["in_stock"]:
                available.append(product)
        items = available

    return {"count": len(items), "total": total, "products": items}


@app.get("/api/categories")
def categories() -> dict:
    """Normalized categories with counts, for the Products page filter bar."""
    return {"categories": list_categories()}


@app.get("/api/products/{product_id}")
def product_detail(product_id: str) -> dict:
    """One product, with per-size stock for the detail page."""
    item = get_product(product_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"No product '{product_id}'")
    return item


@app.get("/api/images/{filename}")
def product_image(filename: str) -> FileResponse:
    """Serve a catalogue image. Images are gitignored, so they are read from disk."""
    path = resolve_image_path(filename)
    if path is None:
        raise HTTPException(status_code=404, detail=f"No image '{filename}'")
    return FileResponse(path, media_type="image/jpeg")


# --- Accounts ----------------------------------------------------------------


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)

    @field_validator("first_name", "last_name")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("cannot be blank")
        return value.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def current_user(authorization: str | None = Header(default=None)) -> dict:
    """Resolve the signed session token on an Authorization: Bearer header."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not signed in")
    user_id = auth.read_session_token(authorization[7:].strip())
    if user_id is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    user = find_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Account no longer exists")
    return user


@app.post("/api/auth/register", status_code=201)
def register(request: RegisterRequest) -> dict:
    """Create an account. The plaintext password is hashed and then discarded."""
    try:
        user = create_user(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            password_hash=auth.hash_password(request.password),
        )
    except sqlite3.IntegrityError:
        # The UNIQUE index on users.email is what catches this.
        raise HTTPException(
            status_code=409, detail="An account with that email already exists."
        )
    return {"user": user, "token": auth.create_session_token(user["id"])}


@app.post("/api/auth/login")
def login(request: LoginRequest) -> dict:
    """Verify a password and issue a session token."""
    row = find_user_by_email(request.email)

    # One message for both "no such email" and "wrong password" — a different
    # error for each would let someone probe which emails have accounts.
    invalid = HTTPException(status_code=401, detail="Incorrect email or password.")
    if row is None:
        # Hash anyway so a missing account does not return measurably faster
        # than a wrong password.
        auth.verify_password(request.password, auth.hash_password("placeholder"))
        raise invalid
    if not auth.verify_password(request.password, row["password_hash"]):
        raise invalid

    # The seeded users carry a weaker legacy hash. Now that the correct password
    # is in hand, re-hash at the current work factor and store that instead.
    if auth.needs_rehash(row["password_hash"]):
        update_password_hash(row["id"], auth.hash_password(request.password))

    user = find_user_by_id(row["id"])
    return {"user": user, "token": auth.create_session_token(row["id"])}


@app.get("/api/auth/me")
def me(user: dict = Depends(current_user)) -> dict:
    """Who the current session belongs to."""
    return {"user": user}


# --- Chat --------------------------------------------------------------------
#
# Conversation history is held in memory, keyed by a conversation id the widget
# echoes back. That keeps follow-ups like "do you have that in pink?" resolvable
# without writing to the database yet.

_CONVERSATIONS: dict[str, list] = {}
_MAX_TURNS = 24


def optional_user(authorization: str | None = Header(default=None)) -> dict | None:
    """Like `current_user`, but returns None instead of 401 for guests.

    Chat is open to everyone; being signed in only adds memory and a name.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    user_id = auth.read_session_token(authorization[7:].strip())
    return find_user_by_id(user_id) if user_id is not None else None


@app.get("/api/chat/history")
def chat_history(user: dict = Depends(current_user)) -> dict:
    """A signed-in shopper's saved conversation, replayed on their return."""
    return {"messages": load_chat_history(user["id"])}


@app.post("/api/chat", response_model=ChatReply)
async def chat(
    request: ChatRequest, user: dict | None = Depends(optional_user)
) -> ChatReply:
    """Send a shopper's message to the agent and return its reply."""
    conversation_id = request.conversation_id or secrets.token_urlsafe(12)
    history = _CONVERSATIONS.get(conversation_id, [])

    # A signed-in shopper returning after a restart has no in-memory history, so
    # rebuild it from the database rather than losing the thread.
    if user and not history:
        history = _history_from_db(user["id"])

    try:
        reply, updated = await agent_module.answer(
            request.message,
            history,
            user=user,
            current_product_id=request.current_product_id,
        )
    except Exception as exc:  # noqa: BLE001
        # A model or network failure should degrade to an honest message rather
        # than a 500 that the chat widget renders as a dead end.
        logger.exception("Agent run failed")

        # The provider runs its own content filter and rejects some messages
        # before the agent ever sees them. That is a refusal, not an outage, so
        # it should not be reported as "try again in a moment".
        if "content_filter" in str(exc):
            return ChatReply(
                reply=(
                    "I can't help with that one. If you're after a hoodie, a tee "
                    "or anything else on our shelves, ask away."
                ),
                conversation_id=conversation_id,
                error="content_filter",
            )

        return ChatReply(
            reply=(
                "Sorry — I had trouble reaching our system just then. "
                "Try asking again in a moment."
            ),
            conversation_id=conversation_id,
            error=type(exc).__name__,
        )

    # Trim the oldest turns so a long session cannot grow without bound.
    _CONVERSATIONS[conversation_id] = updated[-_MAX_TURNS:]
    reply.conversation_id = conversation_id

    # Persist only for signed-in shoppers — a guest has no row to attach to.
    if user:
        save_chat_message(user["id"], "user", request.message)
        save_chat_message(
            user["id"],
            "assistant",
            reply.reply,
            [p.model_dump() for p in reply.products],
        )

    return reply


def _history_from_db(user_id: int) -> list:
    """Rebuild PydanticAI message history from stored rows.

    The database stores plain role/content for display; the agent needs typed
    message objects, so they are reconstructed here. Tool calls are not replayed
    — only the conversation as the shopper saw it, which is enough context for
    follow-ups and avoids re-running stale lookups.
    """
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        TextPart,
        UserPromptPart,
    )

    messages: list = []
    for row in load_chat_history(user_id, limit=_MAX_TURNS):
        if row["role"] == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=row["content"])]))
        elif row["role"] == "assistant":
            messages.append(ModelResponse(parts=[TextPart(content=row["content"])]))
    return messages
