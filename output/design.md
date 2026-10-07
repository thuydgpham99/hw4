# Campus Customs — Design

What changed, and why it should keep a shopper on the page.

---

## 1. A three-face type system

| Face | Job |
|---|---|
| **Anton** | Varsity block. Hero headline, prices, size boxes, the wordmark. |
| **Playfair Display** | Editorial serif. Section headings — the Ivy register. |
| **Inter** | Everything a shopper actually reads. |

Before this, the CSS asked for Inter but never loaded it, so the whole site fell
back to system fonts and looked like an unstyled template.

**Why it sells:** the hero now reads like a screen-printed banner, not a web
page. More usefully, **prices are set in Anton** — a shopper scanning a grid
locks onto `$68` instantly, which is the number that decides whether they click.

---

## 2. Hero: varsity headline on a textured field

`WEAR IT LIKE **YOU MEAN IT**` at up to 6rem, with the last three words in gold.
Behind it: diagonal athletic stripes at 5% white, and a warm radial glow so the
type sits in light rather than on a flat navy slab.

**Why it sells:** one accent instead of a uniformly loud line gives the eye a
place to land. The stripes read as team kit — the association the store is
actually selling.

---

## 3. A storefront ticker

A gold marquee under the nav, scrolling: *Officially Licensed · 57 Broadway, New
Haven · Sizes XS–XXL · Live Stock Counts On Every Page · Open Late On Game Days ·
Ask Our Shop Assistant Anything.* Pauses on hover.

**Why it sells:** it does the job painted lettering does on a real shop window —
answers "is this legit, where are you, what do you carry" before anyone asks. It
also advertises the two things that make this site different: live stock and the
assistant.

---

## 4. Product cards that behave like a shelf

On hover: the card lifts 6px, the image slowly zooms 6%, a gold rule wipes across
the top edge, and a **View** tag rises in at the bottom-right. Cards fade up in
sequence as you scroll, staggered 55ms apart.

**Why it sells:** the catalogue is 102 near-identical navy garments. Motion on
hover tells a shopper which one they're pointing at, and the View tag makes it
obvious the whole tile is a door — before, only the cursor hinted at that. The
stagger keeps a 102-item grid from arriving as one overwhelming wall.

---

## 5. Product page as a price card

The price is Anton at 2.4rem in Yale Blue, with a gold rule trailing off to the
right like a shelf tag. The image zooms slowly on hover so a shopper can inspect
the print without a lightbox. Size boxes are varsity numerals and lift on hover —
but **only the ones in stock**, so a sold-out size doesn't respond to the cursor.

**Why it sells:** the dead size literally not reacting to your mouse says
"unavailable" faster than reading the label does.

---

## 6. A chat that feels staffed

- A **green pulsing dot** on the launcher — someone is on.
- **Three bouncing dots** while the agent thinks, instead of the words "Looking
  that up".
- **Starter prompts** in an empty chat: *What hoodies do you have? · Something
  warm for The Game · Do you have XL in stock?*
- Bubbles ease in; the panel scales up from the launcher.

**Why it sells:** the hardest part of a chat box is the empty one — most people
don't know what it can do, so they close it. The starters show the assistant's
range in one glance and get a shopper into a real conversation in one click. The
typing dots matter because an agent turn takes a few seconds, and silence reads
as broken.

---

## One thing that is deliberately not decorative

The scroll-reveal animation **fails open**. If `IntersectionObserver` never
fires — which is exactly what happens when a tab is backgrounded — a 1.2 second
fallback timer shows the content anyway.

I found this because my own verification tab was hidden and the entire 102-item
product grid sat at `opacity: 0`. An invisible shop is a worse outcome than no
animation, so the worst case is now a missed fade, never missing merchandise.
