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

## Running a mission

```bash
.venv/bin/python game/main.py --arena 50 --model gemma4:31b-cloud --sols 5
```

Before each sol the app waits up to 60 s for you: type `/start <message>` in her chat (TAB) to
brief her, or `/start` to start her. After each sol it waits again, and `/next` moves on. Every
command, key, flag and term is in [`MANUAL.md`](MANUAL.md); `/help` in her chat and `help` in your
terminal (T) list them in the app.

**The sol and the battery.** A sol lasts `DAY_SECONDS` (600) of mission time, spent by her
thinking and by every step (`STEP_SECONDS` each). Waiting for you costs nothing, except on a radio
call she made. The battery holds `BATTERY` steps (previously `DAY_STEPS`, the steps in a sol),
and only the pad recharges it, overnight. A sol ended away from the pad strands the rover, and a
rover that can never get home is lost.

**When the cloud drops,** the same request goes to `MODEL_FALLBACK` (`gemma4:e4b`, local), and a
one-token check every 30 s brings the cloud model back. `--outage 2` stages a drop for sol 2.

**ESC always asks before quitting:** K keeps the run in `runs/<stamp>/`, D discards it. A
SIGTERM keeps the run and exits, and a run with no window (`SDL_VIDEODRIVER=dummy`) is kept as
`runs/<stamp>-headless/`. A run with no window never waits for the desk and starts with comms
off.

**Resuming and replaying.**

```bash
.venv/bin/python game/main.py --resume runs/<stamp> --sols 8
.venv/bin/python game/main.py --replay runs/<stamp>
```

A resumed run wakes on the next sol with the map, her memory, the board and the finished work,
under your current settings apart from the arena. `--sols` is the whole mission's length. A replay
plays a kept run under its own settings, never yours, and halts if the world stops matching.
