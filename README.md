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

**Unit 4: Moment 3 (the MCP move)**

- *What I asked for:* An explanation of what "uncomment the block" meant in `mcp_server.py`, and help pointing `agent.py` at the server.
- *What came back:* Claude explained that `#` turns a line off and that Ctrl + / toggles a whole block. It also caught a mistake I made: I had replaced the `from tools import ...` line instead of adding the `call_tool` import below it, which would have crashed the agent the first time a search found something.
- *What I changed:* I fixed the imports myself. When Claude pointed out that `_no_results_message` also called `search_listings` directly, I asked whether the homework required changing those lines. It said no, and gave me two options. I chose to move them to MCP too, so every search goes through the server.

**Unit 4: Moment 4 (testing honestly)**

- *What I asked for:* Help running Milestones 3–5: scenarios, five tries per criterion, scoring, and one improvement.
- *What came back:* Claude ran the evals and scored them with fixed rules instead of eyeballing. While writing the diagnosis, it said the empty-wardrobe fit card made up clothes "5 of 5" times. When it scored the same cards with a fixed rule in Milestone 5, the real number was 2 of 5.
- *What I changed:* We corrected the README to 2 of 5 before measuring the fix. That taught me to trust a counted rule over a summary, even an AI's summary. I also learned why my broken-key test didn't fail at first: VS Code had loaded the old key into my terminal, and a repeated query came from the cache.

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
| 1. A matching query completes all three tools and returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before `suggest_outfit` and names what to change | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item passed to `suggest_outfit` is `session["selected_item"]` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card mentions the price and is 2–4 sentences | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Response in under a minute from the `ask` command | 4 of 5 | PASS (7.0s) | PASS (6.8s) | PASS (15.9s) | PASS (6.9s) | PASS (6.7s) | MET (5/5) |

**How the tries were run**

- Criteria 1–4: `python run_eval.py --label before`, with caching off and
  temperature 0.9 (40 model calls). Full output:
  [results/run_2026-10-14_0157_before.md](results/run_2026-10-14_0157_before.md).
  The scenarios are in `scenarios.py`.
- Criterion 5: `run_eval.py` doesn't record time, so I timed five separate
  `python app.py ask 'corduroy wide-leg pants'` runs with `AI201_CACHE=0`,
  from launching the command to it exiting. Full output:
  [results/run_2026-10-14_criterion5_timing_before.txt](results/run_2026-10-14_criterion5_timing_before.txt).

**How each try was scored**

1. PASS if the run didn't crash or stop early, and the trace shows all three
   tools with a non-empty fit card.
2. PASS if `session["error"]` is set, the trace has no `suggest_outfit` step,
   and the message suggests a change.
3. PASS if the trace's `select_item` output and `suggest_outfit` input are the
   same listing. The trace prints title, price, and platform rather than the
   `id`, so this compares those instead of the id.
4. PASS if the card contains the listing's price (for example "$30") and has 2–4
   sentences, counting sentence-ending `.` `!` `?` with hashtags removed.
5. PASS if the command finished in under 60 seconds with a fit card or an error
   message.

**Real output from one try per criterion**

Criterion 1, Try 1: `agent.py::run_agent` (fit card from `tools.py::create_fit_card`)

```
- selected_item: Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
- search_results: 10

[1] parse_query
[2] search_listings (via MCP)
      out: 10 items: Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style, Y2K Baby Tee — Butterfly Print … +7 more
      →    branch: results found, continuing
[3] select_item
      out: Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
      →    swapped a fair top result for a better one
[4] suggest_outfit
[5] create_fit_card

Fit card:
Scored this vintage-style Graphic Tee — 2003 Tour Bootleg Style on depop for just $24, and the worn-in cotton is honestly unmatched. I love throwing it on with baggy dark-wash jeans and combat boots for that effortless, heavy grunge-streetwear vibe. #thriftfinds #streetwear
```

Criterion 2, Try 1: `agent.py::run_agent` (message from `agent.py::_no_results_message`)

```
[1] parse_query
      in:  designer ballgown size XXS under $5
[2] search_listings (via MCP)
      out: [] (empty)
      →    branch: empty, stopping

stopped early: yes — Nothing matched 'designer ballgown' in size XXS at $5 or less. No listing mentions 'designer ballgown' at any size or price — try a broader word for the item, like 'tee', 'jeans', 'jacket', 'boots', or 'bag'.
```

Criterion 3, Try 1: `agent.py::run_agent` (trace from `trace.py::step`)

```
[3] select_item
      in:  top result condition: good
      out: Suede Chelsea Boots — Tan ($44.0, poshmark)
      →    kept the top result
[4] suggest_outfit
      in:  Suede Chelsea Boots — Tan ($44.0, poshmark)
```

Criterion 4, Try 1: `tools.py::create_fit_card` (listing price $30)

```
I scored this gorgeous 90s Silk Slip Dress — Floral, Midi Length on depop for just $30 and I am obsessed. I love styling it with an oversized grey crewneck and combat boots for that ultimate grungy, 90s contrast. #thriftfinds #vintagestyle
```

Criterion 5, Try 3: `app.py::cmd_ask`, the slowest try (15.9s), which hit a rate-limit wait

