# Campus Customs — Usability Improvements

Four improvements on top of the working shop: two on the front end, two in the
agent/backend. Each one is live in the running app.

---

## Front-end 1 — Chat replies render as formatted text, not raw Markdown

### What I added

The agent writes Markdown — it bolds prices and sizes, and uses bullet lists for
multiple products. The chat panel was rendering that as plain text, so shoppers
saw the raw characters:

> No — the \*\*Baseball Left Chest Crewneck\*\* is out of stock in XL.

A small Markdown renderer (`frontend/src/markdown.tsx`) now converts the agent's
replies into real formatting: **bold**, bullet lists, and paragraph breaks. It is
deliberately a tiny hand-written parser rather than a library — the agent emits a
narrow, known subset of Markdown, and pulling in a full dependency to render three
constructs would be more supply-chain surface than the feature is worth.

It handles only `**bold**`, `-` bullets and blank-line paragraphs. Anything else
passes through as text, so a stray character can never break the panel.

### Why it helps

The asterisks were actively working against the thing the whole assistant is built
for. The agent bolds exactly the facts a shopper is scanning for — **$58**,
**XL**, **25 left** — and showing those wrapped in punctuation buried the emphasis
instead of delivering it. Prices and sizes now stand out at a glance, and a list
of five hoodies reads as a list rather than a wall of hyphens.

For the business: this is the difference between a chat widget that looks
finished and one that looks like a prototype, on the page where a shopper decides
whether to trust what the store tells them.

---

## Front-end 2 — Filter the catalogue by what is actually in stock, in your size

### What I added

Two controls on the Products page, next to the existing category chips:

- **"In stock only"** toggle — hides anything sold out in every size.
- **Size filter** (XS–XXL) — shows only products available *in that size*, not
  products that merely exist in that size.

Both work alongside the category chips and the search box, and the result count
updates to say what is being shown ("Showing 18 of 102 items · in stock in M").
The backend carries the filtering, so the per-size stock check happens in SQL
rather than by fetching 102 products and filtering in the browser.

### Why it helps

The catalogue has **145 of 612 size rows at zero**, and **77 of 102 products are
out of stock in at least one size**. So a shopper who wears XL spends real effort
clicking into products that cannot be sold to them. Three-quarters of the
catalogue has a hole in it somewhere, and before this change the only way to find
the holes was one product page at a time.

For the business: fewer dead-end product views, and a shopper who filters to
their size sees a catalogue that is entirely buyable. It also means the honesty
the site already shows on product pages becomes something a shopper can *act* on
rather than just read.

---

## Agent/backend 1 — Catalogue caching: faster and cheaper per message

### What I added

An in-process cache for the product catalogue (`db.list_products()`), with a
mtime check against the database file so an edited database still invalidates it.

Before, every agent tool call re-read all 102 catalogue rows from SQLite and
re-parsed 204 JSON strings (`colors` and `search_tags` on each row). A single
shopper question routinely triggers two or three tool calls, and a search scores
every product — so one message could mean 300+ row reads and 600+ JSON parses.

### Why it helps

The catalogue and inventory are **read-only at runtime** — only `users` and
`chat_messages` are ever written — so re-reading them per tool call was pure
waste. Caching turns the repeated work into a single load.

The practical effect is latency: the shopper waits less between asking and
answering, and the chat feels like a conversation rather than a form submission.
Stock lookups deliberately **stay uncached** and still hit the database directly,
because quantity is the one number that must never be stale — a cached "25 left"
that is actually 0 would break the honesty the whole assistant is built on.

For the business: lower cost per conversation, and a cache that cannot cause the
one failure mode that matters.

---

## Agent/backend 2 — "Out of stock" now comes with real alternatives

### What I added

A `find_similar_products` tool. Given a product id, it returns genuinely
comparable items — same category, scored by shared search tags and overlapping
colors, with a nearby price — and **only items actually in stock**, optionally in
a specific size.

The prompt now instructs the agent: when something is sold out in the size a
shopper asked for, call this tool and offer one or two real alternatives in the
same reply.

### Why it helps

"No, we're out of that in XL" is honest but it ends the conversation. With this
tool the same answer becomes "No — that one's out in XL, but the Champion Reverse
Weave is the same weight and we have it in XL for $68." The shopper gets what
they came for, and the honest answer stops being a dead end.

This matters because of the shape of the data: **no product is sold out entirely,
but 77 of 102 have at least one size missing.** So "we have it, just not in your
size" is the single most common disappointing answer this assistant will ever
give. Making that specific moment useful is worth more than any other single
improvement to the agent's output.

Critically, the alternatives are filtered by real stock before the agent ever
sees them, so it cannot recommend something that is also unavailable. The
suggestion is as honest as the refusal it follows.

---

## Where to see each one

| Improvement | Where | Confirmed in the running app |
|---|---|---|
| Markdown in chat | Open the chat, ask anything with a price | Reply renders `<strong>$32</strong>` in Yale Blue; zero literal asterisks |
| Stock/size filters | Products page, under the category chips | Filtering to XL shows **77 of 102 items · in stock in XL** |
| Catalogue cache | `backend/db.py` | Cold read 4.77 ms → cached 0.0015 ms (**3237× faster**); 20 searches in 6 ms |
| Alternatives tool | Ask for something in a sold-out size | "out of stock in XL … alternatives available in XL include the Davenport College Crewneck and Squash Left Chest Tennis, both $58" |

---

## Verification

Every claim above was checked against the database rather than taken from the
agent's word.

**Markdown.** Asked "how much is the Boola Boola T Shirt and what sizes are
left?". The rendered HTML came back as:

```html
<p class="md-p">The <strong>Boola Boola T Shirt</strong> is <strong>$32</strong>.
Large is out of stock; it's available in <strong>XS (12), S (12), M (15),
XL (2), and XXL (20)</strong>.</p>
```

Database: `XS=12 S=12 M=15 L=0 XL=2 XXL=20`. Every figure correct, and the
alternatives it offered for large — District Tri Blend T Shirt Vintage Shield
(L=8) and Football Left Chest T Shirt (L=2) — are both genuinely in stock in L.

**Size filter.** 102 products in the catalogue, 77 available in XL. So 25
products — nearly a quarter of the shop — were dead ends for an XL shopper before
this filter existed.

**Cache.** Measured over 50 repeat reads after a cold load. Inventory lookups
were confirmed to still go to the database on every call.

**Alternatives.** Asserted programmatically that every product returned by
`find_similar_products(product_id, size)` is in stock in that size — the test
fails if any suggestion is unavailable.
