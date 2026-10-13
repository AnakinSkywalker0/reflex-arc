# Prototype 10c — the rover works by itself

10c is 10b with the rover left to work on its own. A mission clock runs every sol, the sol is a
span of mission time, and the steps are a battery only the pad recharges. Mission control keeps to
the edges of her sol: it briefs her before, talks after, answers when she radios from the pad,
and can break in one way with an urgent message. Her memory is a few named entries she keeps lean
herself. If the cloud model drops, a local one takes over, and a report is written from the
record every night. The clock, battery, fallback and report were built in DA task 19; the rest
was added on 13 Oct. Every command and key is in [`MANUAL.md`](MANUAL.md).

Everything not listed here is inherited from [`../prototype10b/DESIGN.md`](../prototype10b/DESIGN.md)
and [`../prototype10a/DESIGN.md`](../prototype10a/DESIGN.md). Setup and every key are in
[`README.md`](README.md). 10b stays as it was, for the team's tests.

## The sol runs on a clock, and the steps are a battery

A sol is `DAY_SECONDS` on a mission clock. Two things run it down: her thinking, charged at the
seconds each request actually took, and every step the rover takes, at `STEP_SECONDS` each. A slow
model gets less done, which is Mars. The animation, the settle pause, the operator typing and the
SPACE pause cost nothing, so a display setting never changes an outcome.

The battery holds `BATTERY` steps (previously `DAY_STEPS`, the steps in a sol): one per tile
driven, one per step of work. Looking and thinking are free. A flat battery does not end the sol,
but nothing drives or works until the pad recharges it. On the design preset (150 charge, 200 s)
the cloud 31B runs out of battery a little before the clock. A model slower than a few seconds a
request runs out of sol first.

## Home before dark

Only the pad recharges the battery, overnight, and the rover is home beside any side of it
(`World.docked`). A sol that ends anywhere else strands the rover: no recharge, and it wakes where
it stopped. A rover with less charge than the shortest possible trip back is lost
(`World.lost`), and the mission ends that night. The view gives the pad's distance on every
request, in charge and in seconds, and results warn when either runs short. A stranded night
carries in `night.json`, so `--resume` wakes stranded too.

## The clock runs every sol

The clock opens each sol with a turn of its own (`autopilot.py`), and opens another whenever one
ends without her choosing to stop. It closes the sol when she calls `end`, when the clock runs
out, or after `AUTO_TURNS` turns. Then it asks her to bring her memory up to date and rolls the
night over. Its lines are `auto` on the tape, never `you`, so a sol nobody coached can't be taken
for one somebody did. The operator-runs-every-sol mode is gone from 10c; 10b keeps it.

- **Her `end` closes the sol.** The exception is an `end` sent after a cap stopped the turn,
  which gets a fresh turn instead. The cap sent her to `end`, and the first unattended run lost
  116 steps to it.
- **A request that never reached the model** is asked again after `AUTO_RETRY_SECONDS` and is
  not counted as a turn.
- **The SPACE pause is off by default** (`ROVER_PAUSE none`), since nobody has to be at the keys.

## The desk keeps to the edges of the sol

`COMMS` says whether anyone is at mission control's desk, and she is told which. With someone
there, the desk talks to her in four places, and only one of them costs her any of the sol:

| when | how | costs her |
|---|---|---|
| before the sol | `/start <message>`: the clock's paragraph with the desk's words appended | nothing |
| a question before she starts | the morning window stays open while she only talks | nothing |
| mid-sol | her `radio`, from beside the pad only | every second the line is open |
| after the sol | the night window, if she ended beside the pad | nothing |

With a window open on the app, the clock holds a window at each of these and waits up to
`COMMS_WAIT` (60 s) for the desk. Typing holds it, `/next` ends it, and the night one is held
whatever the comms. While a window is open her `end` hands back to the desk rather than closing
the sol. A run with no window, or a replay, holds none: nobody is there.

- **Free before the sol.** Her words cost no mission time until her first call begins the sol
  (`Conversation.free`), so a question about her briefing is free.
- **Urgent is one-way,** and lives in the desk's terminal rather than her chat, because the desk
  does not talk to her while she works. It stops her after the call in hand
  (`Conversation.cut`), arrives marked URGENT, and she carries on under the clock. To answer she
  drives to the pad and radios. A briefing given while she is away from the pad arrives the same
  way.
- **Her chat holds what is meant for her:** `/start`, `/next`, the board and words. The terminal
  holds what runs the mission: `urgent`, `comms`, `sols`, `place`, and playing by hand.
