"""Structured types for the Campus Customs shop assistant.

Everything the agent returns, and everything its tools hand back, is typed here.
Keeping the shapes in one file means the API contract, the agent's tool returns,
and the frontend's TypeScript interfaces can be kept in step deliberately rather
than by accident.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Tool return types -------------------------------------------------------


class SizeStock(BaseModel):
    """Stock for one size of one product."""

    size: str
    quantity: int
    in_stock: bool


class ProductSummary(BaseModel):
    """A product as the agent sees it when browsing or searching.

    Carries the fields the agent needs to answer honestly — price and colors —
    so it never has to guess at either.
    """

    product_id: str
    name: str
    category: str
    description: str
    colors: list[str]
    price: float
    image_url: str


class ProductDetail(ProductSummary):
    """A product with its full inventory breakdown attached."""

    search_tags: list[str] = Field(default_factory=list)
    sizes: list[SizeStock] = Field(default_factory=list)
    total_stock: int = 0
    in_stock: bool = False

    @property
    def available_sizes(self) -> list[str]:
        return [s.size for s in self.sizes if s.in_stock]

    @property
    def sold_out_sizes(self) -> list[str]:
        return [s.size for s in self.sizes if not s.in_stock]


class PriceAnswer(BaseModel):
    """The result of a price lookup.

    Only three fields, deliberately: a price question has one right answer, and
    a wider payload would give the model more surface to paraphrase. `found`
    keeps "we do not sell that" distinct from a price of zero.
    """

    product_id: str
    product_name: str
    found: bool
    price: float | None = None
    note: str = ""


class DescriptionAnswer(BaseModel):
    """What a product is, in the catalogue's own words.

    Carries `colors` alongside the description because "what is this like?" and
    "what colors does it come in?" are usually the same question, and splitting
    them would cost a second tool call.
    """

    product_id: str
    product_name: str
    found: bool
    description: str = ""
    category: str = ""
    colors: list[str] = Field(default_factory=list)
    price: float | None = None
    note: str = ""


class StockAnswer(BaseModel):
    """The result of a specific 'do you have X in size Y' question.

    Deliberately explicit: `found` separates "that product does not exist" from
    "that product exists but is out of stock in that size", because those are
    two different answers to a shopper and collapsing them produces a vague reply.
    """

    product_id: str
    product_name: str
    found: bool
    size: str | None = None
    quantity: int = 0
    in_stock: bool = False
    available_sizes: list[str] = Field(default_factory=list)
    sold_out_sizes: list[str] = Field(default_factory=list)
    note: str = ""


# --- Agent output / API types ------------------------------------------------


class ProductCard(BaseModel):
    """One product card rendered under a chat reply on the website.

    Mirrors the `Product` interface in frontend/src/types.ts.
    """

    product_id: str
    name: str
    category: str
    description: str
    colors: list[str] = Field(default_factory=list)
    search_tags: list[str] = Field(default_factory=list)
    price: float
    image_url: str


class ChatRequest(BaseModel):
    """A message from the website's chat widget.

    `conversation_id` is issued by the backend on the first reply and echoed back
    by the widget, so follow-ups like "do you have that in pink?" resolve against
    the right earlier turn.
    """

    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None
    # The product page the shopper is on, if any — gives "this" a referent.
    current_product_id: str | None = None


class ChatReply(BaseModel):
    """What the chat route returns to the website.

    `products` is the mechanism behind "matching items appear on the page" — the
    frontend renders one card per entry directly beneath the reply text.
    """

    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    conversation_id: str | None = None
    error: str | None = None
