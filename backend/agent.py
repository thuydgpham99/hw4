"""PydanticAI agent for the Campus Customs shop assistant.

The agent is assembled from three things:

  1. The system prompt, read from `prompts/prompt.md` at import time. Keeping the
     prompt in a file rather than a string literal means it can be edited and
     reviewed without touching Python.
  2. A model reached through Portkey, which speaks the OpenAI wire format.
  3. The tools in `tools.py`, each of which reads the live SQLite database.

Run this file directly to talk to the agent from a terminal:

    python agent.py "do you have a navy hoodie in medium?"
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

import tools
from models import ChatReply, ProductCard
from tools import ShopDeps

# Loads backend/.env, then falls back to the course-root .env so the Portkey key
# can live in one place for every assignment.
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent.parent / ".env")

PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"

PORTKEY_API_KEY = os.environ.get("PORTKEY_API_KEY")
PORTKEY_BASE_URL = os.environ.get("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
PORTKEY_MODEL = os.environ.get("PORTKEY_MODEL", "gpt-5.6-luna")


def load_system_prompt() -> str:
    """Read the system prompt from disk."""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"System prompt missing at {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_agent() -> Agent[ShopDeps, str]:
    """Wire the model, prompt and tools into a runnable agent."""
    if not PORTKEY_API_KEY:
        raise RuntimeError(
            "PORTKEY_API_KEY is not set. Put it in backend/.env "
            "(see backend/.env.example)."
        )

    # Portkey is an OpenAI-compatible gateway, so the OpenAI client works against
    # it unchanged — only the base URL differs.
    model = OpenAIChatModel(
        PORTKEY_MODEL,
        provider=OpenAIProvider(
            base_url=PORTKEY_BASE_URL,
            api_key=PORTKEY_API_KEY,
        ),
    )

    agent = Agent(
        model,
        deps_type=ShopDeps,
        instructions=load_system_prompt(),
        retries=2,
    )

    # --- Dynamic context -----------------------------------------------------
    #
    # Appended to the system prompt on every run. Keeping it here rather than in
    # prompt.md means the file stays a static document while who-is-chatting and
    # what-they-are-looking-at change per request.

    @agent.instructions
    def shopper_context(ctx: RunContext[ShopDeps]) -> str:
        lines = ["## This conversation"]

        if ctx.deps.is_signed_in:
            name = ctx.deps.user_first_name or ctx.deps.user_name or "there"
            lines.append(
                f"You are talking to {ctx.deps.user_name} ({ctx.deps.user_email}). "
                f"You may greet them as {name}. Use their name sparingly — once "
                "at the start of a conversation is plenty, not in every reply."
            )
        else:
            lines.append(
                "You are talking to a guest who is not signed in. Do not ask who "
                "they are. If it comes up naturally you may mention that creating "
                "an account keeps their chat history, but do not push it."
            )

        if ctx.deps.current_product_id:
            lines.append(
                f"\nThey are currently looking at the product page for "
                f"**{ctx.deps.current_product_name}** "
                f"(product_id: `{ctx.deps.current_product_id}`). "
                "If they say 'this', 'it', or 'this one' without naming a product, "
                "they mean that item — look it up by that id rather than asking "
                "which product they mean."
            )

        return "\n".join(lines)

    # --- Tools ---------------------------------------------------------------
    #
    # Each wrapper records what it surfaced onto the run's deps, which is how
    # looked-up products reach the website as cards.

    @agent.tool
    def search_products(ctx: RunContext[ShopDeps], query: str) -> list[dict]:
        """Search the catalogue using the shopper's own words.

        Use for open-ended requests like "something warm", "navy hoodie", or
        "Harvard-Yale shirt". Returns matching products, best match first.
        """
        results = tools.search_products(query)
        ctx.deps.record_all([_lookup(r.product_id) for r in results])
        return [r.model_dump() for r in results]

    @agent.tool
    def browse_category(ctx: RunContext[ShopDeps], category: str) -> list[dict]:
        """List products in one category.

        Valid categories: T-Shirts, Crewnecks, Hoodies, Quarter-Zips, Jackets,
        Long Sleeve.
        """
        results = tools.browse_category(category)
        ctx.deps.record_all([_lookup(r.product_id) for r in results])
        return [r.model_dump() for r in results]

    @agent.tool
    def get_product_details(ctx: RunContext[ShopDeps], product_id: str) -> dict | None:
        """Everything about one product: all colors, every size and its stock count."""
        result = tools.get_product_details(product_id)
        if result is None:
            return None
        ctx.deps.record(_lookup(result.product_id))
        return result.model_dump()

    @agent.tool
    def get_product_price(ctx: RunContext[ShopDeps], product_id: str) -> dict:
        """Look up what one product costs.

        Call this for any price question. Never state a price you have not read
        from this tool.
        """
        result = tools.get_product_price(product_id)
        if result.found:
            ctx.deps.record(_lookup(result.product_id))
        return result.model_dump()

    @agent.tool
    def get_product_description(ctx: RunContext[ShopDeps], product_id: str) -> dict:
        """What a product is: catalogue description, category and every color.

        Call this when a shopper asks what something looks like, what it's made
        of, or what colors it comes in. The `colors` list is complete — a color
        not in it is a color we do not make.
        """
        result = tools.get_product_description(product_id)
        if result.found:
            ctx.deps.record(_lookup(result.product_id))
        return result.model_dump()

    @agent.tool
    def check_size_stock(
        ctx: RunContext[ShopDeps], product_id: str, size: str | None = None
    ) -> dict:
        """Check availability of one product, optionally in one specific size.

        Distinguishes "we do not carry that size" from "we are out of it" — keep
        that distinction when you answer.
        """
        result = tools.check_size_stock(product_id, size)
        if result.found:
            ctx.deps.record(_lookup(result.product_id))
        return result.model_dump()

    @agent.tool
    def find_similar_products(
        ctx: RunContext[ShopDeps], product_id: str, size: str | None = None
    ) -> list[dict]:
        """Comparable in-stock products to offer when something is unavailable.

        Call this whenever you have to tell a shopper something is sold out, so
        the bad news comes with a real alternative. Everything returned is
        already confirmed in stock (in `size` if you pass one), so you can offer
        it without re-checking.
        """
        results = tools.find_similar_products(product_id, size)
        ctx.deps.record_all([_lookup(r.product_id) for r in results])
        return [r.model_dump() for r in results]

    @agent.tool_plain
    def list_categories() -> list[str]:
        """The categories a shopper can browse, with how many items are in each."""
        return tools.list_categories()

    return agent


def _lookup(product_id: str) -> dict:
    """Fetch the catalogue row used to build a product card."""
    import db

    return db.get_product(product_id) or {}


def to_product_cards(deps: ShopDeps, limit: int = 6) -> list[ProductCard]:
    """Turn the products the agent looked at into cards for the website."""
    cards: list[ProductCard] = []
    for row in deps.surfaced[:limit]:
        if not row:
            continue
        cards.append(
            ProductCard(
                product_id=row["product_id"],
                name=row["name"],
                category=row["category"],
                description=row["description"],
                colors=row["colors"],
                search_tags=row["search_tags"],
                price=row["price"],
                image_url=row["image_url"],
            )
        )
    return cards


# Built once at import; the agent is stateless between runs, so one instance
# serves every request.
shop_agent = build_agent()


async def answer(
    message: str,
    history: list | None = None,
    *,
    user: dict | None = None,
    current_product_id: str | None = None,
) -> tuple[ChatReply, list]:
    """Run one turn of conversation.

    `user` is the signed-in shopper (or None for a guest) and
    `current_product_id` is the product page they are viewing, if any. Both go
    into deps, where the dynamic instructions above turn them into context.

    Returns the reply for the website plus the updated message history.
    """
    deps = ShopDeps()

    if user:
        deps.user_name = user.get("name")
        deps.user_first_name = user.get("first_name")
        deps.user_email = user.get("email")

    if current_product_id:
        import db

        product = db.get_product(current_product_id)
        if product:
            deps.current_product_id = product["product_id"]
            deps.current_product_name = product["name"]

    result = await shop_agent.run(message, deps=deps, message_history=history or [])
    reply = ChatReply(reply=result.output, products=to_product_cards(deps))
    return reply, result.all_messages()


if __name__ == "__main__":
    import asyncio
    import sys

    question = " ".join(sys.argv[1:]) or "What hoodies do you have?"
    reply, _ = asyncio.run(answer(question))
    print(f"\n> {question}\n")
    print(reply.reply)
    if reply.products:
        print("\nProduct cards sent to the page:")
        for card in reply.products:
            print(f"  - {card.name} (${card.price:.0f})")
