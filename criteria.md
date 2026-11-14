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

---
---

# Capstone criteria (unit 9): hardened `/ask` endpoint

Written before any capstone test was run. The criteria above are from unit 3 and
are left as they were. Each criterion below is checked three times (three
trials), and a trial means the full set of requests listed in that criterion.

## C1. Bad input is rejected before the agent runs

Six malformed requests to `POST /ask` each get HTTP **400** with a JSON `error`
that names the thing to fix (contains `query`, `wardrobe`, or `JSON`). None of
them gets a 500, and each one's log record shows `model_calls: 0`. The six are:
a body that isn't JSON, `{}` (no query), `{"query": "   "}`, `{"query": 123}`,
`{"query": "tee", "wardrobe": {"items": "abc"}}`, and a wardrobe with 51 items.
**Target: 6 of 6 in every trial.**

**Why this target:** validation is plain code with no model involved, so the
same bad request always takes the same path, and anything less than 6 of 6
means there's a hole. Before this unit, two of these six (`query: 123` and
`items: "abc"`) crashed with a 500 and a Python exception name. A bad request
that reaches the model would also spend about 1,000 tokens on nothing.

## C2. A model outage returns a 503 with a sentence a user can act on

With the server started on an invalid `GEMINI_API_KEY` (cache off), five
different matching queries each come back as HTTP **503** within **10 seconds**.
The JSON `error` must not contain a Python exception name (`Error:`,
`Exception`, `Traceback`, `ModelUnavailable`) and must not mention `.env` or
`GEMINI_API_KEY`. **Target: 5 of 5 in every trial.**

**Why this target:** the person calling a web endpoint can't fix the server's
key, so telling them to "check your .env" is the wrong message for them, and it
also leaks how the server is configured. The only fix they can make is to try
again later. Nothing here is random (a bad key fails the same way every time),
so 5 of 5 is the right bar. I picked 10 seconds because the failing run is one
MCP search (about 2 s) plus one rejected model call, so anything near 10 s
would mean it's retrying something that can't succeed.

## C3. Every request leaves exactly one log record

Across one trial (the 6 bad requests from C1, the 5 bad-key requests from C2,
and the 5 matching requests from C4, so 16 requests), `logs/requests.jsonl`
gains exactly **16** new lines. Every line parses as JSON with non-null `ts`,
`status`, `outcome`, and `duration_ms`, and its `status` matches the HTTP status
the caller got. **Target: 16 of 16 in every trial.**

**Why this target:** a log is only useful for diagnosis if a missing line
means a missing request. If even one failure path skips the log, that is
exactly the kind of failure I'd never find later. The 503 path matters most
here because it runs in a different server process with a different key.

## C4. The original agent still works through the endpoint

`{"query": "vintage graphic tee under $30"}` sent 5 times to a working server
(real key, cache off) returns HTTP 200 with `error: null` and a non-empty
`fit_card` that contains the selected item's price (`$24`).
**Target: at least 4 of 5 in every trial.**

**Why this target:** this is the regression check. The extension wraps
`run_agent`, so it shouldn't change what comes out. I allow one miss, not zero,
because the fit card is written fresh by the model at temperature 0.9 and can
occasionally drop the price, the same reasoning as my unit 3 criterion 4.

## C5. A warm request answers in under 10 seconds

For those same 5 matching requests, sent one after another to a server that
has already answered `/health`, the log's `duration_ms` is under **10,000** in
**at least 4 of 5** in every trial. "Warm" means the server process is already
running; it does not mean the model was called recently.

**Why this target:** my 10-run cost measurement had a median of 2.7 s, so
10 s leaves room for a slow model response. But the server's rate limiter
paused one run for 26 s when calls went over 15 a minute, and a web caller sees
that as a hang with no message. Allowing 1 of 5 over 10 s accepts one such
pause per batch. More than that would mean normal use is regularly hitting
the limit.
