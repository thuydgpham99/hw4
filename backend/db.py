"""Database access for Campus Customs.

Wraps the read-only catalogue/inventory tables in data/campus_customs.db and
smooths over the two quirks found in the Problem 2 analysis:

  1. `garment_type` is free text with 22 distinct values (including a case-only
     duplicate pair) that collapse to ~6 shopper-facing categories.
  2. `colors` and `search_tags` are JSON array strings, not native columns.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

# data/ lives next to backend/, one level up from this file.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
PRODUCT_IMAGE_DIR = DATA_DIR / "products"

# Sizes sort by garment convention, not alphabetically.
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
_SIZE_RANK = {size: i for i, size in enumerate(SIZE_ORDER)}

# The 22 raw `garment_type` values mapped onto the categories a shopper would
# actually click. Matching is done on a lowercased, stripped key.
CATEGORIES = ["T-Shirts", "Crewnecks", "Hoodies", "Quarter-Zips", "Jackets", "Long Sleeve"]

_CATEGORY_RULES: list[tuple[tuple[str, ...], str]] = [
    # Order matters: the first rule whose keyword appears in the raw type wins.
    (("quarter-zip", "1/4 zip"), "Quarter-Zips"),
    (("bomber", "fleece jacket", "jacket"), "Jackets"),
    (("full-zip hooded", "full-zip hood", "hoodie", "hooded"), "Hoodies"),
    (("crewneck", "crew-neck", "crew neck"), "Crewnecks"),
    (("performance shirt", "long-sleeve", "long sleeve", "mockneck"), "Long Sleeve"),
    (("t-shirt", "tee"), "T-Shirts"),
]


def normalize_category(garment_type: str) -> str:
    """Collapse a raw `garment_type` string onto one shopper-facing category.

    Lowercasing is what merges the `short-sleeve T-shirt` / `short-sleeve t-shirt`
    split that would otherwise show up as two separate categories.
    """
    key = garment_type.strip().lower()
    for keywords, category in _CATEGORY_RULES:
        if any(word in key for word in keywords):
            return category
    return "Other"


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. The .db file is intentionally "
            "gitignored — copy it into data/ before running the backend."
        )
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_json_list(raw: str) -> list[str]:
    """`colors` and `search_tags` are JSON strings; never trust them to parse."""
    try:
        value = json.loads(raw)
        return [str(v) for v in value] if isinstance(value, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _row_to_product(row: sqlite3.Row) -> dict[str, Any]:
    """Shape one catalogue row into the JSON the frontend consumes."""
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "category": normalize_category(row["garment_type"]),
        "description": row["description"],
        "colors": _parse_json_list(row["colors"]),
        "search_tags": _parse_json_list(row["search_tags"]),
        "price": float(row["price"]),
        # Served by the backend rather than linked from disk, so the frontend
        # never needs filesystem access to the gitignored images.
        "image_url": f"/api/images/{Path(row['image_file_path']).name}",
    }


# The catalogue is read-only at runtime — only `users` and `chat_messages` are
# ever written — so it is cached in process. Every agent tool call previously
# re-read all 102 rows and re-parsed 204 JSON strings; a single shopper question
# can trigger several tool calls, so that was the hottest path in the app.
#
# Inventory is deliberately NOT cached (see get_product): a stale quantity is the
# one error that would break the honesty the assistant is built on.
_CATALOGUE_CACHE: list[dict[str, Any]] | None = None
_CATALOGUE_MTIME: float | None = None


def _catalogue_is_stale() -> bool:
    """True when the cache is empty or the database file changed underneath it."""
    global _CATALOGUE_MTIME
    if _CATALOGUE_CACHE is None:
        return True
    try:
        return DB_PATH.stat().st_mtime != _CATALOGUE_MTIME
    except OSError:
        return True


def list_products() -> list[dict[str, Any]]:
    """Every product, in name order. No stock data. Cached."""
    global _CATALOGUE_CACHE, _CATALOGUE_MTIME

    if not _catalogue_is_stale() and _CATALOGUE_CACHE is not None:
        return _CATALOGUE_CACHE

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM catalogue ORDER BY name COLLATE NOCASE"
        ).fetchall()

    _CATALOGUE_CACHE = [_row_to_product(row) for row in rows]
    try:
        _CATALOGUE_MTIME = DB_PATH.stat().st_mtime
    except OSError:
        _CATALOGUE_MTIME = None
    return _CATALOGUE_CACHE


def get_product(product_id: str) -> dict[str, Any] | None:
    """One product with its per-size stock attached."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            return None
        sizes = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?",
            (product_id,),
        ).fetchall()

    product = _row_to_product(row)
    product["sizes"] = [
        {
            "size": s["size"],
            "quantity": s["quantity"],
            "in_stock": s["quantity"] > 0,
        }
        # Alphabetical order would put XL before XS; sort by garment convention.
        for s in sorted(sizes, key=lambda r: _SIZE_RANK.get(r["size"], 99))
    ]
    product["total_stock"] = sum(s["quantity"] for s in sizes)
    product["in_stock"] = product["total_stock"] > 0
    return product


