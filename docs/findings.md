# What prototypes 1–9 settled

Nine prototypes between 26 August and 5 September, each one paid for by running a model through
it. Their code is archived in `archive/` and at the git tag `prototypes-1-9`.
This page keeps what they concluded, so the next build starts from the conclusions rather than
re-deriving them. Most of these were invisible to code review: the tests passed throughout.

Unless a line says otherwise, the model was `gemma4:e4b` running locally, and **every rate here is
small-n**. The bedrock items are structural, such as a cap that holds or a code that lies. The soft
items are rates, and are marked with their n.

## The line, in one table

| | what it added | what it taught |
|---|---|---|
| 1 | a puzzle world with A\*, fog, `goto`, notes | most of this page |
| 2 | the 50×50 rover arena | `why` optional; gemma cannot count off the map |
| 3 | run-length map, `end`, `count`, schema withdrawal | the turn runs until the model ends it; a cap is an absence, not an argument |
| 4–6 | the team's branches: flyer, cell policy, objectives and hazards | parallel forks drift: all three forked before p3 moved |
| 7 | the three merged; one dust storm a sol | driving out-mapped the flyer |
| 8 | the rover blinded, the flyer its only eye; `rover_link.py` | contact must reveal what it hit |
| 9 | `notes.py`: the daily list, the one note that crosses the night | the write path |
| 10 | the seam to the real rover | lives on as `prototype10a/` |

## Talking to the model

**A lying success code is worse than any failure.** A `goto` aimed at a visible wall answered
`DONE`, and the model spent four days re-issuing a move it had been told succeeded. Make every
code match what actually happened.

**A field is not a sentence.** `DONE(at=(10,15), beside=(10,16))` was read as failing to reach
(10,16), even with the field there. The answer now says it in words: *"(10,16) is solid, so
stopping beside it IS arriving."*

**A costless call repeats.** Seven identical `goto`s each answered `DONE(steps=0)` honestly, and
nothing gave the model a reason to stop. The rule that stopped it is an invariant, not a list of
cases: a call that spends nothing cannot change the world, so an identical call after it gets the
identical answer. A detector written around the case in front of you misses the next one, and
this was recorded three separate times.

**A gainless drive says nothing about being gainless.** `DONE(steps=19, new=0)` reads as success.
Prototype 4 lost 24% of a sol (43 of 178 steps) to drives back over mapped ground.

**A limit enforced by asking is not a limit.** A request to stop let 4 more calls through.
Withdrawing the tool schemas still let through 8. Only dropping later calls on the floor held.
Assume anything that relies on the model's cooperation will not hold.

**An optional argument gets volunteered.** Unprompted, the model passed `avoid="auto"`. Describing
it as *"omit it entirely unless…"* fixed that in 3 of 3 tries. An argument the model does not need
has to be made unattractive, not merely optional.

**`why` is optional.** As a required field it was being stripped from the history the model read
back, so every past call it saw showed how to leave it out: 16 of 21 calls in one run failed for
lack of it. Made optional, failures went to 0 of 13. The cost is that it is now rarely given.

**About one turn in ten, the model types the call out as text instead of making it.** That was
measured at 9/10 tool calls with temperature 0, and 7/10 with it unset, over forty samples. Neither
the prompt nor a retry fixes it. A written call that is complete gets parsed and run, and is
labelled as recovered. In those turns the model often goes on to write an invented view block, a
whole fake map. `chat.cut_fabrication` cuts at the view's own headings.

**The chat template leaks.** Every turn ended `<channel|>`, which then went back into the context.
`chat.clean` strips an explicit list of tokens, not a catch-all pattern.

**Ollama's `num_ctx` defaults to 4096 and truncates silently.** A sol loses its own morning and
the model looks forgetful. Always set it.

## What the model can read