```
[3] select_item
      out: Corduroy Wide-Leg Pants — Rust ($32.0, depop)
  [rate limit] service pushed back. Waiting 9s (attempt 1 of 5). This is the limiter doing its job, not a bug.
[4] suggest_outfit
[5] create_fit_card

  Fit card: I scored these Corduroy Wide-Leg Pants — Rust on depop for just $32, and they instantly unlocked my ultimate 70s earth-tone vibe. I love wearing them with a fitted tank and combat boots, but they look just as good dressed down with a cozy oversized crewneck. #thriftedstyle #depopseller

3 model calls this session, 770 prompt + 185 output tokens
```

**Diagnostic run (not one of the five):** the empty-wardrobe scenario
(`denim jacket under $50`, empty wardrobe) completed 5 of 5 with general styling
advice. In 2 of the 5, though, the fit card described styling the jacket with
clothes the user doesn't own, for example "when I style it over an olive green
slip dress with chunky combat boots".

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
| 1 | A matching query completes all three tools and returns a fit card | 4 of 5 | MET (5/5) | All 5 traces show steps 1–5 with a non-empty fit card and no `session["error"]`. 5 passes is at least 4. |
| 2 | An impossible query stops before `suggest_outfit` and names what to change | 5 of 5 | MET (5/5) | All 5 traces end at step 2 with `[] (empty)`, there's no `suggest_outfit` step, and every message says to "try a broader word". |
| 3 | The item passed to `suggest_outfit` is `session["selected_item"]` | 5 of 5 | MET (5/5) | In all 5 traces, step 3's output and step 4's input are the same listing (Suede Chelsea Boots — Tan, $44, poshmark). This compares title, price, and platform, because the trace doesn't print the `id` (see below). |
| 4 | Fit card mentions the price and is 2–4 sentences | 4 of 5 | MET (5/5) | All 5 cards contain "$30" and have exactly 2 sentences once the hashtags are removed. I checked the script's count by reading every card. |
| 5 | Response in under a minute from the `ask` command | 4 of 5 | MET (5/5) | Times were 7.0s, 6.8s, 15.9s, 6.9s, and 6.7s, all under 60s and all ending in a fit card. |

**Diagnoses**

**No criterion missed, so there's no miss to diagnose.** Honestly, though, the
clean sweep says more about my targets than about the agent. Here's where each
target was too low or measured the wrong thing.

- **Criterion 5 was too loose. This is the one I'd tighten first.** I guessed
  15–30 seconds for a normal run and set the bar at 60. The real runs took about
  7 seconds, and even the slowest, with a rate-limit wait, took 15.9. A target
  of "under 20 seconds in 4 of 5" would still leave room for a rate-limit wait
  and would actually test something.
- **Criterion 4 was easy to meet because of how the prompt works.**
  `tools.py::create_fit_card` puts the exact formatted price ("$30") into the
  prompt and asks for it by name, so the model copies it every time. All 5
  cards came out at exactly 2 sentences, the bottom of the allowed range. A
  stricter target would be 5 of 5.
- **Criterion 3 can't fail with my current code.** `agent.py::run_agent` passes
  `session["selected_item"]` straight into `suggest_outfit`, so the handoff is
  the same object every time and could only break if the code changed. It also
  names the `id`, which the trace doesn't print, so I scored it by title, price,
  and platform instead. A better version would check that the outfit *text* is
  about the selected item. On these runs, the outfit named it by exact title in
  3 of 5 tries and as "suede Chelsea boots" in the other 2, so it was always
  the same item.
