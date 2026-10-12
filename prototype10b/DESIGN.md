# Prototype 10b

A language model plans for a rover on a fogged Martian plain, the simulation drives each leg, and
the real rover replays it. 10b is prototype 10 with settings you change inside the app, a
scratchpad you can watch fill up, and setup instructions; ESC always asks before quitting, and a
kept run can be resumed from the next sol (`--resume`). Its job is to make multi-sol runs cheap,
because no model has yet played past sol 1. Prototype 10 itself is history: frozen as 10a, the
build the 29 Sept recording ran on.

**Built 11 Oct 2026.** Setup and every key are in [`README.md`](README.md).

## The seam

The planner decides, the real rover drives, and `plan.txt` is the only thing that crosses between
them. Every leg the planner commits to appears on disk as directions, the rover executes them and
stops, and only then does the planner get to think again. The pause is the demo.

`plan.txt` (`PLAN_FILE`, under `runs/`) holds one of `N`, `E`, `S`, `W` per line and nothing else.
No header, no comments, no coordinates, no leg structure.

The directions are absolute rather than rover-relative. Relative directions make every turn a
function of a heading the simulation never measures, and with a pause at every leg boundary that
assumed heading is exactly where the simulation's belief and the robot's reality drift apart.
Absolute removes the quantity rather than correcting it. It is also shorter: a worked 5×5 example
came to 1, 5 and 4 tokens a leg against 1, 8 and 7 relative. A step is
`HEADING_NAMES[DIRS.index(step)]` and nothing else.

The cycle, per leg:

1. `goto` plans over the map the rover knows, fog assumed drivable
2. the simulation drives the plan until it arrives or runs into rock
3. **the prefix that actually worked** is written to `plan.txt`
4. the real rover replays it and stops
5. the file is wiped; if the leg ended on rock, replan and go again

The robot only ever receives moves the simulation has already proved, so it cannot be sent into an
outcrop. That is what step 3 buys, and it is why the file holds a record rather than a hypothesis.

The model is unaffected by any of this. One `goto` returns one result however many legs it took.
`NAV_REPLANS = 5` bounds hardware round-trips at six per call. The full journey, detours included,
lives in the run's log, never in `plan.txt`, which holds the current leg only.

`ROVER_PAUSE` says who reports that the rover has finished a leg: `key`, the default, has the
operator press SPACE; `none` does not wait. The rover reporting back for itself replaces both, and
`nav._await_rover` is the only function that changes when it does.

## The world

**30×30, and the rover sees by driving.** Every cell it reaches reveals a disc of
`VISION_RADIUS = 2` around it. The only free map is the landing site, opened once on arrival
(`BASE_REVEAL`). `--arena 50` loads the older 50×50.

The geology is ten formations of six and eight cells, and one C of twelve opening east as the
unique largest. Two clear cells lie between formations so the flood fill and the eye agree on where
one ends. The C brings back an effect the small arena would otherwise lack: crossing its mouth is
expensive, so `goto` returns BLOCKED for a reason other than being driven at a wall. Which
formation is largest is the geology question, and only driving answers it.

