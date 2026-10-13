# Prototype 10c — setup

A language model plans for a rover on a Martian plain, and you watch it drive. What 10c is
for, and what it adds over 10b, is in [`DESIGN.md`](DESIGN.md).

You need Python 3.12, pygame, and Ollama with a model in it. Every command below runs from
this directory, `prototype10c/`.

## Linux

Tested on Linux Mint 22.3 on 11 Oct 2026.

**1. Python and the venv.** `uv` installs without root and fetches its own Python:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r ../requirements.txt
```

Without uv, Ubuntu and Mint need the venv package first, or `python3 -m venv` fails with
"ensurepip is not available". This route was not tested here, because it needs sudo:

```bash
sudo apt install python3.12-venv
python3 -m venv .venv
.venv/bin/pip install -r ../requirements.txt
```

**2. Ollama and a model.**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma4:e4b          # 9.6 GB, runs locally
```

The cloud model needs no key. It goes through this machine's own Ollama sign-in:

```bash
ollama signin
ollama pull gemma4:31b-cloud    # registers it; nothing large downloads
```

`ollama list` should now show both.

**3. Check it.** Every suite should end in "passed":

```bash
for t in game/test_*.py; do .venv/bin/python "$t" | tail -1; done
```

**4. Run it.**

```bash
.venv/bin/python game/main.py
```

The shipped model is `gemma4:31b-cloud`. If you have not signed in, start with
`--model gemma4:e4b`, or choose it on the settings screen and restart.

## Windows

Written, not yet tested. Use PowerShell, from `prototype10c\`:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r ..\requirements.txt
irm https://ollama.com/install.ps1 | iex
ollama pull gemma4:e4b
ollama signin
ollama pull gemma4:31b-cloud
.venv\Scripts\python.exe game\main.py
```

## Settings

**O** opens the settings screen. Every setting says when a change lands:

- **now:** comms, animation speed, the settling pause, showing the model's reasoning.
- **next sol:** the model, the sol's length, the battery, the turn caps, the storm, the map
  format and mission length. The planner is fixed for a sol, so these wait for nightfall.
- **after a restart:** the arena, the tile size and the pane width.

Your changes are saved in `user_settings.json`, which git ignores, and only the ones that
differ from the code's defaults are written. Two presets load whole sets at once:
**29 Sept recording** (what 10c ships with: a 500-step battery and a 600-second sol) and
**design** (a 150-step battery, which the objective costs were balanced for, and a
200-second sol). Which should be the default has not been decided.

Flags override your saved settings for one launch: `--model`, `--map`, `--arena`,
`--executor`, `--pause`, `--sols`, `--think`, `--comms`, `--preset`, `--outage`.

## A mission

```bash
.venv/bin/python game/main.py --sols 3
```

**The clock runs every sol.** It opens each sol, keeps the planner going until she calls
`end` or the clock runs out, asks for tomorrow's note, and rolls the night over. Every sol
gets a fresh conversation, and the note and the map carry over. With no orders she is told
to explore. If the model stops answering, the clock asks again every 30 seconds and does
not count it as a turn. **Mission length** (`MISSION_SOLS`, or `--sols 3`) ends the run
after that many sols: it is kept in `runs/<stamp>/` and the app closes. `--sols 0` runs until
you quit.

**The arena.** The 30×30 is the default. `--arena 50` is the bigger plain, with six objectives
under the fog: two of each priority, one of them inside the C-shaped rock, whose mouth faces
east.

**Comms: whether anyone is at the desk.** `COMMS` (C in the app for this run, or
`--comms on|off`) says whether someone will answer. She is told which.

| | beside the pad | away from the pad |
|---|---|---|
| **comms on** | talk both ways: TAB from here, `radio` from her | urgent only: U from here, `sos` from her |
| **comms off** | nothing | nothing |

- **At night,** if the sol ends with the rover beside the pad and comms on, she reports
  and the line stays open. Talk, plan, give `/orders`. N starts the next sol, and so does
  60 seconds with nothing said (`COMMS_WAIT`). Stranded off the pad, there is no line that
  night.
- **By day,** TAB beside the pad and U from anywhere stop her after the call in hand, the
  drive included, and she waits for you. Your first line on an urgent call reaches her
  marked URGENT. While a line is open her `end` hands back to you. N closes the line, or
  60 seconds of silence does, and she carries on with the sol.
