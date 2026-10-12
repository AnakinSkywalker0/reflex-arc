# Architecture

| layer | what it answers | how fast it thinks |
|---|---|---|
| **language model** | what is worth doing | seconds |
| **A\*** | how to get there | milliseconds |
| **learned policy** | how to actually move | real time |

The whole design is the refusal to let any one of them do all three.

## The chain

```
   language model            "the interesting ground is north-east"
        │
        │   goto(12, 4)
        ▼
   A*                        replans until it has a route that works
        │
        │   3 up · 2 right · 2 up · 1 left · 4 up
        ▼
   learned policy            trained in Unity to cross one cell
        │
        │   W / A / S / D, held for as long as it takes
        ▼
   the body                  the simulation, and the rover on the floor
        │
        └──────  where it actually ended up  ──────►  back to the language model
```


## The grid

The world is cells, each with an `x, y`. The model names a cell, A\* moves between cells in whole
steps, and the policy crosses one cell at a time. One coordinate system runs from the model down to
the motors.

Routes come back run-length encoded — `3 up, 2 right` rather than eleven separate instructions —
because that is both shorter to send and easier to read.

Unity and the floor rover receive the same plan. The rover has no map and no brain; it is a set of
motors that runs what it is handed, and a LiDAR that reports where it ended up. **Whatever happens
in the simulation happens on the floor** — and there will be disagreements.

## Errors are reported, not corrected

The rover was told to reach (3,4) and stopped at (3,3). We do not nudge it back.

Instead the language model is told: *you are at (3,3), not where you asked to be.* It plans again
from where it actually is.

A hardcoded table has no row for "you are not where
you thought you were." A frozen policy has no experience of it. A model with general knowledge can
simply take the new position and carry on — and that is a thing you can watch happen, live.

**Rotation is the exception.** A short turn is not a local error: get the heading wrong once and
every move after it is wrong, further out each time. Position error stays where it happened; heading
error grows with distance. So rotation is corrected, using the heading the LiDAR measures to recover
which way the rover is actually pointing.

## The LiDAR

The rover carries a LiDAR that measures its pose, position and heading, against fixed features
whose places are known: in testing, the room's four walls.

That is how wheel slip gets caught. A slipped wheel leaves the rover short of where it was sent, the
LiDAR reports where it actually is, and the model replans from there, as above.

[`prototype10b/`](prototype10b/) does not model any of this yet. Its simulated rover never slips,
and by default the operator presses SPACE when the real one finishes a leg.

## Open

- **Is the LiDAR the source of truth before every plan, or only when something looks wrong?** If
  position is re-read from the LiDAR each time, error never accumulates and the model is always
  told the truth. If it is dead reckoning between fixes, error compounds. Settle this explicitly.
- **Cell size, and how big the real map can be.** A foot-long rover turning in place needs most of a
  half-metre cell, which puts a room-sized floor at well under ten cells across. The simulator's grid
  is far larger. Whether the two have to match, and what breaks if they do not, is unanswered.
