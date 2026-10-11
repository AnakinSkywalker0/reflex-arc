# Prototype 10b — the base the team builds on

10b is 10a with three things added: settings you change inside the app, a scratchpad you can watch
fill up, and instructions that get a teammate's Linux machine running. Its job is to make the
multi-sol tests cheap enough for the team to run, because no prototype has yet had a model play
past sol 1. The UI team also works from here.

Everything not listed below is inherited unchanged and described in
[`../prototype10a/DESIGN.md`](../prototype10a/DESIGN.md).

## Settings inside the app

There are 98 module constants today: 56 in `settings.py` and 42 in `config.py`. They are read at
import time as `S.X` and `C.X`. The work is making the tunable ones changeable while the app runs.
Palette and layout constants stay as code.

**Every tunable goes in one registry.** Each entry has a name, a type, a range or a list of choices,
a default, a one-line description and a **tier**:

| tier | applies | examples |
|---|---|---|
| **now** | on the next frame | animation speeds, time scale, showing the model's thinking |
| **next sol** | at the next nightfall | the model, steps per sol, storm settings, mission length |
| **relaunch** | after a restart, and the app says so | the arena (30×30 or 50×50), tile size, window size |

- **Defaults stay in code.** A person's changes live in a local file that git ignores, so a pull
  never overwrites someone's settings.
- **The settings screen is deliberately plain.** The UI team restyles it from the registry; they
  do not rebuild it.
- **The model is picked from what Ollama has installed.** Cloud models go through the machine's own
  Ollama sign-in, so there is no key to enter. Gemini keys are deferred.
- **Mission length is a new setting:** the number of sols after which the run ends and is kept. It
  is what turns a multi-sol test into one launch.
- **Every run's log records the settings in force, and replay uses the log's settings,** never the
  current ones. Otherwise changing a setting silently breaks every kept run.
- **The 29 Sept recording values become a preset:** TILE 30, HUD_H 150, DAY_STEPS 500, MOVE_HOPS 20,
  FREE_HOPS 10, CHAT_W 990, animation at half speed. 10b inherits them as its current values. The
  design default for DAY_STEPS is 150, the value the 40/15/60 objective costs were balanced for.
  Which set is the default has not been decided.

## The scratchpad on screen

A collapsible panel showing today's list as checkboxes. Items appear as the model adds them and
tick as it strikes them. Under the list go the note that crosses the night and the operator's
standing orders. One key toggles it. It should be the simplest thing that shows the list live, and
the UI team makes it look good later.

## Running it

A README with setup for Linux, tested on this machine, and for Windows, written but untested until
someone runs it there. It covers Python and the venv, `requirements.txt`, Ollama, `gemma4:e4b`
pulled locally, and `ollama signin` for the cloud model.

## Two tests that already fail

Both fail identically in 10a, so they predate 10b:
- `test_sight.py` dies with `KeyError: '1'`. The objective tiles `1`, `2` and `3` are missing from
  the word table, the same cause that broke prototype 6.
- In `test_skills.py`, the group "each gainless drive says so on its own" fails.

## For the team, once this lands: the multi-sol tests

- **The first question is whether anything survives the night as designed.** That covers the map,
  the note, the orders and the finished objectives. `world.next_day` says it keeps them, and no
  model run has ever checked.
- **Run 3 sols at 150 steps,** so something has to be put off. Read the note it leaves itself each
  night.
- **`gemma4:e4b` is fine for checking the machinery.** Anything that becomes a conclusion gets
  repeated on `gemma4:31b-cloud`. In p2, e4b read cells right 44% of the time; see
  [`../docs/findings.md`](../docs/findings.md).
- **Report each result with its n.** The same script has given 31, 14 and 32 calls on one build.

What memory and the scratchpad should become is decided from those runs, not before them.

## Not in 10b

- **The rover-bridge merge.** It is deferred until Ishan reviews it. The branch was written against
  `prototype10/`, so its files will need to land in 10b by hand.
- **Gemini keys, and a test on Windows.** Both are deferred.
- **Full autonomy:** orders given once, several sols run unattended, then a report. That is
  prototype 11.
