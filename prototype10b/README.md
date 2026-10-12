# Prototype 10b — setup

A language model plans for a rover on a Martian plain, and you watch it drive. What 10b is
for, and how it works, is in [`DESIGN.md`](DESIGN.md).

You need Python 3.12, pygame, and Ollama with a model in it. Every command below runs from
this directory, `prototype10b/`.

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

Written, not yet tested. Use PowerShell, from `prototype10b\`:

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

- **now:** animation speed, the settling pause, showing the model's reasoning.
- **next sol:** the model, steps per sol, the turn caps, the storm, the map format and
  mission length. The planner is fixed for a sol, so these wait for nightfall (N).
- **after a restart:** the arena, the tile size and the pane width.

Your changes are saved in `user_settings.json`, which git ignores, and only the ones that
differ from the code's defaults are written. Two presets load whole sets at once:
**29 Sept recording** (what 10b ships with: a 500-step sol) and **design** (the 150-step sol
the objective costs were balanced for). Which should be the default has not been decided.

Flags override your saved settings for one launch: `--model`, `--map`, `--arena`,
`--executor`, `--pause`, `--sols`, `--think`.

**Mission length** (`MISSION_SOLS`, or `--sols 3`) stops the run once that many sols are
over: N is refused, and ESC asks whether to keep the run. 0 means no limit.

**ESC always asks before quitting,** including while the rover is driving a leg: K keeps the
run in `runs/<stamp>/`, D discards it, ESC goes back.

**Resuming.** A kept run can be carried on later from the next sol:

```bash
.venv/bin/python game/main.py --resume runs/<stamp>
```

The rover wakes at the pad with the map, the formation ids, the open objectives, its note
and your orders. If you quit partway through a sol, that sol counts as played. The resumed
session is a new run directory, and it uses your current settings, apart from the arena.

Every run's `game.jsonl` has a `settings` row for each sol. `--replay runs/<stamp>` plays a
kept run under its own settings, never yours, apart from the window and the animation pace.

## Keys

| key | does |
|---|---|
| TAB | talk to the planner |
| P | show or hide the scratchpad: today's list, the note, the orders |
| O | settings |
| V | the exact view the model was sent |
| H | show or hide its reasoning |
| Q / N | end the sol / start the next one |
| SPACE | the rover has finished its leg (with `ROVER_PAUSE key`) |
| WASD, M, X, T | drive by hand, the map, mark a cell, the console |
| ESC | quit, and choose whether to keep the run |
