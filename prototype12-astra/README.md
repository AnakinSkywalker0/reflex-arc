# Prototype12-astra — Angaraka mission control

Pygame UI redesign of prototype10d, keeping the dashboard layout and using `reference2.png` for its charcoal, silver and muted teal colour palette.
The rover, terrain generation, navigation, AI, mission timing, saved runs and replay
use the original prototype10d implementation.

From this directory, launch with the existing environment:

```bash
.venv/bin/python game/main.py
```

The UI adds live rover telemetry, Scratchpad, a sliding Memory drawer, activity, and clickable
Map / Terminal / Settings controls. All original keyboard shortcuts still work.
Press **M** for a map that uses the whole app window. Press **F11**, or click
**Expand** on the terrain, for a full-screen map; **M / ESC / F11** returns to the
dashboard. Map-mode WASD moves the cursor and X marks a cell, as before.
Terrain uses prototype12b’s connected, rounded rock silhouettes, shaded facets and cast shadows over rust-red Martian regolith. Grid lines mark each simulation cell, using the same base tile size as prototype10d. Storms show animated dust.

The visual preview is `previews/reference2-dashboard.png`; it uses a fully surveyed demo map to show the rock formations. Normal missions retain exploration fog.
`previews/reference2-laptop.png` shows the compact layout, and
`previews/reference2-fog.png` shows normal exploration visibility.
`previews/reference2-map.png` shows the expanded map. Regenerate all four without
a model connection or saved mission using `.venv/bin/python game/preview.py`.

Click the planner input or press TAB to type; the planner expands while typing or
viewing the model input (V). ESC closes typing/the view. P toggles planner notes,
and the mouse wheel scrolls the conversation. Drag the Memory handle beside Scratchpad left to reveal saved model memory; scroll with the mouse wheel over the drawer. Unexplored terrain stays hidden.

The setup and launch options inherited from prototype10d follow below. Run commands
from `prototype12-astra/` when using this copy.

## Original prototype10d setup

A language model plans for a rover on a Martian plain, and you watch it drive. What 10d is
for, and what it changes from 10c, is in [`DESIGN.md`](DESIGN.md).

You need Python 3.12, pygame, and Ollama with a model in it. Every command below runs from
this directory, `prototype10d/`.

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

Written, not yet tested. Use PowerShell, from `prototype10d\`:

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

Astra display settings apply immediately: `DISPLAY_MODE` selects `fit`,
`fullscreen` (the whole dashboard), or `custom`. Set `SCREEN_WIDTH` and
`SCREEN_HEIGHT` for custom dimensions. `EXPAND_SIMULATION` fills the window
with the simulation; use its back control or O → Settings to restore the dashboard.
The window can also be resized by dragging its edges. The default fills the
available desktop while leaving room for window borders.


**O** opens the settings screen. Every setting says when a change lands:

- **now:** comms, animation speed, the settling pause, showing the model's reasoning.
- **next sol:** the model, the day's length, the battery, the radio's cost, auto objectives,
  the turn caps, the storm, the map format and mission length. The planner is fixed for a
  sol, so these wait for nightfall.
- **after a restart:** the arena, the tile size and the pane width.

Your changes are saved in `user_settings.json`, which git ignores, and only the ones that
differ from the code's defaults are written. Two presets load whole sets at once:
**29 Sept recording** (what 10d ships with: a 500-step battery and a 600-second day) and
**design** (a 150-step battery, which the work costs were balanced for, and a 200-second
day). Which should be the default has not been decided.

Flags override your saved settings for one launch: `--model`, `--map`, `--arena`,
`--executor`, `--pause`, `--sols`, `--think`, `--comms`, `--objectives`, `--preset`,
`--outage`.

## Running a mission

```bash
.venv/bin/python game/main.py --arena 50 --model gemma4:31b-cloud --sols 5
```

A sol is dawn, day, dusk and night. At dawn and night you talk to her in her chat (TAB); the
day is hers; dusk is her report. `/next` moves to the next phase, and each phase also moves on
60 s after the last thing typed or said. Every command, key, flag and term is in
[`MANUAL.md`](MANUAL.md); `/help` in her chat and `help` in your terminal (T) list them in the
app.

**The day and the battery.** The day lasts `DAY_SECONDS` (600) of wall clock, which nothing
pauses. The battery holds `BATTERY` steps, and only the pad recharges it, overnight; a flat
battery ends the day. A day ended away from the pad strands the rover, and a rover that can
never get home is lost.

**When the cloud drops,** the same request goes to `MODEL_FALLBACK` (`gemma4:e4b`, local), and a
one-token check every 30 s brings the cloud model back. `--outage 2` stages a drop for sol 2.

**ESC always asks before quitting:** K keeps the run in `runs/<stamp>/`, D discards it. A
SIGTERM keeps the run and exits, and a run with no window (`SDL_VIDEODRIVER=dummy`) is kept as
`runs/<stamp>-headless/`. A run with no window never waits for the desk and starts with comms
off.

**Scoring a run.** `.venv/bin/python game/score.py runs/<stamp>` prints a row per sol from
the run's own logs, and several run directories are compared side by side.

**Resuming and replaying.**

```bash
.venv/bin/python game/main.py --resume runs/<stamp> --sols 8
.venv/bin/python game/main.py --replay runs/<stamp>
```

A resumed run wakes on the next sol with the map, her memory, the board, the work and her
reports, under your current settings apart from the arena. Nights saved by 10c do not resume
here. `--sols` is the whole mission's length. A replay
plays a kept run under its own settings, never yours, and halts if the world stops matching.
