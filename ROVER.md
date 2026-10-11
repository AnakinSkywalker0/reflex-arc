# The rover

Perseverance has been driving across Jezero Crater since February 2021. It crosses ground nobody
has stood on, photographs it, drills rock and stores the samples. Ingenuity, a small helicopter,
flew with it — up over the terrain ahead, looking at ground the rover could not see yet.

Between them the job is the same one: cross the terrain, and carry out the missions along the way.

## The problem

Mars is 3 to 22 minutes away at the speed of light, each way. Nothing there can be driven live. By
the time a picture of an obstacle reaches Earth and an answer gets back, the better part of an hour
is gone and the rover has been sitting still for all of it.

So the driving is done from Earth, a day at a time. A team reads yesterday's images, decides where
the rover should go and what it should do there, writes the day out as a sequence of commands and
sends it up. The rover runs the day and the team finds out how it went tomorrow. It can pick its own
way around a rock in the path — that much is onboard. What it cannot do is decide where the path
should lead.

What if it decided for itself?

## Not a Roomba

A Roomba navigates. It covers the floor, avoids the furniture, finds its way back to the dock — and
it never decides anything.

Navigation is not the hard part. We want a machine that thinks: one
that can look at where it is, what it has found and what it was sent to do, and choose what to do
next.

## Reflex Arc

- **A language model decides.** What is worth doing, and where to go next.
- **A\* plans the route.** Given a destination, work out the way there.
- **A learned policy drives.** It handles the ground itself, reacting far faster than anything that
  has to be thought about.

The knowledge sits in the model, the reflexes sit in the policyn. What comes out is a machine that can make the call on the spot. How the three fit together is
in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## What exists

**The rover is built.** Six wheels, a Raspberry Pi 5, a SmartElex motor driver, a buck converter
and an 11.1 V LiPo, about a foot long. It carries a 360° camera, which gives it the sight the
simulation gives the model, and a LiDAR, which tracks its position against fixed features such as
the walls of the room. It decides nothing: it drives what it is handed and reports where it ended
up.

**The planner runs, and the route reaches the motors.** The model, A\* and the fogged simulation
are in [`prototype10b/`](prototype10b/), and a planned route already drives the real chassis. The
learned driving policy is not built yet: until it is, the route drives the motors directly. What
comes next is in the [README](README.md#current-plan).
