# Prototype 10c — the rover works by itself

10c is 10b with the rover left to work on its own. A mission clock runs every sol, the sol is a
span of mission time, and the steps are a battery only the pad recharges. Mission control can talk
to her only when someone is at the desk: beside the pad, or by urgent call when she is away from
it. If the cloud model drops, a local one takes over, and a report is written from the record
every night. The clock, battery, fallback and report were built in DA task 19. Comms and the
fixes below were added on 13 Oct.

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
out, or after `AUTO_TURNS` turns. Then it asks for tomorrow's note and rolls the night over. Its
lines are `auto` on the tape, never `you`, so a sol nobody coached can't be taken for one somebody
did. The operator-runs-every-sol mode is gone from 10c; 10b keeps it.

- **Her `end` closes the sol.** The exception is an `end` sent after a cap stopped the turn,
  which gets a fresh turn instead. The cap sent her to `end`, and the first unattended run lost
  116 steps to it.
- **A request that never reached the model** is asked again after `AUTO_RETRY_SECONDS` and is
  not counted as a turn.
- **The SPACE pause is off by default** (`ROVER_PAUSE none`), since nobody has to be at the keys.
  `key` still works for a run with a rover on the floor.

## Comms: someone at the desk, or nobody

`COMMS` says whether anyone is at mission control's desk, and she is told which.

| | beside the pad | away from the pad |
|---|---|---|
| **comms on**: someone will answer | talk both ways: TAB from the desk, `radio` from her | urgent only: U from the desk, `sos` from her |
| **comms off**: she knows nobody is there | nothing | nothing |

**A line** opens when one side calls, or at night when the sol ends beside the pad with comms on,
after she has reported. While it is open the clock opens no turns. The desk's messages open them,
and her `end` hands back to the desk, because the clock only takes an `end` as closing the sol in
a turn it opened. The line closes on N, or after `COMMS_WAIT` (60 s) with nothing typed and nothing
being said. By day the clock then has the sol back and tells her so; at night the next sol opens.

- **A call from the desk** stops her after the call in hand (`Conversation.cut`). The drive it
  started finishes, and nothing more is asked. An urgent call's first line reaches her marked
  URGENT. U works while the sol runs; once it is over, the night line is the channel.
- **Her calls** are two skills, offered only when they can get through, because what is not
  offered cannot be asked for. `radio` is offered beside the pad and `sos` everywhere, and
  neither when nobody is at the desk. A call that gets through ends her turn. Nothing in the
  world gives her a reason for `sos` yet; hazards will.
- **Changing comms mid-sol** swaps her prompt at the next turn and tells her. A line open when
  the desk leaves closes as soon as she has finished speaking.
- **A run with no window starts with comms off,** because nobody is there to answer.

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
0 mismatches. No line opens in a replay, because nobody on a tape can be talked to. The desk's
turns play as the clock's, and the calls inside them come out the same.

**Headless runs.** SIGTERM keeps the run and exits. Before, SDL turned it into the
keep-or-discard question, and a run with nobody to answer waited for ever. A run with no window
is kept as `runs/<stamp>-headless/`.

## For the team: start here

Work on a branch and open a pull request ([`../repo_rules.md`](../repo_rules.md)). Follow
[`README.md`](README.md); every suite in `game/` should pass.

- **Run a mission:** `--sols 3`, on the **design** preset (`--preset design`), with
  `gemma4:e4b` for the machinery. Anything that becomes a conclusion gets repeated on
  `gemma4:31b-cloud`.
- **Talk to her at night.** Plan the next sol on the line, or with `/orders`, and see whether it
  shows in what she does.
- **Press U mid-drive,** tell her to come home, then N. Try TAB beside the pad, and C off and on.
- **Check what survives the night:** the map, the note, the orders, the finished objectives, and
  a stranding. `report.md` in the run directory is the record. P shows her note.
- **`--resume runs/<stamp>`** wakes on the next sol. **`--replay runs/<stamp>`** plays it back
  without "REPLAY DIVERGED".
- **Report each result with its n,** and with its run directory. The same script has given 31,
  14 and 32 calls on one build.

## Not in 10c

- **The rover-bridge merge.** It is deferred until Ishan reviews it.
- **Gemini keys, and a test on Windows.** Both are deferred.
- **Orders given at launch.** A run takes its orders from a resumed night or from the night
  line. With none, she is told to explore.
- **Anything that makes her call `sos`.** Hazards and damage are parked.
