# Reflex Arc

**Language models decide. Learned policies act.**

> The language model doesn't waste its weights on learning movements.
> The reinforcement learning doesn't waste its weights on making informed decisions.

---

## The problem

A language model can reason about what ought to be done and has no idea what the body it is
driving can physically do. It plans *walk through that gap* when the gap is too narrow.

Learned control policies have the opposite deficit — precise, reactive, fast, and with no notion of
what is worth doing. A policy that can reach any coordinate you name has no opinion about which
coordinate matters.

## Two implementations

The architecture is the project. Anything it drives is an implementation, and there are two,
running in parallel with different teams.

**A rover.** A Mars expedition in a classroom-sized arena — trained in a simulator we write, then
driven on real hardware. Designed in [`ROVER.md`](ROVER.md).

**Hollow Knight.** The system plays a hard game start to finish, an Any% run. Designed in
[`docs/course.md`](docs/course.md).

## Current plan

*As of 11 October 2026.* Both SIH entries are in and the results will take a while. Until they
arrive, the work is making the project better, not the pitch.

**The rover has changed.** It now carries a 360° camera, which mimics the simulation's sight, and
a LiDAR. The LiDAR knows where fixed things are, which in testing means the room's four walls, and
tracks the rover's position from them well. That is how wheel slip gets caught. The LiDAR reports
where the rover actually is, and the model replans from there. Errors are still reported, not
corrected. The overhead camera in [`ARCHITECTURE.md`](ARCHITECTURE.md) is superseded.

1. **Cleanup — done 11 October.**
   - Prototypes 1–9 are archived in [`archive/`](archive/) and at the git tag `prototypes-1-9`,
     with their conclusions in [`docs/findings.md`](docs/findings.md).
   - Prototype 10 is frozen as [`prototype10a/`](prototype10a/), the build the Angaraka recording
     ran on.
2. **Prototype 10b, the base — built 11 October; the team is testing it.**
   [`prototype10b/DESIGN.md`](prototype10b/DESIGN.md) covers:
   - settings inside the app, each saying whether it applies now, at the next sol or after a
     relaunch;
   - the scratchpad on screen;
   - setup instructions;
   - resuming a kept run from the next sol.

   Then the team runs the multi-sol tests. No model has yet played past sol 1, and those runs
   decide what memory and the scratchpad become. The project team takes UI and UX from 10b.
3. **Prototype 10c, the rover by itself — autonomy landed 13 October; comms next.**
   [`prototype10c/DESIGN.md`](prototype10c/DESIGN.md) covers:
   - a mission clock that runs each sol, with a battery only the pad recharges;
   - home before dark, or stranded;
   - a local fallback when the cloud model drops;
   - a report written from the record.

   Next, the comms system: mission control talks to her only when someone is at the desk, from
   the pad, or by urgent call when she is away from it.
4. **Prototype 11 — Ishan.** A Martian simulation game, scoped in its own conversation. On the
   table:
   - a bigger map, with regions besides Jezero flats that each have their own hazards;
   - storms that move;
   - missions that span several sols, with enough objectives that choosing between them matters.

   The LiDAR is enacted, not implemented. Slip is injected, the rover stops short, and the result
   says so with its own code, distinct from `BLOCKED`. Still being discussed:
   - **chunks:** 50×50 cells, each a small block, with hazards and objectives taking whole chunks;
   - **a scripted baseline** to compare decisions against;
   - **how the view scales.** The grid view costs about 1,200 tokens at 50×50.
5. **Prototype 12 — hardware integration with the real LiDAR.** Owned by the team, with Koushik.
   Whether it forks from 10b, 10c or 11 is decided after 11.
6. **Documentation overhaul — Ishan, after 11 is scoped.** Two levels: plain docs for people,
   technical or not, and deep docs for developers and AI.

**Deferred:**
- merging Abhishek's `rover-bridge` branch, which Ishan reviews first;
- Gemini keys in the settings;
- a test run on Windows.

**Stale until the overhaul:**
- `ARCHITECTURE.md`'s camera section;
- `work_division.md`, which is the 4 September allocation;
- `rover_ideas.md`.

---

## Repository

**Reading order for anyone new:** this file → [`ROVER.md`](ROVER.md) →
[`ARCHITECTURE.md`](ARCHITECTURE.md) → [`docs/findings.md`](docs/findings.md) →
[`repo_rules.md`](repo_rules.md) before you push anything. On the coursework track,
[`docs/course.md`](docs/course.md) instead of the rover. Not the raw transcript.

| | |
|---|---|
| [`ROVER.md`](ROVER.md) | the hardware implementation — the hackathon track |
| [`rover_ideas.md`](rover_ideas.md) | the rover in full — the reasoning, and what was already cut |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | how the three layers fit together |
| [`work_division.md`](work_division.md) | who owns what |
| [`prototype10c/`](prototype10c/) | the current build — the rover working sols by itself; comms next |
| [`prototype10b/`](prototype10b/) | the base the team is testing — the simulation, the planner and the seam to the rover |
| [`prototype10a/`](prototype10a/) | prototype 10 frozen as the Angaraka recording ran it |
| [`docs/findings.md`](docs/findings.md) | what prototypes 1–9 settled — read before changing how the model is spoken to |
| [`archive/`](archive/) | prototypes 1–9, as a tarball |
| [`repo_rules.md`](repo_rules.md) | git, context budget, and how ideas get written down |
| [`docs/course.md`](docs/course.md) | the Hollow Knight implementation — the coursework track |
| [`docs/sih-decision.md`](docs/sih-decision.md) | which SIH entries we made, and why — closed; links both decks |
| [`docs/novelty.md`](docs/novelty.md) | is this actually new — prior art, verified against primary sources |
| [`docs/pitch.md`](docs/pitch.md) | how to explain the project to someone from nothing |
| [`docs/literature.md`](docs/literature.md) | reading list with links |
| [`docs/00-raw-transcript.md`](docs/00-raw-transcript.md) | original ideation, verbatim |

Rejected ideas keep their reasoning rather than being deleted, so they don't get rediscovered.

Four references worth the time: [SayCan](https://arxiv.org/abs/2204.01691) for grounding a language
model in what a machine can actually do · [ExpeL](https://arxiv.org/abs/2308.10144) for learning
from logged experience with no weight updates ·
[Trackmania](https://www.youtube.com/watch?v=zFLQU70QstY) for what precision control costs to train
· [OC-STORM](https://arxiv.org/abs/2501.16443) for the game as a published benchmark.
