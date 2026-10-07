"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── helpers ───────────────────────────────────────────────────────────────────

# Words that say nothing about the item. Dropped before matching, so "looking
# for a tee" scores the same as "tee".
_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "in", "on", "of", "to",
    "i", "im", "me", "my", "want", "need", "looking", "find", "some", "any",
    "something", "that", "this", "is", "it", "please", "under", "below",
}

# Words inside a size string that aren't the size itself: "US 9", "XL (fits
# oversized)", "One Size (adjustable)".
_SIZE_FILLER = {"us", "size", "fits", "oversized", "adjustable"}


def _words(text: str) -> set[str]:
    """Lowercase keywords with stopwords removed and a light plural strip."""
    words = set()
    for word in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if len(word) < 2 or word in _STOPWORDS:
            continue
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]  # "tees" → "tee", "jeans" → "jean"
        words.add(word)
    return words


def _size_tokens(size: str) -> set[str]:
    """
    Split a size into whole tokens: "S/M" → {s, m}, "US 8.5" → {8.5},
    "W30 L30" → {w30, 30, l30}. Whole tokens are the point — a substring test
    would say "s" is in "us 9" and "l" is in "xl".
    """
    tokens = set()
    for tok in re.findall(r"[a-z]*\d+(?:\.\d+)?|[a-z]+", size.lower()):
        if tok in _SIZE_FILLER:
            continue
        tokens.add(tok)
        digits = re.sub(r"^[a-z]+", "", tok)
        if digits and digits != tok:
            tokens.add(digits)  # so a bare "30" matches "W30"
    return tokens


def _size_matches(wanted: str, listing_size: str) -> bool:
    """True when every token of the wanted size is in the listing's size."""
    if "one size" in listing_size.lower():
        return True  # fits anyone
    want = _size_tokens(wanted)
    return not want or want <= _size_tokens(listing_size)


def _format_price(price: float) -> str:
    return f"${price:.0f}" if float(price).is_integer() else f"${price:.2f}"


def _describe_item(item: dict) -> str:
    """One listing as a few lines of prompt text. Leaves out a missing brand."""
    lines = [
        f"Title: {item.get('title')}",
        f"Category: {item.get('category')}",
        f"Colors: {', '.join(item.get('colors') or [])}",
        f"Style: {', '.join(item.get('style_tags') or [])}",
        f"Condition: {item.get('condition')}",
        f"Price: {_format_price(item.get('price', 0))} on {item.get('platform')}",
    ]
    if item.get("brand"):
        lines.append(f"Brand: {item['brand']}")
    if item.get("description"):
        lines.append(f"Description: {item['description']}")
    return "\n".join(lines)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    candidates = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > float(max_price):
            continue
        if size and not _size_matches(size, listing["size"]):
            continue
        candidates.append(listing)

    keywords = _words(description)
    if not keywords:
        # Nothing to rank on — price and size were the whole request.
        return sorted(candidates, key=lambda l: l["price"])[: config.SEARCH_RESULT_LIMIT]

    scored = []
    for listing in candidates:
        title_words = _words(listing["title"])
        all_words = title_words | _words(" ".join([
            listing.get("description") or "",
            listing.get("category") or "",
            " ".join(listing.get("style_tags") or []),
            " ".join(listing.get("colors") or []),
            listing.get("brand") or "",
        ]))
        matched = len(keywords & all_words)
        if matched == 0:
            continue
        in_title = len(keywords & title_words)
        # More words matched first; ties go to more title matches, then cheaper.
        scored.append(((-matched, -in_title, listing["price"]), listing))

    scored.sort(key=lambda pair: pair[0])
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    if not new_item:
        return "No item to style — search didn't select anything."

    items = (wardrobe or {}).get("items") or []
    item_text = _describe_item(new_item)

    if not items:
        prompt = (
            f"Someone is thinking about buying this thrifted item:\n\n{item_text}\n\n"
            "They haven't saved any wardrobe items yet. Give general styling "
            "advice: one or two outfit ideas that describe the kinds of pieces "
            "(type, color, fit) that would go well with it. Don't say or imply "
            "that they already own anything. Under 120 words, plain text, no "
            "headings."
        )
    else:
        closet = "\n".join(
            f"- {w.get('name')} ({w.get('category')}; colors: "
            f"{', '.join(w.get('colors') or [])}; style: "
            f"{', '.join(w.get('style_tags') or [])}"
            + (f"; note: {w['notes']}" if w.get("notes") else "")
            + ")"
            for w in items
        )
        prompt = (
            f"Someone is thinking about buying this thrifted item:\n\n{item_text}\n\n"
            f"Here is what they already own:\n{closet}\n\n"
            "Suggest one or two outfits that pair the new item with pieces from "
            "their wardrobe. Only use pieces from the list, and name each one "
            "exactly as it's written there. One short line on why each outfit "
            "works. Under 120 words, plain text, no headings."
        )

    response = generate(prompt, system="You are a thrift-savvy personal stylist.").strip()
    return response or f"Couldn't come up with outfit ideas for {new_item.get('title')} — try again."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "Can't write a fit card without an outfit suggestion."

    brand_rule = (
        f"Mention the brand ({new_item['brand']}) once."
        if new_item.get("brand")
        else "There is no brand, so don't mention one."
    )
    prompt = (
        f"The item:\n{_describe_item(new_item)}\n\n"
        f"How it's being styled:\n{outfit.strip()}\n\n"
        "Write the caption someone would post about this thrift find. Rules:\n"
        "- 2 to 4 sentences, first person, casual — a real post, not a product description.\n"
        f"- Mention the item ({new_item.get('title')}), the price "
        f"({_format_price(new_item.get('price', 0))}), and the platform "
        f"({new_item.get('platform')}) exactly once each.\n"
        "- Be specific about the vibe of the outfit.\n"
        f"- {brand_rule}\n"
        "- At most 2 hashtags, at the end of the last sentence.\n"
        "Return only the caption, with no quotes around it."
    )
    response = generate(prompt).strip()
    return response or "Couldn't write a fit card this time — try again."