**Gemma cannot index a monospace grid, and states wrong readings confidently.** It got 5 of 10
cells right with thinking off, and 5 of 10 with thinking on at 187× the time.
- **Counting off the map:** 0 of 42 region questions and 0 of 21 row questions.
- **The 31B:** read cells at 65%, but never once answered rock (0 of 21).
- **Gemini:** 3.5-flash read every cell right (21 of 21), and 3.7-flash counted a 30-cell box
  correctly (n=1).
- **So:** counting is a Gemma limit, not an LLM one.

**Any coordinate the model would have to count out of a grid is suspect, so hand it the answer.**
The view pre-computes the four neighbours, the open distances and every thing with its
coordinate. `distance` and `count` are exact and free. The environment computes facts; the model
decides.

**The map is not the expensive part of a request.** In prototype 1, an ASCII grid cost 196 tokens.
Run-length spans of the same map cost 598, and coordinate lists cost 972. Repetitive text packs
well and coordinates do not. Measured on prototype 10's whole view block (`settings.py`, beside
`MAP_FORMAT`):

| arena | grid, fresh sol | grid, surveyed | run-length, surveyed |
|---|---|---|---|
| 30×30 | 845 | 772 | 1,414 |
| 50×50 | 1,280 | 1,155 | 3,168 |

**The view is injected on every request, never fetched, and replaced rather than appended.**
Given one tool, the model uses it for everything: asked *"what is around you?"* with only `goto`,
it called `goto` on its own cell, twice out of two. The model holds exactly one map, and it is the
current one.

## Navigation

**Fog is planned as open ground.** `goto` plans over the map the rover knows, drives until reality
refuses, stops there and reports. A blocked drive is how the map fills in, not a wasted one.

**Contact has to reveal what it hit.** If it does not, the replan returns the same path and the
rover bumps the same cell until its replans run out. Prototype 8 found this when it made driving
reveal nothing else.

**Show the walk, not just the plan.** Each replan replaces the plan, so a drawing of the plan shows
a route through walls the walk never crossed. Where the two disagree is exactly where the fog lied.

**An atomic `goto` through fog reads as teleporting.** That is why the reel replays the drive.

## The day, and what is written down

**A day is counted in steps, not wall-clock.** Otherwise the model's thinking time sets the
difficulty, and two machines play different games.

**The note is replaced whole, not appended to.** Appending means the model can never correct
itself, and correction is the thing most worth watching.

**The notes are injected into the view, not fetched.** A forgotten `read_notes()` costs a whole
day and teaches nothing.

**Free calls stay legal after the step budget runs out,** or the end of the day locks the model
out of writing its own record.

**Failure codes are the schema of memory.** Log the conditions an
outcome happened under, not the outcome alone, or *"failed at X"* hardens into *"X does not
work"*.

## The flyer, and why it was cut

- **Prototype 4, n=1 each way:** the model reached for the flyer unprompted in one run and ignored
  it in another. The recharge gate visibly shaped its plans.
- **Prototype 7:** the best run drove a perimeter lap, mapped 782 cells and flew zero times in
  twelve calls. Driving was strictly the better way to map, so the flyer posed no real decision.
- **Prototype 8:** made the rover blind. The same lap then mapped 17 cells, and one 20-step sortie
  about 90.
- **Prototype 10:** cut the flyer and gave the rover back its sight at radius 2. Nothing else could
  answer the geology question.

## Measuring

**An n=1 comparison is worthless here.** The same four-turn script on the same build gave 31, 14
and 32 calls. What survived repetition was structural: a cap firing at most once, zero bad
arguments, the arithmetic landing right. Totals did not survive.

**Prompt processing is the cost, not generation.** On an integrated GPU a turn took 111–237 s, and
130 s of one went on producing 17 tokens. The prompt grows through the sol, so the sol slows as it
goes.

## How the building went

Prototype 1's first attempt built everything in one session and was reverted. What worked was
putting the model in the window talking, with no skills at all, then adding each capability once
working without it became annoying. A skill you have watched someone talk to is a different thing
from a skill you specced.
