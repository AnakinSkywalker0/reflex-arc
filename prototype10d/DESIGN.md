# Prototype 10d — the sol in four phases

10d makes a sol four phases you can see at a glance: dawn, day, dusk and night. The desk
talks with her at dawn and at night. The day is hers, on a wall clock that nothing pauses.
At dusk she reports. Work comes in two kinds: interests she has to find, and objectives
the desk gives her. Every command and key is in [`MANUAL.md`](MANUAL.md).

10c modelled the comms on a real Mars mission, and the 13 Oct run showed where that went
soft:
- the night line stayed shut after comms came back on;
- `execute` named every objective, fogged or not, and she drove to both high-priority
  ones off that list;
- a report radioed at dusk ended her turn before her memory was written;
- the clock jumped, because each step cost a second of mission time at the moment the
  drive was planned.

10d is built for the demonstration instead: a simple model that a person watching can
follow. It starts as a copy of 10c with those four fixes, and 10c stays as it was.
Everything not listed here is inherited from
[`../prototype10c/DESIGN.md`](../prototype10c/DESIGN.md).

## The four phases

| phase | what she does | what the desk can do | how it ends |
|---|---|---|---|
| dawn | reads her memory, the board and the work; sets up today's list | talk, post orders | `/next`, or 60 s of quiet |
| day | works: drives, does the work, keeps her list | one urgent message; answer her radio | her `end`, the clock, a flat battery, or Q |
| dusk | brings her memory up to date, then reports as her last words | read | `/next`, or 60 s of quiet |
| night | answers | talk, post orders | `/next`, or 60 s of quiet |

Looking and writing (`distance`, `count`, `count_cells`, `todo`, `strike`, `remember`,
`forget`) work in every phase. Driving, work, `radio` and `end` are the day's. A call outside
its phase is refused, and counts as a look. The arena is washed by phase: clear by day,
dark at night, lit from the east at dawn and from the west at dusk.

`/next <words>` moves on and hands her the words with whatever she is sent next: the day's
opening, the turn after a radio line closes, the night, or the next dawn.

**Comms on means someone is watching.** Each phase waits for the desk. **Comms off means
nobody is at the desk.** Every phase moves on by itself as soon as she is quiet, no urgent
message can be sent, and she has no radio. A run with no window behaves as comms off.

## The day runs on the wall clock

The day is `DAY_SECONDS` (600) of real time from the moment it begins, and nothing pauses it.
Her thinking, each drive and each piece of work as it is drawn, the settle after them, and
any radio line all happen on it. Work is drawn a step at a time at a driving step's pace, so
`execute` costs its steps in battery and their time on the day. A drive or a piece of work
that starts before the clock runs out finishes; the next call is refused. A flat battery
ends the day where the rover stands. Replay runs no clock: every call row carries the clock
it ran on, and the replay sets it from there.

**`end` is the day, and only hers.** A turn also ends when either allowance runs out (20
drives, or 10 looks between drives), when an urgent message cuts it, when she radios, or
when she replies with no call in it. Each time, the clock opens the next turn with both
allowances back. She never calls `end` for a cap.

## The desk by day

**One urgent message.** By day, anything typed in her chat is the urgent message: words, or
a change to the board. It reaches her after the call in hand, marked URGENT, and ends her
turn, not her day. Only one can be waiting at a time. A board change at dawn or night is
told to her as a line she can answer.

**Her radio.** `radio` works by day from anywhere and costs `RADIO_STEPS` (5) of battery. It
ends her turn and opens a line. While the line is open, every reply she speaks costs the
same. The line closes after 60 s with nothing said, or on `/next`, and she carries on. The
clock runs throughout, so a long conversation costs her the day as well as the battery, and
her prompt tells her to ask for the line to close. An `end` on the line closes the day.

## Two kinds of work

**Interests** are the arena's: the old objectives, each now carrying what is there ("signs of
past water", "a vein of a rare mineral") instead of a priority. Nobody knows where they are.
One shows on her map as `*` only once the rover has come within sight of it since it was
placed. Placed on ground already mapped, it stays hidden until she drives near it again. The
drive that finds one says so.

Examining one (`execute` beside it) is the only place its text appears. Her view then lists it
as examined, without the text, so carrying what she found into her report is her memory's
job. `report.md` has the text from the record, to check her against.

**Objectives** are mission control's, with a priority and a cost. They go only on ground the
rover has mapped, so she sees each one the moment it exists. `place X Y high 40` places one.
`--objectives auto` places three from sol 2, one of each priority, on mapped open ground
seeded by the sol. A new set comes only once every one of the last set is finished.

## What she is told, and what she is not

Every list she reads names only work she knows of: objectives, and interests she has found.
That holds for refusals too. Before every call she sees:
- the open objectives;
- the interests she has found;
- the finished work, by sol, with no interest's text;
- her memory, the board and her list.

Her dusk report is kept for `report.md`, under "Her reports at dusk".

## Replay and resume

- **What a call row carries:** its phase and its clock, which a replay sets before re-issuing
  it.
- **What the tape also carries:** the battery her words cost on an open radio line, in order
  with the calls, so a replay spends it before the call that followed.
- **What a replay re-applies:** auto objectives, placed objectives and hidden interests, as
  operator rows.
- **Nights saved by 10c do not resume here,** because their work was all objectives.

## For the team: start here

Work on a branch and open a pull request ([`../repo_rules.md`](../repo_rules.md)). Follow
[`README.md`](README.md); every suite in `game/` should pass. [`MANUAL.md`](MANUAL.md) has every
command.

- **Run a mission:** `--arena 50 --sols 3 --objectives auto`, with `gemma4:e4b` for the
  machinery. Anything that becomes a conclusion gets repeated on `gemma4:31b-cloud`.
- **At dawn, give her a constraint in conversation,** not on the board. Then watch whether
  she keeps it in her memory, unprompted, across the sols it should last.
- **Watch the interests.** Does she examine one when she finds it? Does what it was reach
  her memory and her dusk report? `report.md` has the truth beside her words.
- **By day, send one urgent message that asks a question,** and see whether she answers by
  radio.
- **Report each result with its n,** and with its run directory.

## Not decided, and not in 10d

- **The numbers.** 600 s and 500 steps are 10c's. At the 13 Oct run's pace, 500 steps last
  about three minutes of a ten-minute day, so the clock binds only when she talks. To be
  set from runs.
- **The display now changes outcomes.** ANIM_SPEED and SPACE (skip the drive) change how much
  fits in a day.
- **A call she starts herself.** Today the radio is mostly for answering an urgent message.
  What a call she starts should be for is left for later; nothing in the arena gives her a
  reason yet.
- **Objectives with a timer.** Without one, an auto set she leaves a low-priority objective
  in never refreshes.
- **`sos`**, once hazards exist, and a partial recharge on mid-sol pad visits.
- **The rover-bridge merge, Gemini keys and a test on Windows.**