Objectives cost 40, 15 and 60 steps of work, and a crossing is about 30. At the design sol of
`DAY_STEPS = 150`, the dearest objective plus getting there is 90: one objective a sol, with room
left to explore. 10b ships at 500 steps, which breaks that balance (see the presets under
[Settings inside the app](#settings-inside-the-app)).

**One dust storm a sol, at `STORM_RADIUS = 2`.** An impassable overlay, reseeded each sol, visible
from the moment it exists, and distinct from rock. It must stay distinct: `count` reports rock
formations, and a storm counted as one breaks the largest-formation question. It never lands on the
pad, the landing site or an objective.

## What is written down

Three stores, and they differ by who holds the pen. The code is `notes.py`.

| store | written by | lifetime | example |
|---|---|---|---|
| **orders** | the operator, at nightfall | until replaced | *finish objective 3 today* |
| **scratchpad** | the model, each morning | wiped at nightfall | *today: objectives 1 and 2* |
| **memory** | the model, before nightfall | crosses the night | *objective 3 was missed, do it today* |

Orders need their own store rather than a corner of an existing one. `next_day` clears the message
log and the todos, so anything typed at nightfall is gone by morning unless it lives somewhere that
survives, and the only other such place is `memory`, which `remember` replaces wholesale. Put orders
there and the model deletes mission control on its next call. So orders are written only by the
operator, read-only to the model, and ride in the view on every request the way the other two do.

The map already crosses the night, so a survey sol makes the **map** valuable. What makes *memory*
valuable is the deferral: the sixty-step objective left undone and the line that says do it first
tomorrow, which a 150-step day produces on its own.

## Nightfall

The day ends, the operator gives the rover its work, and the operator presses N. TAB talks to the
model, and what is typed lands in the pane as `OPERATOR`. `/orders ...` sets the standing orders,
and `/place X Y [high|medium|low] [cost]` puts an objective on the map. The model never opens a sol
by itself: talk to it at the start of the sol, or leave orders before pressing N.

**The guard.** `World.place_objective` refuses a cell with no approach the rover can reach, flooding
from the spawn over the true grid rather than the fogged one. The operator can see the whole arena,
and refusing placements into unmapped ground would refuse the one sol worth running. The storm is
not consulted because it cannot bury one: `_weather` keeps it clear of every live objective, placed
ones included.

A run would typically go:

| sol | orders |
|-----|--------|
| 1 | survey only — find and report the largest formation |
| 2 | one objective placed |
| 3 | survey only |
| 4 | one objective placed |
| 5 | one objective placed in ground the rover has not been to |

Sol 1 needs a stated job or it is a blank day and `_stuck` fires. The geology question is that job,
it is only answerable by driving, and it is the natural first thing to write in the scratchpad.

## Live and replay

Two modes, because a demo and an experiment want opposite things.

**Live:** the model decides. It might be brilliant, and it might flop.

**Replay** (`--replay runs/<stamp>`): a kept run re-issues the recorded tool calls, and the model is
never asked. The run directory already holds enough: `chat.jsonl` keeps every prompt and reply in
full, and `game.jsonl` keeps every world event and a `settings` row for each sol. Replay uses the
log's settings, never the current ones. With no model in the loop and everything else
deterministic, the same `plan.txt` gets written and the rover drives the same route.

So the script for a scripted run is a run that already happened. Go live until a sol comes out
well, keep it (K at ESC), and that directory is the demo, operator orders and objective placements
included.

**Replay assumes the hardware obeys.** Live, the simulation leads and the robot follows, so a robot
that stops early feeds back into a replan. In replay there is no planner to react: a slipped wheel
puts the rover somewhere the run does not know about, and every leg after it is wrong. Replay
re-plans and re-drives every `goto` and checks each result against the log; a mismatch halts it
with REPLAY DIVERGED rather than carrying on plausibly.

### The determinism ledger

| | |
|---|---|
| **arena** | authored strings |
| **storm** | seeded `f"{name}:{w}x{h}:sol{day}"`, and Python seeds from the bytes via SHA-512, so `PYTHONHASHSEED` cannot reach it |
| **the day** | counted in steps, not wall-clock, so it does not depend on machine speed |
| **the view** | built in map order, so no set-iteration order reaches the model |
| **Ollama** | `num_ctx`, `temperature` and `seed` (`MODEL_SEED = 0`) are sent |
| **animation** | wall-clock, so pacing varies between runs. Affects a video, not an outcome. |
| **the model** | **not controllable.** `MODEL_TEMP = 0.0` is greedy and usually reproduces on a fixed local build, but inference batches requests and floating-point addition is not associative, so identical prompts can give different logits depending on what else was in the batch. Hosted models are worse. One differing token cascades through the sol. |

The last row is why replay exists. Everything above it can be pinned; the model cannot, so for
anything that has to come out the same twice, take it out of the loop.

## Settings inside the app

The tunables are module constants in `settings.py` and `config.py`, read at import time as `S.X`
and `C.X`. The tunable ones can be changed while the app runs. Palette and layout constants stay as
code.

**Every tunable goes in one registry** (`registry.py`). Each entry has a name, a type, a range or a
list of choices, a default, a one-line description and a **tier**:

| tier | applies | examples |
|---|---|---|
| **now** | on the next frame | animation speeds, time scale, showing the model's thinking |
| **next sol** | at the next nightfall | the model, steps per sol, storm settings, mission length |
| **relaunch** | after a restart, and the app says so | the arena (30×30 or 50×50), tile size, window size |

- **Defaults stay in code.** A person's changes live in a local file that git ignores, so a pull
  never overwrites someone's settings.
- **The settings screen is deliberately plain.** Restyle it from the registry rather than rebuilding
  it.
- **The model is picked from what Ollama has installed.** Cloud models go through the machine's own
  Ollama sign-in, so there is no key to enter.
- **Mission length** is the number of sols after which the run stops, and ESC asks whether to keep
  it. It is what turns a multi-sol test into one launch.
- **Every run's log records the settings in force, and replay uses the log's settings,** never the
  current ones. Otherwise changing a setting silently breaks every kept run.
- **The 29 Sept recording values are a preset:** TILE 30, HUD_H 150, DAY_STEPS 500, MOVE_HOPS 20,
  FREE_HOPS 10, CHAT_W 990, animation at half speed. 10b ships with them as its current values. The
  design default for DAY_STEPS is 150, the value the 40/15/60 objective costs were balanced for,
  and the **design** preset loads it. Which set is the default has not been decided.

## The scratchpad on screen

A collapsible panel showing today's list as checkboxes. Items appear as the model adds them and
tick as it strikes them. Under the list go the note that crosses the night and the operator's
standing orders. P toggles it. It is the simplest thing that shows the list live.

## Running it

Setup is in [`README.md`](README.md): Linux, tested, and Windows, written but not yet tested. It
covers Python and the venv, `requirements.txt`, Ollama, `gemma4:e4b` pulled locally, and
`ollama signin` for the cloud model.

## Not in 10b

- **The rover reporting back for itself.** The operator stands in for it (`ROVER_PAUSE`, above).
- **Gemini keys.** Every model goes through Ollama.
- **A tested Windows setup.**
- **Full autonomy:** orders given once, several sols run unattended, then a report.

## Open

- **`VISION_RADIUS = 2` is a guess** sized to the smaller arena, not a swept value.
- **Two objectives may share a priority.** The operator can place a second `high`, and the view
  tells them apart by cell and cost alone. Untried on a model.
- **Turns are free in the budget and slow in the room.** The day is charged one step per tile
  driven, so a turn-heavy route costs the same as a straight one in the simulation and considerably
  more on hardware.
