# Prototype 10c — the manual

Everything you can do in 10c and what it does. Setup is in [`README.md`](README.md), and why it
is built this way is in [`DESIGN.md`](DESIGN.md). In the app, `/help` in her chat and `help` in
your terminal list the same commands.

**The idea in one paragraph.** She is the planner: a language model choosing where a rover on a
fogged Martian plain goes and what it does. The mission clock runs every sol by itself. You sit at
mission control's desk, and you keep to the edges of her sol. You can brief her before it, talk
to her after it, answer her if she radios from the pad, and break in with a one-way urgent
message. Everything in between is hers.

## Launching

```bash
.venv/bin/python game/main.py --arena 50 --model gemma4:31b-cloud --sols 5
```

| flag | what it does |
|---|---|
| `--arena 30\|50` | which plain. The 50 has six objectives, one inside the C-shaped rock |
| `--sols N` | sols in the mission; `0` is no limit |
| `--comms on\|off` | whether anyone is at the desk. On by default with a window, off without one |
| `--model TAG` | the planner, e.g. `gemma4:31b-cloud` or `gemma4:e4b` |
| `--preset design` | a 150-step battery and a 200-second sol, for this launch only |
| `--resume runs/<stamp>` | carry on a kept run from the sol after it stopped |
| `--replay runs/<stamp>` | play a kept run again, exactly, with no model |
| `--outage N` | cut the cloud model off for sol N, to watch the fallback |
| `--map grid\|rle`, `--think`, `--pause key\|none`, `--executor teleport\|plan` | how the map is written, a reasoning trace, the SPACE pause per leg, and whether `goto` drives |

## A sol, start to finish

1. **Morning window**, up to 60 s. She waits for you: `/start <message>` briefs her and starts
   her, and `/start` alone or silence just starts her. Your board changes go here too. If she
   answers your briefing with a question rather than with work, the window stays open and the
   talk is free.
2. **Her day.** She works in turns until she calls `end`, the sol's time runs out, or 6 turns
   have been opened. You don't talk to her while she works. She can radio you from the pad, and
   you can send an urgent message from your terminal.
3. **Dusk.** One more turn: she brings her memory up to date and, if she's beside the pad with
   comms on, reports to you.
4. **Night window**, up to 60 s, whatever the comms. If she ended the sol beside the pad with
   comms on, you can talk. `/next` skips the rest of the wait.
5. **Next sol.** The battery recharges if she's beside the pad. If not, she's stranded and wakes
   where she stopped, on whatever charge was left.

At the end of the mission the app waits: `sols N` in your terminal plays N more, and ESC
finishes (K keeps the run). With no window, or in a replay, there are no windows at all: each sol
starts at once, the night rolls straight over, and a headless run is kept and exits at the end.

A window counts down only while you aren't typing and she isn't talking. Anything that acts on her
is refused while she is still talking; send it again when she has finished.

## When you can reach her, and what it costs

| when | how | what it costs her |
|---|---|---|
| before the sol | `/start <message>`, or plain words, in her chat. Off the pad it arrives marked urgent | nothing |
| she asks before starting | answer in her chat; `/next` starts her | nothing |
| mid-sol, she radios from the pad | answer in her chat; `/next` lets her carry on | every second the line is open |
| mid-sol, you need her | `urgent <message>` in your terminal (U opens it). One-way: she stops after the call in hand, acts, and carries on | nothing beyond the stop |
| after the sol, beside the pad | talk in her chat; post to the board | nothing |
| comms off | nothing reaches either side | — |

## Her chat (TAB)

For talking to her. Plain words go to her when a window allows it.

| command | what it does |
|---|---|
| `/start <message>` | before a sol: brief her and start her. Plain words do the same |
| `/start`, `/next` | start her now; at night, the next sol; on a radio call, she carries on |
| `/order <text>` | post an order on her board. It stands every sol until you take it down |
| `/orders` | show the board. `/orders clear` takes everything down |
| `/retract N` | take order N down; the rest renumber |
| `/status` | the status line, as she reads it |
| `/help` | this list |

## Your terminal (T)

For running the mission and playing by hand. A leading `/` is fine.