- **Her calls** open a line the same way: `radio` beside the pad, and `sos` from anywhere,
  for emergencies. Nothing in the world gives her one yet. If nobody answers in 60
  seconds she carries on.
- **A run with no window starts with comms off,** since nobody is there to answer. Pass
  `--comms on` to override.

**A sol is a clock; the steps are a battery.** A sol lasts `DAY_SECONDS` on a mission
clock. Her thinking runs it down, at the seconds each answer actually took, and so does
every tile driven and every step of work (`STEP_SECONDS` each). A slow model gets less
done. The animation, the settle pause, your typing and the SPACE pause don't count. The
battery holds `BATTERY` steps (previously `DAY_STEPS`, the steps in a sol): one per tile
driven, one per step of work. A flat battery doesn't end the sol, but nothing can drive or
work until the pad recharges it. The HUD shows the time left and the charge.

**Home before dark.** Only the pad recharges the battery, overnight. If a sol ends with
the rover anywhere else, it is stranded: next sol it wakes where it stopped, on whatever
charge is left. That is true however the sol ended: the clock running out, her `end`,
your Q, or quitting. A rover with less charge than the shortest trip back can never get
home: it is lost, and the mission ends at that nightfall. The view tells her how far the
pad is, in charge and in seconds, and every result warns her once she is short of either
for the trip home. The HUD shows `(stranded)` after a night out.

**Presets for one launch.** `--preset design` loads the design set (150 battery,
200-second sol) without saving it. At 500 steps the 30×30 is fully mapped by sol 2.

**The report.** Every kept run has a `report.md`, rewritten each night and once more at
the end. It is written from the world's record, not from anything she said: what was
finished and on which sol, what is still out there, how much is mapped, the largest
formation seen, and where each sol ended and on what charge. Her last note goes
underneath, labelled as hers and not checked against the record. The view also lists
finished work on every request, so she never has to remember what got done.

**When the cloud drops.** If a request to the planner's model fails, the same request
goes straight to `MODEL_FALLBACK` (`gemma4:e4b`, local), and she carries on with it.
While the fallback answers, the cloud model gets a one-token check every 30 seconds
(`PROBE_SECONDS`). The first request after it answers goes back to the cloud, and each new
sol starts with a check, so if the cloud came back overnight she is on it from her first
request. The pane
says when she drops and when she comes back, the subtitle reads `(fallback)` meanwhile,
and every cost row on the tape names the model that answered. The fallback thinks
slower, and thinking runs the clock, so a sol on it gets less done. Set
`MODEL_FALLBACK` to the planner's own model to turn this off. If Ollama itself is down,
nothing can answer, and the clock asks again every 30 seconds as before.

To watch it without a real outage, `--outage 2` cuts the cloud model off for all of
sol 2. Its requests and checks go to a port nothing listens on, so the real
connection-refused path runs. The pane and the tape both mark it as staged:

```bash
.venv/bin/python game/main.py --sols 3 --preset design --outage 2
```

**ESC always asks before quitting,** including while the rover is driving a leg: K keeps the
run in `runs/<stamp>/`, D discards it, ESC goes back. A SIGTERM keeps the run and exits, so
`timeout` can end a headless run. A run with no window (`SDL_VIDEODRIVER=dummy`) is kept as
`runs/<stamp>-headless/`.

**Resuming.** A kept run can be carried on later from the next sol:

```bash
.venv/bin/python game/main.py --resume runs/<stamp>
```

The rover wakes with the map, the formation ids, the open objectives, its note and your
orders: at the pad, or stranded where it stopped. If you quit partway through a sol, that
sol counts as played. The resumed session is a new run directory, and it uses your current
settings, apart from the arena.

Every run's `game.jsonl` has a `settings` row for each sol. `--replay runs/<stamp>` plays a
kept run under its own settings, never yours, apart from the window and the animation pace.

## Keys

| key | does |
|---|---|
| TAB | talk to the planner: on an open line, or beside the pad |
| U | urgent call, from anywhere, while the sol runs |
| N | close the line: she carries on, or at night the next sol opens |
| C | comms on or off, for this run |
| P | show or hide the scratchpad: today's list, the note, the orders |
| O | settings |
| V | the exact view the model was sent |
| H | show or hide its reasoning |
| Q | end the sol now |
| SPACE | the rover has finished its leg (with `ROVER_PAUSE key`; the default is `none`) |
| WASD, M, X, T | drive by hand, the map, mark a cell, the console |
| ESC | quit, and choose whether to keep the run |