- **The board** is mission control's numbered standing orders, posted and retracted one at a
  time. She reads it on every request and can't touch it, so she has no reason to spend her
  memory on the desk's rules.

## Her memory is named entries

Up to `MEMORY_ENTRIES` (10) entries of `MEMORY_CHARS` (300) characters. `remember(name, text)`
writes or replaces one, and `forget(name)` drops one; at the cap she forgets before she adds, as
the handoff's line cap works. All of it is in her view on every request. Her prompt carries the
rules our own memory keeps:
- one subject to an entry;
- change an entry rather than add a near-copy;
- forget what's no longer true;
- don't copy what the view already carries;
- write sols as numbers.

It was one paragraph, rewritten whole every night, and that rewrite is where a standing constraint
gets dropped. An entry she does not touch survives untouched. Replacing rather than appending,
settled in prototype 1, still holds per entry. Nights saved before this wake with their paragraph
as one entry called "note".

## The record and the report

The world keeps what was finished, and on which sol, plus where each sol ended and on what
charge. The view lists the finished work on every request. An unattended run once ended on a
note saying nothing had been found, after all three objectives were done, because the view only
listed open ones. `report.py` writes `report.md` from these records every nightfall and at the
end. Her note goes underneath it, labelled as hers. The dusk turn asks her for judgement only,
since the facts are the record's.

## When the cloud drops

`chat.Link` picks the model for the whole run. When a request to `MODEL` fails, the same request
goes to `MODEL_FALLBACK` (`gemma4:e4b`, local) at once. A one-token probe tries `MODEL` every
`PROBE_SECONDS`, and the first request after it answers goes back to the cloud. Each new sol
starts with a probe. Every cost row names the model that answered. `--outage N` stages an outage
for sol N through a port nothing listens on, and the tape marks it as staged.

## Replay

Replay re-issues a kept run's calls with no model, and halts if a result stops matching the tape.
Two fixes landed in 10c:

- **A sol she closed with time left is closed in the replay too.** Every call row carries
  `over`, whether the sol was already over when the call ran. Before, a drive asked for at dusk
  was refused live but ran in the replay, which then diverged.
- **A turn ends in the replay where it ended live,** even with no `end`: a cap's refusals ended
  it, or an urgent call. Every call row carries its `turn`, and the replay ends the turn idle at
  the same call. Otherwise the next turn's drive is refused against the old turn's allowance.
- **What the operator did lands before the call it came before.** A placement or an order
  typed in the morning window was there for the whole live sol, so the replay applies it before
  her first call, not at nightfall.

Tapes kept before 14 Oct diverge at their first `execute`, whose result no longer names
objectives she has not seen. Before that point they replay as they did. No window opens in a
replay, because nobody on a tape can be talked to. The desk's turns play as the clock's, and the calls inside them come out the same.

**Headless runs.** SIGTERM keeps the run and exits. Before, SDL turned it into the
keep-or-discard question, and a run with nobody to answer waited for ever. A run with no window
is kept as `runs/<stamp>-headless/`.

## For the team: start here

Work on a branch and open a pull request ([`../repo_rules.md`](../repo_rules.md)). Follow
[`README.md`](README.md); every suite in `game/` should pass. [`MANUAL.md`](MANUAL.md) has every
command.

- **Run a mission:** `--arena 50 --sols 3`, with `gemma4:e4b` for the machinery. Anything that
  becomes a conclusion gets repeated on `gemma4:31b-cloud`.
- **Brief her and talk at night.** Give a constraint in conversation, not on the board, and
  watch whether she keeps it in her memory, unprompted, across the sols it should last.
- **Try the board, a radio call, and `urgent` mid-drive** from your terminal (U).
- **Check what survives the night:** the map, her memory, the board, the finished objectives,
  and a stranding. `report.md` in the run directory is the record. P shows her memory.
- **`--resume runs/<stamp>`** wakes on the next sol. **`--replay runs/<stamp>`** plays it back
  without "REPLAY DIVERGED".
- **Report each result with its n,** and with its run directory.

## Not in 10c

- **Calling from anywhere at a battery cost,** with a partial recharge for coming back to the pad
  mid-sol. The numbers for both are open; next conversation.
- **`sos`.** It returns when hazards give her a reason to call from anywhere.
- **Objectives with a timer.**
- **The rover-bridge merge**, deferred until Ishan reviews it, and **Gemini keys and a test on
  Windows.**
- **Orders given at launch.** The morning window and the board cover it.
