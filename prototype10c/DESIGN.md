# Prototype 10c — the rover works by itself

10c is 10b with the rover left to work on its own. A mission clock runs each sol in place of the
operator, the sol is a span of mission time, and the steps are a battery only the pad recharges.
If the cloud model drops, a local one takes over, and a report is written from the record every
night. The code was built in DA task 19 and lands here unchanged except for the fixes below. Next
comes the comms system, which decides when you can talk to her at all.

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

## Nobody on shift

`--auto` (`AUTOPILOT`) hands the operator's half of the sol to the clock (`autopilot.py`). The
clock opens the sol with a turn of its own, and opens another turn whenever one ends without her
choosing to stop. It closes the sol when she calls `end`, when the clock runs out, or after
`AUTO_TURNS` turns. Then it asks for tomorrow's note and rolls the night over. Its lines are
`auto` on the tape, never `you`, so a sol nobody coached can't be taken for one somebody did.

- **With nobody there, `end` closes the sol.** The exception is an `end` sent after a cap
  stopped the turn. That one gets a fresh turn, because the cap sent her to `end` and the first
  unattended run lost 116 steps to it.
- **C takes the rover over mid-sol, and C hands it back.** She is told who has the rover at her
  next turn, and the prompt is swapped then.
- **A request that never reached the model** is asked again after `AUTO_RETRY_SECONDS` and is
  not counted as a turn.

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
  it, or later an urgent call. Every call row carries its `turn`, and the replay ends the turn
  idle at the same call. Otherwise the next turn's drive is refused against the old turn's
  allowance.

Tapes kept before these fields existed replay as before. The DA's two final-code runs replay with
0 mismatches.

**Headless runs.** SIGTERM keeps the run and exits. Before, SDL turned it into the
keep-or-discard question, and a run with nobody to answer waited for ever. A run with no window
is kept as `runs/<stamp>-headless/`.

## Next in 10c: comms

Decided on 13 Oct, and not built yet. Mission control can talk to her only when someone is at the
desk:

| | beside the pad | away from the pad |
|---|---|---|
| **comms on**: someone will answer | normal talk, both ways | urgent only: U from us, `sos` from her |
| **comms off**: she knows nobody is there | nothing | nothing |

At night beside the pad she reports, and the line stays open for 60 s of silence. An urgent call
stops her after the call in hand. The clock always runs, so `--auto`, C-to-take-over and the
operator-runs-every-sol mode go. 10b keeps that mode.

## For the team: start here

Work on a branch and open a pull request ([`../repo_rules.md`](../repo_rules.md)). Follow
[`README.md`](README.md); every suite in `game/` should pass.

- **Run it unattended:** `--auto --sols 3`, on the **design** preset (`--preset design`), with
  `gemma4:e4b` for the machinery. Anything that becomes a conclusion gets repeated on
  `gemma4:31b-cloud`.
- **Check what survives the night:** the map, the note, the orders, the finished objectives, and
  a stranding. `report.md` in the run directory is the record. P shows her note.
- **C mid-sol and back.** Type to her while you have the rover. That path is unit-tested only.
- **`--resume runs/<stamp>`** wakes on the next sol. **`--replay runs/<stamp> --auto`** plays it
  back without "REPLAY DIVERGED".
- **Report each result with its n,** and with its run directory. The same script has given 31,
  14 and 32 calls on one build.

## Not in 10c

- **The rover-bridge merge.** It is deferred until Ishan reviews it.
- **Gemini keys, and a test on Windows.** Both are deferred.
- **Orders given at launch.** An unattended run takes its orders from a resumed night or from
  TAB. With none, she is told to explore.
