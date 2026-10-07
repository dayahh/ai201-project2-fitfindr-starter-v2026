# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
I picked 4 of 5 because two things on this path can vary. My query parser is regex, so an unusual phrasing like "nothing over thirty bucks" can be misread, which turns a query that should match into an empty search. And suggest_outfit and create_fit_card both call the model, so a slow or failed response can stop a run before the fit card. Expecting 5 of 5 would mean assuming neither of those ever happens.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
I picked 5 of 5 because nothing on this path is random. search_listings always returns a list ([] when nothing matches, never None), the loop checks for that empty list with a plain if, and the message about what to change is built in code, not written by the model. The model is never called on this path, so the same impossible query gives the same result every time, and even one miss would mean the branch is broken.

---

## 3. State is preserved across the tool handoff
Given a query that matches a listing, the item passed to `suggest_outfit` has the same `id` as `session["selected_item"]` in 5 of 5 tries. The same listing must reach the second tool; a different item, a stale result, or an empty dict is a failure.

**Why this target:**
I picked 5 of 5 because passing the item to suggest_outfit is a deterministic handoff, with no model randomness involved. Criterion 1 allows a miss because wording can vary, but this step does the same thing every run, so even one wrong item would mean the session state is wrong.

---

## 4. Something about the fit card

Given a query that matches a listing, the caption must mention the item’s price (regardless of format) and it must stay between 2 and 4 sentences in 4 of 5 tries.

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->



**Why this target:**
I picked 4 of 5 because the model is allowed to vary in wording, but the fit card still needs to keep the basic facts the user would actually use to decide on the item. A caption that omits the price is not just stylistically weaker; it fails the core purpose of the tool, which is to help someone judge whether a find is worth buying. I didn’t choose 5 of 5 because the model writes each caption fresh at a high temperature (0.9), so even when the prompt asks for the price and 2–4 sentences, it can occasionally omit the price or drift into a sentence count that is too short or too long.

---

## 5. Your choice
Given a query that matches a listing, the agent should take under a minute from the first ask command to provide the user with a response (fit card or error message) in 4 of 5 tries.
<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->



**Why this target:**
I picked under a minute because a normal run only makes 2 model calls, which should take about 15–30 seconds total. I chose 4 of 5 instead of 5 of 5 because network latency or a slow model response can add a long wait when the model is busy or rate-limited, and that is outside my code’s control.




---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