def list_categories() -> list[dict[str, Any]]:
    """Normalized categories with product counts, for the Products filter bar."""
    counts: dict[str, int] = {}
    for product in list_products():
        counts[product["category"]] = counts.get(product["category"], 0) + 1
    ordered = [c for c in CATEGORIES if c in counts]
    ordered += sorted(c for c in counts if c not in CATEGORIES)
    return [{"name": name, "count": counts[name]} for name in ordered]


# --- Users -------------------------------------------------------------------
#
# These are the only write paths in the app. Note that `users.name` is NOT NULL
# and predates `first_name`/`last_name`, so every insert must populate all three
# or the row is rejected.


def _row_to_user(row: sqlite3.Row) -> dict[str, Any]:
    """Public view of a user. Deliberately omits `password_hash`.

    Every API response about a user goes through this function, so the hash
    cannot leak into JSON by accident.
    """
    return {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "name": row["name"],
        "email": row["email"],
        "created_at": row["created_at"],
    }


def find_user_by_email(email: str) -> sqlite3.Row | None:
    """Full row including the hash — for password checks only, never returned."""
    with get_connection() as conn:
        return conn.execute(
            # Emails are matched case-insensitively so Test@… and test@… are the
            # same account, which is what a shopper expects.
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),)
        ).fetchone()


def find_user_by_id(user_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_user(row) if row else None


def create_user(
    first_name: str, last_name: str, email: str, password_hash: str
) -> dict[str, Any]:
    """Insert a new account. Raises sqlite3.IntegrityError on duplicate email."""
    full_name = f"{first_name.strip()} {last_name.strip()}".strip()
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO users (name, email, password_hash, first_name, last_name)
               VALUES (?, ?, ?, ?, ?)""",
            (
                full_name,
                email.strip(),
                password_hash,
                first_name.strip(),
                last_name.strip(),
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return _row_to_user(row)


def update_password_hash(user_id: int, password_hash: str) -> None:
    """Used to silently upgrade a legacy hash after a successful login."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id)
        )
        conn.commit()


# --- Chat history ------------------------------------------------------------
#
# Only written for signed-in users. Guests chat happily, but nothing is stored
# against them — there is no user id to attach a row to.


def save_chat_message(
    user_id: int, role: str, content: str, products: list[dict] | None = None
) -> None:
    """Append one turn to a user's history.

    `products_json` holds the cards shown with an assistant turn, so a reloaded
    conversation looks exactly as it did when it happened rather than losing its
    product cards.
    """
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO chat_messages (user_id, role, content, products_json)
               VALUES (?, ?, ?, ?)""",
            (user_id, role, content, json.dumps(products) if products else None),
        )
        conn.commit()


def load_chat_history(user_id: int, limit: int = 40) -> list[dict[str, Any]]:
    """The most recent turns for a user, oldest first."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT role, content, products_json, created_at
               FROM chat_messages WHERE user_id = ?
               ORDER BY id DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()

    history = []
    for row in reversed(rows):  # DESC + reversed = newest N, oldest first
        history.append(
            {
                "role": row["role"],
                "content": row["content"],
                "products": _parse_json_list_of_dicts(row["products_json"]),
                "created_at": row["created_at"],
            }
        )
    return history


def _parse_json_list_of_dicts(raw: str | None) -> list[dict]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def resolve_image_path(filename: str) -> Path | None:
    """Map an image filename to a real file, refusing anything outside data/products."""
    candidate = (PRODUCT_IMAGE_DIR / filename).resolve()
    # Blocks ../ traversal out of the image directory.
    if PRODUCT_IMAGE_DIR.resolve() not in candidate.parents:
        return None
    return candidate if candidate.is_file() else None