| command | what it does |
|---|---|
| `urgent <message>` | one-way, while she works: she stops after the call in hand and reads it marked URGENT |
| `comms on\|off` | someone at the desk, or nobody. C does the same |
| `sols N` | N more sols in the mission |
| `place X Y high\|medium\|low COST` | put an objective under the fog. She isn't told; she finds it |
| `goto X Y`, `distance X Y`, `execute` | drive, price a drive, or do the work, by hand |
| `help` | this list |

## Keys

| key | what it does |
|---|---|
| TAB | her chat; ESC leaves it |
| T | your terminal; ESC leaves it |
| U | your terminal, with `urgent ` already typed |
| C | comms on or off, for this run |
| P | the scratchpad: her list, her memory, the board |
| V | the exact view she was sent last |
| H | show or hide her reasoning |
| M | the map of what she has seen |
| O | settings, each saying when it applies |
| Q | end the sol now |
| SPACE | skip the drive animation |
| WASD | drive by hand. Avoid it in a test: she isn't told |
| ESC | quit: K keeps the run, D discards it, ESC goes back |

## What she can do

| skill | what it does | costs |
|---|---|---|
| `goto(x, y)` | drive there, the whole way in one call | a step a tile |
| `distance(x, y)` | what that drive would cost | nothing |
| `execute()` | do the work at the objective she is beside | its cost in steps |
| `count(kind)` | every rock formation or fog patch, with size and middle | nothing |
| `count_cells(x, y)` | the exact cells of one formation | nothing |
| `todo(text)`, `strike(n)` | add to and cross off today's list | nothing |
| `remember(name, text)` | write or replace one entry of her memory | nothing |
| `forget(name)` | drop an entry | nothing |
| `radio(text)` | call the desk, from beside the pad, with comms on | the line's seconds |
| `end()` | end her turn. Outside a window it ends the sol; on a line it hands back to you | nothing |

Each turn allows 20 drives, and 10 looks between drives.

## What is written down

| place | who writes it | lifetime |
|---|---|---|
| today's list (the scratchpad) | she does, with `todo` and `strike` | wiped every night |
| her memory | she does, with `remember` and `forget`. Up to 10 entries of 300 characters | survives every night |
| the board | you do, from her chat | until you take an order down |
| `report.md` | the record, every night | the run |

She is told to keep her memory lean:
- one subject to an entry;
- change an entry rather than add a near-copy;
- forget what's no longer true;
- don't copy what her view already shows (the map, finished work, the board);
- write sols as numbers: "until the end of sol 3", never "for two more sols".

## Terms

- **Sol:** one Martian day. 600 seconds of *mission time*, spent only by her thinking and her
  steps. Waiting for you never spends it, except on a radio call she made.
- **Battery:** 500 steps. A tile driven or a step of work costs one. Only the pad recharges it,
  overnight.
- **Beside the pad (docked):** next to any side of the landing pad. Where she recharges, and
  the only place she can call the desk from.
- **Stranded:** she ended a sol away from the pad: no recharge, and no line that night.
- **Lost:** less charge than the shortest trip home. The mission ends.
- **Turn:** one stretch of her working, from a message to her `end`. A sol has several.
- **Window:** a wait for the desk. Morning, a question before she starts, a radio call, and
  night.
- **Comms / the desk:** whether anyone is at mission control. Off means she knows nobody is
  there.
- **Briefing:** your `/start` message, appended to the clock's morning paragraph.
- **Urgent:** a one-way message that stops her mid-sol. Only you can send one.
- **Board / orders:** your numbered standing instructions, shown to her on every request.
- **Memory:** her named entries, the only thing of hers that survives the night.
- **Fallback:** if the cloud model drops, the local `gemma4:e4b` answers until it is back.
- **Replay / resume:** play a kept run again exactly, or carry it on from its next sol.

## A run directory

Every session writes to `runs/pending-<stamp>/` as it goes. K keeps it as `runs/<stamp>/`, and a
run with no window is kept as `runs/<stamp>-headless/`. A `pending-` folder left behind is a run
that crashed.

| file | what is in it |
|---|---|
| `chat.jsonl` | everything she was sent and said, every call and its result |
| `game.jsonl` | what happened to the world: settings per sol, windows, orders, memory writes |
| `report.md` | the mission from the record, then her memory, rewritten every night |
| `night.json` | what the last night kept, for `--resume` |