- **Criterion 1 measured the wrong thing.** It checks that the loop *finishes*,
  not that it found what the user asked for. My scenario also used an easy
  query, so it never tested the regex risk my reason named ("nothing over thirty
  bucks"). See problem B below: a run that styles shoes for someone who asked
  for a jacket still counts as a PASS here.
- **Criterion 2 was strict for a good reason.** Nothing on that path is random,
  so 5 of 5 was the right target and anything less would mean the branch was
  broken.

**Two real problems the criteria didn't catch**

Both turned up in this unit's testing, outside the five criteria. Each names
the step and the mechanism.

**A. The fit card makes up clothes when the wardrobe is empty.**
*Step: `tools.py::create_fit_card`. Place: the model's output, caused by the
prompt.* In the empty-wardrobe diagnostic run, `suggest_outfit` correctly gave
general advice in 5 of 5 tries. But 2 of the 5 fit cards wrote as if the user
already owned other pieces: "when I style it over an olive green slip dress
with chunky combat boots" (try 2) and "I love throwing it over a graphic tee
and baggy cargo pants" (try 4). My manual empty-wardrobe run in Milestone 2 did
the same ("I've been styling it with baggy distressed denim…"). The mechanism: `suggest_outfit`'s empty-wardrobe
prompt says "Don't say or imply that they already own anything", but
`create_fit_card`'s prompt has no such rule. It only ever gets the outfit text,
so it doesn't know the wardrobe was empty, and its "first person" rule turns
"pair it with a slip dress" into "I style it with my slip dress". The tool
works; the prompt is missing information it needs.

**B. The search returns a different kind of item instead of nothing.**
*Step: `tools.py::search_listings` (via MCP), and then the loop's empty
branch.* `python app.py ask 'black leather jacket under $60'` returned
**Platform Mary Janes — Black Patent ($55)**. The only leather jacket in the
data, "90s Leather Bomber — Black", costs $75, so the price filter removed it.
The search then scores any word overlap across title, description, and colors,
and the Mary Janes match "black" and "leather". The result list wasn't empty,
so the empty-search branch never fired and the agent styled shoes for someone
who asked for a jacket.

**The pattern:** both problems are about *content*, not *shape*. My criteria
checked that things ran, stopped, and had the right parts (a fit card, a price,
2–4 sentences). Nothing checked whether the content was true to the user's
situation: what they asked for, and what they own. That's where my agent
actually breaks.

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
$ python app.py ask 'vintage graphic tee under $30' --trace

[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style, Y2K Baby Tee — Butterfly Print … +7 more
      →    branch: results found, continuing
[3] select_item
      in:  top result condition: fair
      out: Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
      →    swapped a fair top result for a better one
[4] suggest_outfit
      in:  Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
      out: Outfit one: Pair the Graphic Tee — 2003 Tour Bootleg Style tucked into the Baggy straight-leg jeans, dark wash…
[5] create_fit_card
      in:  Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
      out: Scored this Graphic Tee — 2003 Tour Bootleg Style for just $24 on depop and it has the absolute best worn-in f…
```

Step 3 shows the second branch firing: the top search result was in "fair"
condition, so the loop picked the next "good" or "excellent" result instead.

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace

[1] parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    branch: empty, stopping

  Nothing matched 'designer ballgown' in size XXS at $5 or less. No listing mentions 'designer ballgown' at any size or price — try a broader word for the item, like 'tee', 'jeans', 'jacket', 'boots', or 'bag'.

0 model calls this session
```

The empty run stops after step 2. `suggest_outfit` and `create_fit_card` never
run, and no model calls are made.

**On the MCP move:** `search_listings` is now registered as a tool in
`mcp_server.py`, and `agent.py` no longer imports it. Every search goes through
`mcp_client.call_tool`: the main search in `run_agent` and the three re-searches
in `_no_results_message` that work out which constraint emptied the results.
`suggest_outfit` and `create_fit_card` are still called directly. The results
came back the same as in Unit 3 (same Graphic Tee, $24, on depop). The one
difference is speed: each MCP call starts the server, so an empty search,
which makes up to 4 calls, takes a few seconds longer.

### Failure Modes

All three triggered on purpose. None of them crashed or went silent, so no new
handlers were needed.

**1. Empty search**: `python app.py ask 'designer ballgown size XXS under $5'`

```
  Nothing matched 'designer ballgown' in size XXS at $5 or less. No listing mentions 'designer ballgown' at any size or price — try a broader word for the item, like 'tee', 'jeans', 'jacket', 'boots', or 'bag'.
```

The loop stops before `suggest_outfit`. The message names what failed (no
listing mentions the item) and what to try (a broader word). Handled by
`agent.py::_no_results_message`.

**2. Empty wardrobe**: `python app.py ask 'vintage graphic tee under $30' --empty-wardrobe`

```
  Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

  Outfit:   Lean into the grunge and streetwear aesthetic by pairing the tee with baggy, light-wash distressed denim jeans to create a cool contrast with the black top. Add a chunky black leather belt and worn-in skate sneakers like canvas lows or chunky retro runners. For cooler weather, layer an oversized forest green zip-up hoodie or a distressed black leather jacket over the top. Accessorize with a silver chain necklace and a beanie to complete the effortless, lived-in look.
```

No crash and no empty string. `suggest_outfit` gives general styling advice
instead of naming wardrobe pieces. One thing I noticed: the fit card still said
"I've been styling it with baggy distressed denim…", as if the user owns
clothes they don't have.

**3. Model unavailable**: changed one character of `GEMINI_API_KEY` in `.env`,
then ran a new query, `python app.py ask 'white sneakers under $40'`

```
ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
```

No hang and no stack trace. The message names what broke (the key was rejected)
and what to do (check `.env` or make a new key). Handled by `generate.py`, which
raises `ModelUnavailable`, and `app.py`, which prints it as one line.

Two things got in the way while triggering this one. VS Code had already loaded
the old key into the terminal, and `load_dotenv` doesn't overwrite a value
that's already set, so I had to run `Remove-Item Env:GEMINI_API_KEY` first. And
re-running a query I'd already asked came back from the cache, so it needed a
query I'd never run before.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** I added one rule to the prompt in
`tools.py::create_fit_card`. Nothing else changed.

```python
"- The outfit is a styling idea, not something they've already worn. Don't claim to own or have worn any other piece — say how you'd style it or plan to.\n"
```

**Which failure it was meant to fix:** problem A from my diagnosis. With an
empty wardrobe, the fit card sometimes claimed the user already owned other
clothes ("when I style it over an olive green slip dress…"). I picked this one
because the diagnosis pointed at a single place: `suggest_outfit`'s prompt has
a "don't imply they own anything" rule, and `create_fit_card`'s prompt didn't.
I fixed it with a prompt rule rather than by passing the wardrobe into
`create_fit_card`, because that would have changed the tool's inputs, and the
unit allows one change.

**How I measured it:** none of my five criteria covers this, so I scored the
empty-wardrobe diagnostic row (`denim jacket under $50`, empty wardrobe) with a
fixed rule, before and after. A try **FAILs** if the fit card says "I" followed by
a present or past styling verb ("I style", "I've been wearing", "I love
throwing"), or "my" followed by a clothing item ("my slip dress"). Future or
hypothetical phrasing ("I'm planning to style", "I'd pair") **passes**. Then I
re-ran all five criteria to check that nothing else broke.

### Run Log — After

`python run_eval.py --label after` (caching off, temperature 0.9):
[results/run_2026-10-14_0208_after.md](results/run_2026-10-14_0208_after.md).
Criterion 5 timing:
[results/run_2026-10-14_criterion5_timing_after.txt](results/run_2026-10-14_criterion5_timing_after.txt).
Each try was scored with the same rules as the before run.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools and returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before `suggest_outfit` and names what to change | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item passed to `suggest_outfit` is `session["selected_item"]` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card mentions the price and is 2–4 sentences | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Response in under a minute from the `ask` command | 4 of 5 | PASS (7.2s) | PASS (7.2s) | PASS (6.7s) | PASS (6.7s) | PASS (6.7s) | MET (5/5) |
| Empty-wardrobe fit card doesn't claim the user owns other pieces _(diagnostic, not one of my five)_ | — | PASS | PASS | PASS | PASS | PASS | 5/5 |

**Before and after, side by side**

| | Before | After |
|---|---|---|
| 1. Matching query → fit card | 5/5 MET | 5/5 MET |
| 2. Impossible query stops early | 5/5 MET | 5/5 MET |
| 3. Selected item reaches `suggest_outfit` | 5/5 MET | 5/5 MET |
| 4. Price + 2–4 sentences | 5/5 MET (all 2 sentences) | 5/5 MET (four at 2 sentences, one at 3) |
| 5. Under a minute | 5/5 MET (6.7–15.9s) | 5/5 MET (6.7–7.2s) |
| **Empty wardrobe: no made-up ownership** | **3/5** | **5/5** |

Before, failing tries 2 and 4:

```
…It has such a cool, effortless vibe when I style it over an olive green slip dress with chunky combat boots…
…I love throwing it over a graphic tee and baggy cargo pants for an effortlessly cool, nineties-inspired fit…
```

After, the same scenario, try 5 (it suggests the same slip dress, but as a plan):

```
Scored this vintage Wrangler Denim Jacket — Light Wash, Cropped on poshmark for just $42, and I'm already planning to style it over an olive green slip dress with knee-high boots. The structured shoulders will give such a cool edge to the romantic streetwear vibe. #thriftfind #streetwear
```

**Did it help, and how do I know:** yes, for the failure it targeted. The
empty-wardrobe cards went from 3/5 to 5/5 on the ownership rule, and all five
criteria stayed MET. It wasn't free, though, and here's what got worse:

- **The cards got more alike.** Most after cards open with nearly the same
  line: "I'm already dreaming up ways to style it" or "I'm already planning
  how to…", followed by "I'm thinking of pairing it with…". The before cards
  varied more. The new rule pushed the model toward one safe template.
- **The rule also applies when it isn't needed.** With the example wardrobe,
  the user *does* own the jeans and boots, but the cards now talk about them as
  plans ("I'm thinking of pairing it with the baggy straight-leg jeans"). The
  prompt can't tell an empty wardrobe from a full one, because it never sees
  the wardrobe.
- **One new rule break.** Criterion 4, try 2 switched to second person partway
  through ("Alternatively, you could throw an oversized crewneck right over
  it…"), which breaks the prompt's "first person" rule. It didn't fail
  criterion 4, which only checks price and sentence count, but it didn't
  happen in the before run.
- **A borderline pass.** Empty-wardrobe try 3 ends with "I can't wait to throw
  it over everything in my closet". That passes my rule because it doesn't name
  a specific item, but it still assumes a closet the user hasn't saved.

Criterion 5's after times were tighter (no rate-limit wait this time), but that
comes from the rate limit, not from my change.


---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

**No criterion is still missed, but the agent isn't finished.** All five
criteria were MET before and after the fix. As Verdicts and Diagnoses explains,
that's partly because my targets were too easy. These are the problems I know
are still there.

**1. The search returns the wrong kind of item instead of nothing (problem B).**
"Black leather jacket under $60" still returns Platform Mary Janes, because
`search_listings` counts any matching word and the only jacket costs $75. What
I'd do: score the item type (jacket, boots, tee) above colors and materials, and
return `[]` if the type doesn't match at all. Then the empty-search branch would
fire and tell the user to raise their price to $75. I stopped because this unit
allows one improvement, and changing the ranking could affect criteria 1 and 2,
so it would need its own before/after run.

**2. The fit card prompt can't tell an empty wardrobe from a full one.**
My fix stopped the made-up clothes, but it also made the cards sound alike, and
it treats pieces the user really owns as "plans". The real fix is to pass a
flag into `create_fit_card` saying whether the wardrobe was empty, and only add
the rule then. I didn't do it because it changes the tool's inputs, which means
updating my Tool Inventory and the MCP-facing description. That's more than one
change.

**3. My criteria check shape, not content.**
Nothing I measured checks that the item matches what the user asked for. What
I'd do next: tighten criterion 5 to "under 20 seconds in 4 of 5", and add a
criterion like "the selected item's category matches the noun in the query, 5 of
5". I'd test it with tricky phrasings like "nothing over thirty bucks". I
stopped here because the assignment says to revise criteria only when they
can't be measured, not to add new ones mid-test.

**On the MCP move:** `search_listings` now runs behind `mcp_server.py`, and
`agent.py` calls it with `mcp_client.call_tool`. Results were identical to Unit 3.
The only difference is speed: every call starts the server, so an empty search
(up to 4 calls) takes a few seconds longer.


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

---

## Capstone

**What This Extends**

This extends FitFindr, my Unit 3–4 thrifting agent (search → outfit → fit card, with `search_listings` behind MCP). Before this unit it only ran from the command line, and `serve.py` was the untouched starter: any bad request body or model failure turned into a 500 with a raw Python exception in it. What's new is a hardened `POST /ask` endpoint that rejects bad input with a 400, turns a model outage into a 503 with a readable message, and writes one structured log record for every request, including the failed ones.

**The Shape**

Shape B — harden against failure. I'm adding one layer to `serve.py`: input validation before the agent runs, and failure handling around it, so the bad path gives a clear answer instead of a stack trace. Out of scope: I'm not fixing the search ranking bug from Unit 4 (the "black leather jacket" query returning shoes), I'm not changing any of the three tools or their prompts, and I'm not hosting it online or adding a UI.

**Running It**

Path B, local with logs. `python serve.py` starts it on `http://localhost:5000`, and every request is logged to `logs/requests.jsonl`. The exact steps, the environment (Python 3.13.1, pinned `requirements.txt`, no model files), and a clean-clone walkthrough are in [RUNNING.md](RUNNING.md#capstone-run-path--path-b-local-with-logs). I tested it from a fresh `git clone` into a new folder, and it worked on the first try. The one snag was that PowerShell 5.1 shows the log's em-dashes garbled unless you pass `-Encoding UTF8`, so I added that to RUNNING.md.

**Instrumentation**

`serve.py::ask` writes one JSON line to `logs/requests.jsonl` for every `POST /ask`, whether it's a success, a 400, a 503, or a 500. Each record has these fields: `ts` (UTC timestamp), `request_id`, `query` (what came in), `wardrobe_items`, `status` (HTTP code), `outcome` (`ok` / `no_match` / `bad_request` / `model_unavailable` / `server_error`), `selected_item`, `price`, `fit_card` (what came out, first 160 characters), `error` (the message the caller saw), `detail` (the real exception, which is logged but never sent to the caller), `model_calls`, `prompt_tokens`, `output_tokens`, and `duration_ms` (how long it took). Model calls and tokens are the difference in `generate.call_count()` / `generate.token_counts()` before and after the run. That only works because `serve.py` runs one request at a time.

Thirteen entries from a real session (server started with `AI201_CACHE=0`; 10 runs from `measure_cost.py`, then two bad requests and one no-match by hand):

```
{"ts": "2026-11-14T20:13:01.533+00:00", "request_id": "ecde7830", "query": "vintage graphic tee under $30", "wardrobe_items": 10, "status": 200, "outcome": "ok", "selected_item": "Graphic Tee — 2003 Tour Bootleg Style", "price": 24.0, "fit_card": "scored this sick Graphic Tee — 2003 Tour Bootleg Style for just $24 on depop and I'm already obsessed. I’m totally planning to tuck it into some wide-leg khaki …", "error": null, "detail": null, "model_calls": 2, "prompt_tokens": 821, "output_tokens": 190, "duration_ms": 5408}
{"ts": "2026-11-14T20:13:08.979+00:00", "request_id": "6c7d5a4f", "query": "denim jacket under $50", "wardrobe_items": 10, "status": 200, "outcome": "ok", "selected_item": "Denim Jacket — Light Wash, Cropped", "price": 42.0, "fit_card": "Scored this vintage Wrangler Denim Jacket — Light Wash, Cropped on poshmark for just $42 and I'm already dreaming up outfits. I'm planning to lean into a 90s st…", "error": null, "detail": null, "model_calls": 2, "prompt_tokens": 827, "output_tokens": 205, "duration_ms": 3554}
{"ts": "2026-11-14T20:13:14.571+00:00", "request_id": "aaa47ccb", "query": "silk slip dress", "wardrobe_items": 10, "status": 200, "outcome": "ok", "selected_item": "90s Silk Slip Dress — Floral, Midi Length", "price": 30.0, "fit_card": "I just scored this gorgeous 90s Silk Slip Dress — Floral, Midi Length on depop for only $30, and I’m already planning how to style it. I think it would look so …", "error": null, "detail": null, "model_calls": 2, "prompt_tokens": 843, "output_tokens": 205, "duration_ms": 2621}
{"ts": "2026-11-14T20:13:19.262+00:00", "request_id": "ab400d42", "query": "suede chelsea boots", "wardrobe_items": 10, "status": 200, "outcome": "ok", "selected_item": "Suede Chelsea Boots — Tan", "price": 44.0, "fit_card": "I just scored these amazing Suede Chelsea Boots — Tan on poshmark for only $44, and I'm already dreaming up ways to style them. I'm totally planning to pair the…", "error": null, "detail": null, "model_calls": 2, "prompt_tokens": 801, "output_tokens": 186, "duration_ms": 2650}
{"ts": "2026-11-14T20:13:23.964+00:00", "request_id": "5fc90cbc", "query": "corduroy wide-leg pants", "wardrobe_items": 10, "status": 200, "outcome": "ok", "selected_item": "Corduroy Wide-Leg Pants — Rust", "price": 32.0, "fit_card": "I am obsessed with the vibrant autumn energy of these Corduroy Wide-Leg Pants — Rust I just scored on depop for $32. I'm totally planning to style them with a f…", "error": null, "detail": null, "model_calls": 2, "prompt_tokens": 817, "output_tokens": 202, "duration_ms": 2806}
{"ts": "2026-11-14T20:13:28.819+00:00", "request_id": "a47d89d1", "query": "platform sneakers size 8", "wardrobe_items": 10, "status": 200, "outcome": "ok", "selected_item": "Platform Sneakers — White Chunky Sole", "price": 48.0, "fit_card": "I just scored these Platform Sneakers — White Chunky Sole on Poshmark for $48 and I'm already obsessed with them. I'm planning to style them with a black croppe…", "error": null, "detail": null, "model_calls": 2, "prompt_tokens": 804, "output_tokens": 179, "duration_ms": 2710}
{"ts": "2026-11-14T20:13:33.550+00:00", "request_id": "af9b7062", "query": "90s track jacket in size M", "wardrobe_items": 10, "status": 200, "outcome": "ok", "selected_item": "90s Track Jacket — Navy/White Stripe", "price": 45.0, "fit_card": "I am obsessed with this vintage Champion 90s Track Jacket — Navy/White Stripe that I just scored on poshmark for only $45. I can't wait to style it with a fitte…", "error": null, "detail": null, "model_calls": 2, "prompt_tokens": 809, "output_tokens": 178, "duration_ms": 2503}
{"ts": "2026-11-14T20:13:38.098+00:00", "request_id": "d0e750f3", "query": "cargo pants under $40", "wardrobe_items": 10, "status": 200, "outcome": "ok", "selected_item": "Corduroy Wide-Leg Pants — Rust", "price": 32.0, "fit_card": "I just scored these gorgeous Corduroy Wide-Leg Pants — Rust on depop for $32 and I'm already dreaming up ways to style them. I'd love to pair them with a cozy g…", "error": null, "detail": null, "model_calls": 2, "prompt_tokens": 799, "output_tokens": 187, "duration_ms": 28142}
{"ts": "2026-11-14T20:14:08.292+00:00", "request_id": "a668313d", "query": "crossbody bag", "wardrobe_items": 10, "status": 200, "outcome": "ok", "selected_item": "Mini Shoulder Bag — Tan Leather", "price": 38.0, "fit_card": "Score! I just found this gorgeous Mini Shoulder Bag — Tan Leather on Poshmark for only $38, and I'm already dreaming up ways to wear it. I'm totally planning to…", "error": null, "detail": null, "model_calls": 2, "prompt_tokens": 774, "output_tokens": 172, "duration_ms": 2683}
{"ts": "2026-11-14T20:14:13.016+00:00", "request_id": "7de30aa7", "query": "oversized crewneck sweatshirt", "wardrobe_items": 10, "status": 200, "outcome": "ok", "selected_item": "Oversized Crewneck Sweatshirt — Vintage Navy", "price": 20.0, "fit_card": "Scored this gorgeous Oversized Crewneck Sweatshirt — Vintage Navy on thredUp for only $20 and I'm obsessed with the authentic faded look. I'm totally planning t…", "error": null, "detail": null, "model_calls": 2, "prompt_tokens": 785, "output_tokens": 171, "duration_ms": 3434}
{"ts": "2026-11-14T20:14:18.517+00:00", "request_id": "dfe684fa", "query": "123", "wardrobe_items": null, "status": 400, "outcome": "bad_request", "selected_item": null, "price": null, "fit_card": null, "error": "'query' must be text, not int.", "detail": null, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0, "duration_ms": 0}
{"ts": "2026-11-14T20:14:18.533+00:00", "request_id": "524c3c8e", "query": null, "wardrobe_items": null, "status": 400, "outcome": "bad_request", "selected_item": null, "price": null, "fit_card": null, "error": "The body must be a JSON object, e.g. {\"query\": \"vintage graphic tee under $30\"}", "detail": null, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0, "duration_ms": 0}
{"ts": "2026-11-14T20:14:18.538+00:00", "request_id": "f23ad9e5", "query": "designer ballgown size XXS under $5", "wardrobe_items": 10, "status": 200, "outcome": "no_match", "selected_item": null, "price": null, "fit_card": null, "error": "Nothing matched 'designer ballgown' in size XXS at $5 or less. No listing mentions 'designer ballgown' at any size or price — try a broader word for the item, like 'tee', 'jeans', 'jacket', 'boots', or 'bag'.", "detail": null, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0, "duration_ms": 2360}
```

The last three are the failure path. Two **rejected inputs** (`{"query": 123}` and a body that isn't JSON) got a 400 in 0 ms with 0 model calls, and an impossible query got a 200 with `error` set and no model calls. The 8th entry (`cargo pants under $40`, 28,142 ms) is the server's own rate limiter. It was the 16th model call inside one minute, and the server log printed `[rate limit] 15 requests used this minute. Waiting 26s.` A model-outage 503 shows up in the test runs below.

**What It Costs**

Measured with `python measure_cost.py` against a server started with the cache off. It sends 10 different matching queries and averages the 10 log records they write. Token counts come from the API's own `usage_metadata` (via `generate.token_counts()`), not from a pricing page.

| Per run (average of 10) | |
|---|---|
| Model calls | 2.0 |
| Prompt tokens | 808 (774–843) |
| Output tokens | 188 (171–205) |
| **Total tokens** | **996** |
| Wall time | 5.65 s mean, 2.7 s median (2.50–28.14 s; the 28 s run was a rate-limit wait) |
| API spend | $0. The key is on Gemini's free tier |

*A hundred people a day:* 100 runs × 996 tokens = **99,600 tokens a day** (80,800 prompt + 18,800 output), 100 × 2 = **200 model calls a day**, and 100 × 5.65 s = **565 s (about 9.4 minutes) of server time a day**. The actual spend stays $0 on the free tier. The real limit is the rate: at 15 calls a minute the server can finish about 7 runs a minute, so if more than 7 of those 100 people arrive in the same minute, the 8th waits about 26 s, like the `cargo pants` run above.


**Run Log and Verdicts**

Each trial is one `python capstone_eval.py --label before --trial N`, run three times in a row with nothing changed in between. Every trial sends 16 real HTTP requests to `serve.py` (cache off, temperature 0.9) and scores them against the wording in [criteria.md](criteria.md). Raw output: [trial 1](results/capstone_before_trial1.md), [trial 2](results/capstone_before_trial2.md), [trial 3](results/capstone_before_trial3.md).

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| C1. Bad input → 400 naming the field, 0 model calls | 6 of 6 | 6/6 | 6/6 | 6/6 | MET |
| C2. Model outage → 503 in <10 s, no exception name or `.env`/key in the body | 5 of 5 | 0/5 | 0/5 | 0/5 | MISSED |
| C3. Every request → exactly one complete log line, status matches | 16 of 16 | 16/16 | 16/16 | 16/16 | MET |
| C4. Matching query → 200, no error, fit card contains `$24` | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| C5. Warm matching request under 10,000 ms (log `duration_ms`) | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

C5 durations (ms): run 1 6064, 3206, 2533, 2924, 2750 · run 2 5242, 2405, 2784, 2427, 2671 · run 3 5180, 2546, 2503, 2931, 2519. The fit cards were different every time (for example "Scored this amazing Graphic Tee…", "Stumbled across this Graphic Tee…", "Just snagged this Graphic Tee…"), so the model really was re-run.

**Real output, one per criterion (run 1)**

C1: `serve.py::_validate`, logged by `serve.py::_log`. This is the 51-item wardrobe:
```
{"ts": "2026-11-14T20:16:30.245+00:00", "request_id": "be24d85f", "query": "tee", "wardrobe_items": null, "status": 400, "outcome": "bad_request", "selected_item": null, "price": null, "fit_card": null, "error": "'wardrobe' has 51 items; the limit is 50.", "detail": null, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0, "duration_ms": 0}
```
C2 (the miss): `serve.py::ask`'s `ModelUnavailable` handler. The message text comes from `generate.py::_explain`:
```
{"ts": "2026-11-14T20:17:02.022+00:00", "request_id": "7fc90551", "query": "vintage graphic tee under $30", "wardrobe_items": 10, "status": 503, "outcome": "model_unavailable", "selected_item": null, "price": null, "fit_card": null, "error": "The styling model is unavailable right now: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.", "detail": "ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.", "model_calls": 1, "prompt_tokens": 0, "output_tokens": 0, "duration_ms": 3865}
```
C3: run 1's 16 requests wrote 16 lines. The first and last (`serve.py::_log`):
```
{"ts": "2026-11-14T20:16:20.032+00:00", "request_id": "27657dd3", "query": null, "wardrobe_items": null, "status": 400, "outcome": "bad_request", "selected_item": null, "price": null, "fit_card": null, "error": "The body must be a JSON object, e.g. {\"query\": \"vintage graphic tee under $30\"}", "detail": null, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0, "duration_ms": 0}
```
C4 and C5: `agent.py::run_agent` behind `serve.py::ask`:
```
{"ts": "2026-11-14T20:16:55.205+00:00", "request_id": "35eb7716", "query": "vintage graphic tee under $30", "wardrobe_items": 10, "status": 200, "outcome": "ok", "selected_item": "Graphic Tee — 2003 Tour Bootleg Style", "price": 24.0, "fit_card": "Just scored this amazing Graphic Tee — 2003 Tour Bootleg Style for only $24 on depop and I’m already planning out how to wear it. I think it would look so cool …", "error": null, "detail": null, "model_calls": 2, "prompt_tokens": 826, "output_tokens": 191, "duration_ms": 2750}
```

**Diagnosis: C2 missed 15 of 15.** Two of C2's three conditions held every time: all 15 came back as a 503, and the slowest took 5.99 s on the client. All 15 failed the third condition, because the body says "Check GEMINI_API_KEY in your .env file". *Stage:* the `except ModelUnavailable` handler in `serve.py::ask`. *Mechanism:* the handler builds the caller's message with `f"...: {exc}"`, and the exception's text is written by `generate.py::_explain` for the CLI, where the person reading it *is* the one who owns the `.env`. Over HTTP, the person reading it is a stranger who can't fix the key, and the message tells them how the server is configured. The handler reused a message written for a different audience. Because it's code, not the model, it fails the same way 15 of 15.

**What else the runs showed (not a miss):** every client-side time was about 2 s longer than the server's own `duration_ms` (a 400 that took 0 ms on the server took 2.03 s for the caller). I checked it: on this Windows machine `urllib.request.urlopen('http://localhost:5056/health')` took 2.07 s and the same call to `127.0.0.1` took 0.0 s. `localhost` tries IPv6 `::1` first, Flask is only listening on IPv4 `0.0.0.0`, and the fallback costs 2 s. C5 uses the server's log, so it isn't affected. But C2's "under 10 s" was measured on the client and includes that 2 s.

**Pattern:** there's only one miss, so there's no cluster to find. The contrast is still worth noting. C1 and C3 only check messages and records that `serve.py` builds itself, and they held 3 of 3. C2 is the one place where `serve.py` passes along text it didn't write, and that's where it broke.

**The Improvement**

*What I changed:* one thing, in the `except ModelUnavailable` handler in `serve.py::ask`. The caller now gets a fixed sentence, "The styling model can't be reached right now. Your request was fine. Try again in a few minutes.", and the original exception text only goes into the log's `detail` field. I didn't change `generate.py::_explain`, because the CLI still needs the "check your .env" message. Its reader is the person who owns the key.

*Why:* the diagnosis put the C2 miss in that handler. It was passing through a message written for the CLI user to a web caller. Fixing it where `serve.py` hands text to the caller fixes the HTTP path without breaking the CLI.

*After, the same 503 in the log* (`serve.py::_log`, run 1). The caller sees `error`, the operator still has `detail`:
```
{"ts": "2026-11-14T20:21:07.479+00:00", "request_id": "877ed3cd", "query": "vintage graphic tee under $30", "wardrobe_items": 10, "status": 503, "outcome": "model_unavailable", "selected_item": null, "price": null, "fit_card": null, "error": "The styling model can't be reached right now. Your request was fine. Try again in a few minutes.", "detail": "ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.", "model_calls": 1, "prompt_tokens": 0, "output_tokens": 0, "duration_ms": 2949}
```

Second run log: `python capstone_eval.py --label after --trial N`, three times, same requests, same scoring. Raw output: [trial 1](results/capstone_after_trial1.md), [trial 2](results/capstone_after_trial2.md), [trial 3](results/capstone_after_trial3.md).

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| C1. Bad input → 400 naming the field, 0 model calls | 6 of 6 | 6/6 | 6/6 | 6/6 | MET |
| C2. Model outage → 503 in <10 s, no exception name or `.env`/key in the body | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| C3. Every request → exactly one complete log line, status matches | 16 of 16 | 16/16 | 16/16 | 16/16 | MET |
| C4. Matching query → 200, no error, fit card contains `$24` | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| C5. Warm matching request under 10,000 ms (log `duration_ms`) | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

**Before and after, side by side**

| Criterion | Before (runs 1/2/3) | After (runs 1/2/3) |
|---|---|---|
| C1 | 6/6, 6/6, 6/6 MET | 6/6, 6/6, 6/6 MET |
| C2 | **0/5, 0/5, 0/5 MISSED** | **5/5, 5/5, 5/5 MET** |
| C3 | 16/16 ×3 MET | 16/16 ×3 MET |
| C4 | 5/5 ×3 MET | 5/5 ×3 MET |
| C5 | 5/5 ×3 MET (2,405–6,064 ms) | 5/5 ×3 MET (2,351–5,556 ms) |

*Did it help:* yes. C2 went from 0 of 15 to 15 of 15, and nothing else moved. The 503 timing stayed the same too (3.0–5.2 s on the client, which includes the 2 s `localhost` delay). There is a trade-off, though: "try again in a few minutes" is true for a network blip or a rate limit, but a bad key never recovers by waiting. Before, a caller could at least tell the problem was the key. Now only someone reading `logs/requests.jsonl` can, so the fix only works if someone actually reads the log.

**What's Still Broken**

After the fix, all five criteria are MET, which means some targets were too easy. C5 was set too low. The slowest warm request in 30 tries was 6,064 ms and the median was about 2,550 ms, so I'd tighten it to "under 4,000 ms in 4 of 5". That still allows for the first request of each server, which ran 4.5–6.1 s every time because `generate.py` builds its client on the first call. C4 came out 30 of 30, so it should be 5 of 5. Two problems none of my criteria caught are also still there. On Windows, `localhost` adds 2 s to every request because of the IPv6 fallback (binding Flask to `::` as well would fix it). And a bad key now looks like a temporary outage to the caller, as described in The Improvement. I stopped there because the unit allows one improvement, and both of these would need their own before-and-after runs.

*What I'd do first with another unit:* stop the rate limiter from sleeping inside a web request. When a wait would be longer than a few seconds, I'd return a 503 with a `Retry-After` header instead. The 28-second `cargo pants` run in my logged session is the failure a real user would hit first at 100 people a day, and none of my five criteria sent more than 10 model calls in a minute, so the tests never reached it.

**How I Used AI**

**Moment 1: checking the "before" behavior**

- *What I asked for:* I asked Claude to harden `serve.py` so bad requests and model failures don't crash it.
- *What came back:* Before changing anything, Claude sent the original `serve.py` two bad requests (`{"query": 123}` and a wardrobe whose `items` was a string). Both crashed with a 500, and one sent `"AttributeError: 'str' object has no attribute 'get'"` back to the caller.
- *What I changed:* Seeing the crash first made me want C1 to list the exact six bad requests instead of just saying "bad input," so anyone could re-run it and score it the same way. I also kept the rule that a bad request must make 0 model calls, because sending junk to the model still costs tokens.

**Moment 2: the 2-second gap**

- *What I asked for:* I asked Claude to run my three test trials and score them.
- *What came back:* Claude noticed every client time was about 2 s longer than the server's `duration_ms`. It tested the cause instead of guessing: `localhost` took 2.07 s and `127.0.0.1` took 0.0 s.
- *What I changed:* I kept C5 measured from the server's log, because it's meant to measure my system, not the computer sending the request. I listed the 2-second delay under What's Still Broken instead of counting it as a miss, and I learned that on Windows `localhost` can be slower than `127.0.0.1`.
