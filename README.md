# Project Angaraka

**A Mars rover expedition in a classroom-sized arena, where a language model decides what the
rover does next.**

Mars is too far away to drive live, so a rover there runs a day of commands written on Earth the
day before. It can steer round a rock, but it cannot decide where to go. Angaraka puts that
decision on the rover: a model reads what it knows (its map, its position, what it has found and
what it was sent to do) and chooses the next move. The case in full is in [`ROVER.md`](ROVER.md).

## Reflex Arc

The architecture is called Reflex Arc. It splits the work three ways:

- **a language model decides** what is worth doing and where to go;
- **A\* plans** the route there;
- **a learned policy drives** it, reacting faster than anything that has to be thought about.

A language model knows what is worth doing and nothing about what the body can physically do. A
learned policy is the reverse. Each layer does only its own job. How they fit together is in
[`ARCHITECTURE.md`](ARCHITECTURE.md).

## The rover

The rover carries a 360° camera, which mimics the simulation's sight, and a LiDAR. The LiDAR
knows where fixed things are, which in testing means the room's four walls, and tracks the
rover's position from them. That is how wheel slip gets caught: the LiDAR reports where the rover
actually is, and the model replans from there. Errors are reported, not corrected.

## The code

[`prototype10b/`](prototype10b/) is the current build. It holds a fogged Martian plain in
pygame, the planner (a Gemma model served by Ollama, working through tools such as `goto`, `todo`
and `remember`), A\*, and `plan.txt`, the one-leg route file the real rover drives from. The
learned policy is not built yet, so for now the route drives the motors directly.

Setup, the tests and the keys are in [`prototype10b/README.md`](prototype10b/README.md). The one
dependency is pygame, in [`requirements.txt`](requirements.txt).

## Docs

| | |
|---|---|
| [`ROVER.md`](ROVER.md) | why a rover that decides, and what exists |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | how the three layers fit together |
| [`prototype10b/README.md`](prototype10b/README.md) | setup, settings and keys |
| [`prototype10b/DESIGN.md`](prototype10b/DESIGN.md) | how 10b works: the seam to the rover, the world, what is written down, replay, settings |
| [`docs/findings.md`](docs/findings.md) | what prototypes 1–9 settled; read it before changing how the model is spoken to |
