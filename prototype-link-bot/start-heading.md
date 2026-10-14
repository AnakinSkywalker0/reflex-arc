# Start heading — which way the rover faces before its first move

The brain sends **absolute** directions (`N`, `E`, `S`, `W`), never "turn left" or "turn 90°".
So before its first move the rover has to know which way it really faces. Otherwise "go east"
can send it anywhere.

**Status: proposed by Krish, not yet agreed with the team. Nothing here is built.** The test
numbers below come from fake scans, not the real rover. The LiDAR plan this builds on is in
[`lidar.md`](lidar.md).

## The problem

- In prototype10d the rover starts at the **centre of the arena**, with the pad just south of it.
  Its first move can be in any of the four directions.
- The simulation **does not know which way the rover faces.** `route_actions` in
  `../prototype10d/game/nav.py` says so on purpose: turning is "the driver's business… It knows
  which way it is pointing; nothing here can."
- The rover is put down by hand, so it is never facing exactly one way.

Say the first leg is `E E E` and the rover just "turns 90° right". If it wasn't really facing
north, it now faces somewhere else, and every move after that is wrong.

## The rule: face a direction, don't turn an amount

The rover never trusts "I turned 90°, so I must be facing east". For every leg:

1. **Measure** the heading now with the LiDAR, for example "I face 12°".
2. **Work out the turn:** east is 90°, so turn 90° − 12° = **78°**. Always take the shorter
   way round.
3. **Turn**, then **measure again**. Within ±3° of east? If not, make a small fix, at most 3
   tries.
4. Only then drive.

This also covers wheel slip during turns, because every turn is checked against the room.

Headings, measured from the setup reference and clockwise like `HEADING_NAMES` in `nav.py`:
N = 0°, E = 90°, S = 180°, W = 270°.

## How the rover finds its heading at the start

It matches its first scan against the setup reference (see [`lidar.md`](lidar.md) § 2–3). The
reference was taken facing "north", so the match gives the exact heading.

It starts the match from several guesses (for example every 30°), keeps the best fit, and
checks whether a second, different heading fits almost as well.

## What the tests showed (fake scans)

Arena 4 × 3 m, 1.5 cm noise per reading, rover placed at home facing a random direction, 30
tries each:

| start | how it is placed | heading found right |
|---|---|---|
| near a corner | any direction | 30/30 |
| **centre of a plain rectangle** | any direction | **18/30**, and the other 12 were exactly 180° wrong |
| centre, with two boxes placed symmetrically | any direction | 18/30, the other 12 were 180° wrong |
| centre, with **one marker box in one corner** | any direction | 30/30 |
| centre of a plain rectangle | **roughly north (±40°)** | 30/30 |

**Why the centre is a problem:** from the middle of a rectangle, the room looks the same turned
180°. The rover can't tell north from south, so it would drive "east" while really going west.
Boxes don't help if they sit symmetrically.

## Possible solutions

| solution | how | good | bad |
|---|---|---|---|
| **A. Place it roughly north** | an arrow on the floor at home; put the rover down facing it, within about 40° | simple, and the 180° mix-up can't happen because the rover only searches near north | needs a person to place it, but only roughly |
| **B. One marker box in a corner** | a box in one corner only, so the room isn't the same both ways round | works from any starting direction | one more thing in the arena; it must be in the reference and never moved |
| **C. Home off-centre** | move the start cell away from the middle | the view from home is no longer symmetric | changes the sim's spawn, which is Ishu's code |
| **D. Ask a person** | if the heading is unclear, the rover stops and someone turns it | always safe | needs a person every time it happens |
| E. A compass (IMU) | an extra sensor | knows north on its own | the team already chose LiDAR only; compasses are badly thrown off by motors indoors |

**Suggested: A and B together, plus a safety rule.**

- **A** makes the normal case easy.
- **B** is the backup in case someone puts the rover down badly.
- **Safety rule:** if two headings fit almost equally well, the rover replies
  **`FAILED: can't tell which way I face`** and does not move. A guess could send it the
  opposite way.

## North has to come from the room, not the hand

Whichever way the rover faces when the **reference** is taken at setup becomes "north" for the
whole run. If it is put down 3° off then, the whole grid is 3° turned compared with the boxes on
the floor: about 5 cm of error per metre, growing with distance from home.

Fix: at setup, find the longest straight wall in the home scan and make "north" point exactly
along it. Then the grid lines up with the room, however the rover was placed.

## The start of a run, step by step

1. Put the rover on the home mark, roughly facing the north arrow.
2. It scans, matches the reference, and gets its exact x, y and heading, for example "7° left of
   north".
3. If the heading is unclear, it replies `FAILED` and waits for a person.
4. The brain sends the first leg, for example `E E E`.
5. The rover turns from −7° to 90° (97° right), checks within ±3°, and fixes if needed.
6. It drives 3 cells, stops, measures, and reports the real cell. From here it is the normal loop
   in [`lidar.md`](lidar.md) § 4.

## Not decided yet

- A, B, C or a mix. A + B is suggested.
- Where the marker box goes, and its size.
- How close "almost as good" is before the rover says `FAILED`.
- The ±3° limit, which is a guess until tested on the floor.
- Whether 180° turns are done as two 90° turns with a check after each (safer in a symmetric
  room), or as one.
- Whether turning should cost time or battery in the sim. Today it costs nothing, because the
  sim doesn't know about facing.
