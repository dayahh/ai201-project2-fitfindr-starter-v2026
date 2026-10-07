# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## Data Notes (Milestone 1)

**Listing fields:** id, title, description, category, style_tags (list), size,
condition, price (float), colors (list), brand (str or None, usually None), platform

**Sizes are messy:** "S/M", "XL (oversized)", "US 8.5", "W30 L30", "One Size".
A plain substring check won't work ("s" is in "us 9").

**Wardrobe item fields:** id, name, category, colors, style_tags, notes
**Empty wardrobe:** {"items": []}


## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr is a thrifting agent. You describe what you want in plain language, like `'vintage graphic tee under $30, size M'`, and it searches 40 secondhand listings from Depop, ThredUp, and Poshmark for the best match within your price and size. It then suggests one or two outfits that pair the find with pieces from your wardrobe, and writes a short caption you could post about it. If nothing matches, it stops and tells you what to change, such as raising your price, trying another size, or using a broader word.



---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the listings file by price and size, then ranks what's left by how many words from the description each listing contains.
- **Inputs:** `description` (str), `size` (str or None: matched by whole size, so "M" matches "S/M" but "L" doesn't match "XL"), `max_price` (float or None, inclusive)
- **Returns:** A list of up to 10 listing dicts, best match first. Each has `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`.
- **When it has nothing:** An empty list `[]`. Never `None`, never an error.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits that pair the new item with pieces from the user's wardrobe.
- **Inputs:** `new_item` (dict, one listing), `wardrobe` (dict with an `items` list; each item has `name`, `category`, `colors`, `style_tags`, `notes`)
- **Returns:** A non-empty string of outfit ideas that name specific wardrobe pieces.
- **When it has nothing:** If the wardrobe is empty, it returns general styling advice for the item instead.

### `create_fit_card`

- **What it does:** Asks the model for a short caption someone would actually post about the find.
- **Inputs:** `outfit` (str, from `suggest_outfit`), `new_item` (dict, the same listing)
- **Returns:** A 2–4 sentence string that mentions the item's title, price, and platform once each.
- **When it has nothing:** If `outfit` is empty or only whitespace, it returns the string `"Can't write a fit card without an outfit suggestion."` without calling the model.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:**

1. **Empty search (required):** If `search_listings` returns an empty list, put a
   message in `session["error"]` that names what to change (a higher price, a
   different size, or a broader word) and stop without calling `suggest_outfit`.
   Otherwise, go to rule 2.
2. **Fair-condition top result (stretch: second branch):** If the first result's
   `condition` is "fair", look at the next two results and pick the first one
   whose `condition` is "good" or "excellent". If neither is, keep the first
   result. Otherwise, take the first result. Either way, the pick goes in
   `session["selected_item"]` and the loop moves on to `suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex. A price comes from phrases like "under $30",
"below $30", or a bare "$30". A size comes from "size M", "size US 9", or
"size W30". Whatever words are left become the description.

**What moves through the session:** `query` → `parsed` (description, size,
max_price) → `search_results` → `selected_item` → `outfit_suggestion` →
`fit_card`. On the empty path it stops after `search_results` and sets `error`;
`selected_item`, `outfit_suggestion`, and `fit_card` stay `None`.



---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

  Outfit:   Outfit one: Pair the Graphic Tee — 2003 Tour Bootleg Style tucked into the Baggy straight-leg jeans, dark wash, finished with the Black combat boots, the Vintage black denim jacket, and the Black crossbody bag. It works because the faded tee and combat boots lean into an authentic grunge aesthetic, while the double denim adds great texture.

Outfit two: Style the Graphic Tee — 2003 Tour Bootleg Style loose over the Wide-leg khaki trousers, paired with the Chunky white sneakers, the Brown leather belt, and the Black cropped zip hoodie worn open. It works because the edgy graphic tee contrasts nicely with clean earth tones for an easy, balanced streetwear look.

  Fit card: Scored this Graphic Tee — 2003 Tour Bootleg Style for just $24 on depop and it has the absolute best worn-in feel. I've been living in it styled with baggy denim and combat boots for that ultimate grungy, effortless look. #thriftfind #streetwear
```

The top search result for that query was the Vintage Band Tee, which is in "fair" condition, so branch 2 picked the "good" Graphic Tee in second place instead.

**The empty-search branch**

```
$ python app.py ask 'designer ballgown size XXS under $5'

  Nothing matched 'designer ballgown' in size XXS at $5 or less. No listing mentions 'designer ballgown' at any size or price — try a broader word for the item, like 'tee', 'jeans', 'jacket', 'boots', or 'bag'.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_012', 'title': 'Oversized Crewneck Sweatshirt — Vintage Navy', 'description': 'Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.', 'category': 'tops', 'style_tags': ['vintage', 'basics', 'oversized', 'classic'], 'size': 'XL (fits oversized)', 'condition': 'good', 'price': 20.0, 'colors': ['navy'], 'brand': None, 'platform': 'thredUp'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]

$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit 1: Pair the Vintage Levi's 501 Jeans — Medium Wash with the White ribbed tank top, the Vintage black denim jacket, and the Chunky white sneakers.
Why it works: This creates a classic, effortless double-denim look that balances the fitted tank with the structured jacket and fresh sneakers.

Outfit 2: Pair the Vintage Levi's 501 Jeans — Medium Wash with the Black cropped zip hoodie, the Black combat boots, and the Black crossbody bag.
Why it works: The straight-leg cut of the 501s grounds the cropped hoodie and combat boots for an edgy, streetwear-inspired vibe.

$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
Grab those Levi's! Vintage 501s are the ultimate wardrobe foundation. For an effortless daytime look, pair them with a crisp white oversized button-down shirt left half-tucked, finished off with classic black leather loafers and a simple silver belt. If you are heading out for the evening, dress them up by adding a fitted black ribbed baby tee, layered with a vintage oversized leather blazer in rich brown, and complete the outfit with pointed-toe black boots. The medium wash and subtle knee fading make these jeans endlessly versatile for both casual and elevated streetwear aesthetics. At thirty-eight dollars, they are an absolute steal.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Just scored these Vintage Levi's 501 Jeans — Medium Wash on depop for only $38 and I am obsessed with the worn-in knee fading. I've been styling them with crisp white sneakers for the ultimate effortless, casual streetwear fit. Nothing beats a classic pair of Levi's for everyday wear. #thriftfinds #vintagelevis

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
Can't write a fit card without an outfit suggestion.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* Criterion 3 going through several drafts since I didn't understand how to build my own
- *What came back:* Templates to follow and a breakdown on what made the first two criteria successful 
- *What I changed:* I changed some of the formatting for what Claude gave me because I wanted it to fit with my own words and personal reflection

**Moment 2**

- *What I asked for:* Helping me check enviornment values to make sure it was going with what the guidelines said I was supposed to do
- *What came back:* Claude explained to me that I shared my key in the wrong place. It corrected these changes.
- *What I changed:* I made sure to check with my human eyes that I could understand these changes and edits to the env file and it all worked out.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
