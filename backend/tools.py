"""Tools the Campus Customs agent can call.

Every one of these reads the live SQLite database. The agent has no product
knowledge of its own — if a price, color or size count is not returned by a tool
here, the agent has no business stating it.

Each tool also records whichever products it surfaced onto the run's dependency
object, so the chat route can send those back to the website as product cards
without the model having to repeat the data in its reply.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import db
from models import (
    DescriptionAnswer,
    PriceAnswer,
    ProductDetail,
    ProductSummary,
    SizeStock,
    StockAnswer,
)

MAX_RESULTS = 8


@dataclass
class ShopDeps:
    """Per-conversation state handed to every tool call.

    Carries three things: who is chatting, what they are looking at, and what the
    agent has surfaced so far.
    """

    # --- Who is chatting -----------------------------------------------------
    # None for guests. Only the fields needed to greet someone and be useful —
    # no password hash, no account id exposed to the model.
    user_name: str | None = None
    user_first_name: str | None = None
    user_email: str | None = None

    # --- What they are looking at --------------------------------------------
    # Set when the shopper is on a product page, so "do you have this in pink?"
    # has a referent without them naming the item.
    current_product_id: str | None = None
    current_product_name: str | None = None

    # --- What the agent surfaced ---------------------------------------------
    surfaced: list[dict] = field(default_factory=list)
    _seen: set[str] = field(default_factory=set)

    @property
    def is_signed_in(self) -> bool:
        return self.user_email is not None

    def record(self, product: dict) -> None:
        if product["product_id"] not in self._seen:
            self._seen.add(product["product_id"])
            self.surfaced.append(product)

    def record_all(self, products: list[dict]) -> None:
        for product in products:
            self.record(product)


def _to_summary(row: dict) -> ProductSummary:
    return ProductSummary(
        product_id=row["product_id"],
        name=row["name"],
        category=row["category"],
        description=row["description"],
        colors=row["colors"],
        price=row["price"],
        image_url=row["image_url"],
    )


def _to_detail(row: dict) -> ProductDetail:
    return ProductDetail(
        product_id=row["product_id"],
        name=row["name"],
        category=row["category"],
        description=row["description"],
        colors=row["colors"],
        search_tags=row["search_tags"],
        price=row["price"],
        image_url=row["image_url"],
        sizes=[SizeStock(**s) for s in row.get("sizes", [])],
        total_stock=row.get("total_stock", 0),
        in_stock=row.get("in_stock", False),
    )


def _tokenize(text: str) -> list[str]:
    """Split a query into lowercase words, dropping filler that matches everything."""
    stop = {
        "a", "an", "the", "do", "you", "have", "any", "got", "is", "are", "in",
        "for", "of", "with", "and", "or", "to", "me", "i", "want", "looking",
        "show", "need", "can", "get", "some", "that", "this", "it", "my", "your",
        "please", "what", "whats", "s", "like", "something", "anything",
    }
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in stop and len(w) > 1]


def search_products(query: str) -> list[ProductSummary]:
    """Find products matching a shopper's words.

    Scores across name, search tags, colors, category and description rather
    than name alone — shoppers say "navy hoodie" or "The Game", which rarely
    appears in a product title.
    """
    tokens = _tokenize(query)
    if not tokens:
        return []

    scored: list[tuple[int, dict]] = []
    for product in db.list_products():
        name = product["name"].lower()
        category = product["category"].lower()
        description = product["description"].lower()
        tags = [t.lower() for t in product["search_tags"]]
        colors = [c.lower() for c in product["colors"]]

        score = 0
        for token in tokens:
            if token in name:
                score += 5
            if any(token in tag for tag in tags):
                score += 4
            if any(token in color for color in colors):
                score += 3
            if token in category:
                score += 3
            if token in description:
                score += 1

        if score:
            scored.append((score, product))

    # Highest score first; ties broken by name so results are stable run to run.
    scored.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
    return [_to_summary(p) for _, p in scored[:MAX_RESULTS]]


def browse_category(category: str) -> list[ProductSummary]:
    """List products in one category: T-Shirts, Crewnecks, Hoodies,
    Quarter-Zips, Jackets or Long Sleeve.

    Returns the complete category, not a truncated page. Cutting it short here
    made the agent present a partial list as if it were everything we stock.
    Card display is capped separately, at render time.
    """
    wanted = category.strip().lower()
    matches = [p for p in db.list_products() if p["category"].lower() == wanted]
    return [_to_summary(p) for p in matches]


def get_product_details(product_id: str) -> ProductDetail | None:
    """Full record for one product, including per-size stock and all colors."""
    row = db.get_product(product_id)
    return _to_detail(row) if row else None


def get_product_price(product_id: str) -> PriceAnswer:
    """Look up what one product costs. The only source of a price."""
    row = db.get_product(product_id)
    if row is None:
        return PriceAnswer(
            product_id=product_id,
            product_name=product_id,
            found=False,
            note="No product with that id is in the catalogue.",
        )
    return PriceAnswer(
        product_id=row["product_id"],
        product_name=row["name"],
        found=True,
        price=row["price"],
        note=f"{row['name']} is ${row['price']:.0f}.",
    )


def get_product_description(product_id: str) -> DescriptionAnswer:
    """What a product is: the catalogue description, its category and colors."""
    row = db.get_product(product_id)
    if row is None:
        return DescriptionAnswer(
            product_id=product_id,
            product_name=product_id,
            found=False,
            note="No product with that id is in the catalogue.",
        )
    return DescriptionAnswer(
        product_id=row["product_id"],
        product_name=row["name"],
        found=True,
        description=row["description"],
        category=row["category"],
        colors=row["colors"],
        price=row["price"],
        note=f"Comes in: {', '.join(row['colors'])}.",
    )


def check_size_stock(product_id: str, size: str | None = None) -> StockAnswer:
    """Answer a specific availability question for one product.

    Separates "no such product" from "that product is out of stock in that size",
    because those need different answers and blurring them is how a shop assistant
    ends up being vague about bad news.
    """
    row = db.get_product(product_id)
    if row is None:
        return StockAnswer(
            product_id=product_id,
            product_name=product_id,
            found=False,
            note="No product with that id is in the catalogue.",
        )

    sizes = [SizeStock(**s) for s in row["sizes"]]
    available = [s.size for s in sizes if s.in_stock]
    sold_out = [s.size for s in sizes if not s.in_stock]

    answer = StockAnswer(
        product_id=row["product_id"],
        product_name=row["name"],
        found=True,
        available_sizes=available,
        sold_out_sizes=sold_out,
    )

    if size:
        wanted = size.strip().upper()
        match = next((s for s in sizes if s.size.upper() == wanted), None)
        if match is None:
            answer.size = wanted
            answer.note = (
                f"{wanted} is not a size we carry. Sizes run XS through XXL."
            )
        else:
            answer.size = match.size
            answer.quantity = match.quantity
            answer.in_stock = match.in_stock
            answer.note = (
                f"{match.quantity} in stock in {match.size}."
                if match.in_stock
                else f"Out of stock in {match.size}."
            )
    else:
        answer.in_stock = any(s.in_stock for s in sizes)
        answer.note = (
            f"In stock in {len(available)} of {len(sizes)} sizes."
            if available
            else "Sold out in every size."
        )

    return answer


def find_similar_products(
    product_id: str, size: str | None = None, limit: int = 3
) -> list[ProductSummary]:
    """Comparable products to suggest when the original is not available.

    Only returns items that are genuinely in stock — in `size` when one is given
    — so an alternative offered after a sold-out answer cannot itself be
    unavailable. A suggestion has to be as honest as the refusal it follows.
    """
    original = db.get_product(product_id)
    if original is None:
        return []

    original_tags = {t.lower() for t in original["search_tags"]}
    original_colors = {c.lower() for c in original["colors"]}
    wanted_size = size.strip().upper() if size else None

    scored: list[tuple[int, dict]] = []
    for candidate in db.list_products():
        if candidate["product_id"] == product_id:
            continue

        # Stock check first — an out-of-stock alternative is worse than none.
        detail = db.get_product(candidate["product_id"])
        if detail is None:
            continue
        if wanted_size:
            match = next(
                (s for s in detail["sizes"] if s["size"].upper() == wanted_size), None
            )
            if match is None or not match["in_stock"]:
                continue
        elif not detail["in_stock"]:
            continue

        score = 0
        if candidate["category"] == original["category"]:
            score += 6
        score += 2 * len(original_tags & {t.lower() for t in candidate["search_tags"]})
        score += len(original_colors & {c.lower() for c in candidate["colors"]})
        # Prefer a similar price point; penalise by every $20 of difference.
        score -= int(abs(candidate["price"] - original["price"]) // 20)

        if score > 0:
            scored.append((score, candidate))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
    return [_to_summary(p) for _, p in scored[:limit]]


def list_categories() -> list[str]:
    """The categories a shopper can browse, with how many items are in each."""
    return [f"{c['name']} ({c['count']} items)" for c in db.list_categories()]
