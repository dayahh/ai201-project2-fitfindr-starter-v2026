"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    # Each pass runs one step, writes its result into the session, then looks
    # at that result to pick the next step. Every tool reads its inputs back
    # out of the session rather than from a local variable.
    step = "parse"
    count = 0
    while step != "done":
        count += 1
        trace.check_iterations(count)

        if step == "parse":
            session["parsed"] = _parse_query(session["query"])
            step = "search"

        elif step == "search":
            parsed = session["parsed"]
            session["search_results"] = search_listings(
                parsed["description"], parsed["size"], parsed["max_price"]
            )

            # Branch 1 (required): nothing came back, so say what to change and
            # stop. suggest_outfit is never called with nothing.
            if not session["search_results"]:
                session["error"] = _no_results_message(parsed)
                step = "done"
            else:
                step = "select"

        elif step == "select":
            # Branch 2 (stretch): a "fair" top result loses to a "good" or
            # "excellent" one in the next two places, if there is one.
            results = session["search_results"]
            pick = results[0]
            if pick["condition"] == "fair":
                for alt in results[1:3]:
                    if alt["condition"] in ("good", "excellent"):
                        pick = alt
                        break
            session["selected_item"] = pick
            step = "suggest"

        elif step == "suggest":
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"], session["wardrobe"]
            )
            step = "card"

        elif step == "card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            step = "done"

    return session


# ── query parsing (regex) ─────────────────────────────────────────────────────

_PRICE = re.compile(
    r"(?:under|below|less than|up to|max|no more than|<=?)\s*\$?\s*(\d+(?:\.\d+)?)"
    r"|\$\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_SIZE = re.compile(
    r"\b(?:in\s+)?size\s+(us\s*\d+(?:\.\d+)?|w\d+(?:\s*l\d+)?|one size|xxs|xs|xxl|xl"
    r"|small|medium|large|s|m|l|\d+(?:\.\d+)?)\b",
    re.IGNORECASE,
)
_SIZE_WORDS = {"small": "S", "medium": "M", "large": "L"}
_FILLER = re.compile(
    r"^\s*(?:i'?m\s+|i am\s+)?(?:looking for|searching for|i want|i need|find me|show me)"
    r"\s+(?:an?\s+|some\s+)?",
    re.IGNORECASE,
)


def _parse_query(query: str) -> dict:
    """Pull a max_price and a size out of the query; what's left is the description."""
    text = query

    max_price = None
    match = _PRICE.search(text)
    if match:
        max_price = float(match.group(1) or match.group(2))
        text = text[: match.start()] + " " + text[match.end():]

    size = None
    match = _SIZE.search(text)
    if match:
        raw = match.group(1).strip()
        size = _SIZE_WORDS.get(raw.lower(), raw.upper())
        text = text[: match.start()] + " " + text[match.end():]

    description = _FILLER.sub("", text)
    description = re.sub(r"[,;]+", " ", description)
    description = re.sub(r"\s+", " ", description).strip(" .")
    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """
    Say what the user could change. Re-runs the search with one constraint
    dropped at a time to find out which one emptied it. No model call here.
    """
    desc, size, max_price = parsed["description"], parsed["size"], parsed["max_price"]
    asked = f"'{desc}'" if desc else "anything"
    if size:
        asked += f" in size {size}"
    if max_price is not None:
        asked += f" at ${max_price:.0f} or less"

    if desc and not search_listings(desc):
        return (
            f"Nothing matched {asked}. No listing mentions '{desc}' at any size or "
            "price — try a broader word for the item, like 'tee', 'jeans', "
            "'jacket', 'boots', or 'bag'."
        )

    tips = []
    if max_price is not None:
        no_price = search_listings(desc, size, None)
        if no_price:
            cheapest = min(l["price"] for l in no_price)
            tips.append(f"raise your max price to ${cheapest:.0f} (the cheapest match)")
    if size:
        no_size = search_listings(desc, None, max_price)
        if no_size:
            sizes = sorted({l["size"] for l in no_size})[:5]
            tips.append(f"try a different size — it comes in {', '.join(sizes)}")
    if not tips:
        tips.append("loosen both your size and your max price")

    return f"Nothing matched {asked}. To find something, " + ", or ".join(tips) + "."


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
