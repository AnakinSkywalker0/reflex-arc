# The LiDAR — how the rover knows where it really is

The LiDAR has one job: **after every move, say where the rover really is and which way it
really faces.** It does not look for obstacles. The simulation does that, and the rover is only
ever handed ground the simulation has already driven.

**Status: proposed by Krish, not yet agreed with the team. Nothing here is built.** The numbers
under "How well it works" come from fake scans, not the real rover.

## The idea in one paragraph

The rover moves in four directions only (N, E, S, W). After each leg it stops, takes a LiDAR
scan, and compares that scan with a **reference** made at setup time: a few scans of the empty
arena, taken before the run. Lining the two up gives the rover's real position (x, y) and its
real angle. The angle is corrected, because a wrong angle makes every later move wrong. The
position is **reported, not corrected**: the brain is told the real cell and A\* replans from
there, as [`../ARCHITECTURE.md`](../ARCHITECTURE.md) asks.

## No ROS

This plan uses plain Python and numpy on the Pi. It does not use ROS, slam_toolbox, rf2o or Nav2.
The stack in `rover/` stays in the repo as it is, but this design does not need it.

Why:

- **We need two numbers, not a robot framework:** where am I, and which way do I face. A small
  program can work those out from the walls of the arena.
- **Less to break.** The ROS stack needed Docker, a messaging fix (`no_shm.xml`), scan cleaning
  and a 330 MB/day log fix just to run.
- **We understand every line.** That fits the project's "build it yourself" rule.
- **It runs on a Pi 4B too.** One match takes about 5 ms on a laptop.

What we lose: Nav2's steering round obstacles. We don't need it, because the simulation decides
the path. We keep one simple safety brake instead (see "Safety").

## The pieces

| file (to write) | what it does |
|---|---|
| `rover/ld19.py` | reads the LD19 over serial and gives back one full 360° scan, 10 times a second |
| `rover/scan_match.py` | the maths: turn a scan into points, match points to the reference, find a turn angle |
| `rover/reference.py` | the setup step: takes the arena scans and saves them as the reference |
| `rover/drive.py` | turns and drives using the motors, checking with the LiDAR, and returns the result |

Motor control reuses the PWM code from `rover/l298n_node.py` as plain `gpiozero` code, **with
its measured duty range kept**: 8.2 % (below this it doesn't move) to 15.4 %.

## 1. Reading the LD19

The LD19 sends data by itself as soon as it has power: no commands. Over serial at **230400
baud**, 8N1, it sends packets of **47 bytes** ([LD19 manual][manual]):

| bytes | what |
|---|---|
| 1 | header, always `0x54` |
| 1 | `0x2C` (12 points in this packet) |
| 2 | spin speed, degrees per second |
| 2 | start angle, in 0.01° |
| 12 × 3 | each point: distance in mm (2 bytes), then brightness (1 byte) |
| 2 | end angle, in 0.01° |
| 2 | time in ms (counts to 30000, then starts again) |
| 1 | CRC-8 check over all the bytes before it |

All numbers are little-endian. The 12 points sit evenly between the start and end angle. Watch
for the end angle wrapping past 360°. The manual's own example has a wrong number in it, so
trust the field list, not the example.

`ld19.py` does this:

1. Read bytes until it finds `0x54 0x2C`, then read the rest of the 47.
2. **Check the CRC.** If it fails, throw the packet away. Never use a bad packet.
3. Collect points until the angle goes past 360° and starts again. That is one full turn.
4. Throw away points that are too close or too far: under 5 cm (often the rover itself), over
   8 m, or very dim.
5. Give back the turn as `angle, distance` arrays.

**Two things that catch people out:**

- **The LD19 counts angles clockwise**, with 0° at the sensor's front ([Waveshare][waveshare]).
  Normal maths, and the game's grid, count anticlockwise. Flip the sign once, in `ld19.py`, and
  nowhere else.
- **The LD19's 0° may not point at the rover's front.** Measure the offset once (step 1 of
  "Setup") and put it in the config.

Spec, for reference: 10 turns a second, 4500 points a second, so about 450 a turn (Nithin's
stack saw 500–505), 0.02–12 m range, about 10 mm accuracy beyond 30 cm ([Waveshare][waveshare]).

## 2. The reference: a picture of the empty arena

Matching every scan against **one** home scan works, until the rover is far from home. Out
there it sees walls and sides of boxes that home never saw. In the fake-scan tests that is where
the bad matches came from.

So at setup we take **about five scans**: home, the four corners' areas and the middle. We join
them into one set of points, the reference. This is a very small map that we make ourselves.

How: put the rover at the next spot, give a rough guess of where it is (tape measure, ±20 cm is
enough), match it against what the reference has so far, then add its points. Home goes first
and sets the zero point.

**Home sets the grid.** Home is cell (0, 0)'s corner, or the sim's spawn cell, and the rover's
facing at home is the grid's "north" (or east, pick one). Mark that spot and that direction on
the floor. Every run starts there.

**If boxes in the arena move, make the reference again.** It takes a couple of minutes.

## 3. Matching a scan: ICP

ICP (iterative closest point) lines up two sets of points:

1. Move the new scan's points to where we **guess** the rover is.
2. For each point, find the nearest reference point.
3. Find the small move and turn that brings each pair closest. Use point-to-line, which measures
   along the wall's direction and slides better along walls than point-to-point.
4. Apply it and repeat. Stop when the move becomes tiny, usually after 10–40 rounds.

Two details matter:

- **Ignore pairs that are too far apart.** Start at 25 cm and tighten to 5 cm as it settles.
  That drops people, bags and anything not in the reference.
- **The guess must be close:** within about **30 cm and 15°** in the tests. Past 40 cm / 20° it
  starts locking onto the wrong place. The guess comes from the before/after measurement (next
  section), which is usually within a few cm.

The answer is the rover's **x, y in metres and its angle**, measured from home.

## 4. When to calculate what

### During a turn: watch the angle change

To turn 90°, we only need **how much the angle changed**, and it has to be fast.

- Take a scan just before the turn.
- While turning, slide each new scan round, degree by degree, and find where it lines up best
  with the before scan. That shift is how far the rover has turned so far.
- **Only search near the expected angle** (for example 0°–130° for a 90° turn). A square room
  can look the same at 90° and 180°, and a narrow search avoids the wrong one.
- Slow the motors in the last 15° and stop at the target.

### After the turn: check and correct

- Stop, wait about 0.3 s for it to settle, then take a scan and run ICP.
- If the angle is off by more than **3°**, do a small extra turn and check again, at most 3 tries.
- This is the one place we **correct**. A 5° error drifts the rover about 14 cm sideways over 4
  cells of 40 cm.

### During a straight drive: drive, and keep the brake on

- Drive the leg (option (a) below), checking only the safety brake.
- Don't measure the position while moving. A scan taken while moving is smeared.

### After each leg: the real position

1. **Stop and wait** about 0.3 s.
2. Take **about 5 scans** (half a second) and join them. That gives fewer gaps and less noise.
3. **The guess:** where the rover was before the leg, plus how far the wall ahead or behind came
   closer (the before/after reading).
4. **Run ICP** against the reference. That gives the real x, y and angle.
5. **Cross-check:** if ICP and the before/after guess disagree by more than **15 cm or 8°**,
   something is wrong. Try again once. If they still disagree, reply `FAILED`.
6. Turn metres into a cell: `cell = round(x / CELL_SIZE)`, the same for y.
7. Reply to the brain:
   - `DONE`: within a quarter of a cell of the target centre;
   - `SHORT`: otherwise, with the real cell;
   - `BLOCKED`: the safety brake stopped it;
   - `FAILED`: the match failed or the cross-check failed.
8. **Keep the exact metres on the Pi.** The next leg aims at the true centre of the next cell,
   so a few cm of error doesn't grow.

The brain trusts the reply, moves its rover to that cell, and A\* replans from there.

## 5. Driving: two options, not decided

- **(a) Drive blind, then measure.** Run the motors for the time the leg should take, stop,
  measure. Real errors happen and the brain replans from them, which is what the demo is meant
  to show.
- **(b) Measure while driving.** Watch the distance to the wall ahead and stop when the leg's
  distance is covered. This is more accurate, so `SHORT` would mostly mean blocked.

Leaning (a) for the demo. (b) is easy to add later.

`plan.txt` says directions (`N`, `E` ...), not turns. `drive.py` remembers which way the rover
faces and works out the turn: facing N, told E = turn right 90°.

## 6. Safety

The simulation decides the path, but the real floor can differ: a foot, a bag, a box nobody put
in the sim.

- **Brake:** while driving forward, if any point within ±20° of straight ahead is closer than
  about **20 cm**, stop at once and reply `BLOCKED`.
- **Stop if the LiDAR goes quiet** (no full turn for 0.5 s): stop and reply `FAILED`.
- **Stop when the link is lost** ([`grpc-link.md`](grpc-link.md#safety)).
- **Every exit path stops the motors,** including crashes (`try / finally`).

## How well it works (fake scans only)

Tested here on made-up scans: an arena of 4 × 3 m with two boxes, 1.5 cm of noise on every
reading, 3 % of readings dropped, and 40° of view hidden behind the rover's own mast. The rover
was placed up to 25 cm and 10° away from where it was sent.

| setup | bad matches (>5 cm off) | typical error | 95 % within |
|---|---|---|---|
| one home scan, point-to-point | some up to 17 cm | 2.1 cm, 0.4° | 10.6 cm |
| one home scan, point-to-line | 2 of 195 (up to 50 cm) | 0.2 cm | 0.5 cm |
| **5 setup scans + guess from before/after** | **0 of 197** | **0.2 cm, ~0.1°** | **0.4 cm** |
| with a person standing 50 cm away | 0 of 20 | 0.3 cm | max 0.5 cm |

**What this means:** the method is sound, and the two fixes (several reference scans and a good
guess) remove the bad matches. **Real scans will be worse.** Real walls aren't perfectly flat,
the LD19 is noisier than the model, and the rover tilts as it brakes. Expect **a few cm and about
1°** on the floor until measured. That is still far smaller than a 30–40 cm cell.

Speed: one match took about **5 ms** on a laptop. A Pi should be well under a second.

## Problems we expect, and the fix for each

| problem | what happens | fix |
|---|---|---|
| Sideways drift while driving straight | ends in the wrong row, though "distance ahead" looks right | ICP measures x **and** y, not only forward distance |
| Small errors adding up over many legs | the sim thinks it's in one cell, the rover is in the next, and the sim's obstacle check is for the wrong cell | always match against the fixed reference, never chain before/after |
| Far from home, the home scan doesn't fit | wrong match, up to 50 cm off | 5 setup scans as the reference |
| Guess too far off | ICP locks onto the wrong spot | guess from before/after, plus the 15 cm / 8° cross-check → `FAILED` |
| Square room looks the same turned 90° | wrong turn angle | search only near the expected angle |
| Scanning while moving | smeared scan, wrong pose | measure only when stopped, after 0.3 s |
| Rover hides part of its own view | fake close points | cut points under 5 cm, and mask the blocked angles once |
| LD19 0° isn't the rover's front | every angle off by a constant | measure the offset once at setup |
| LD19 counts clockwise | left and right swapped | flip the sign once in `ld19.py` |
| Glass, shiny black, sunlight | missing or wrong readings | plain cardboard walls, no direct sun |
| People walking at the edge | some wrong points | far pairs are ignored; keep the edges clear anyway |
| Boxes moved since setup | reference no longer fits | make the reference again, about 2 minutes |
| Real arena doesn't match the sim map | the sim's path isn't safe on the floor | build the arena from the sim map, marked from home; the brake catches the rest |
| Wheel slip on a turn | under-turns | the angle check after each turn corrects it |

## Setup, before a run

1. **The LiDAR's front offset.** Point the rover at a wall square on, find the angle of the
   shortest reading, and save it as the offset.
2. **Blocked angles.** Take a scan in an open space. Any angles that always read under 10 cm are
   the rover itself; save them as a mask.
3. **Arena.** Walls at least as tall as the LiDAR. Boxes on their cells, as the sim map shows.
4. **Home.** Rover on the marked spot, facing the marked direction.
5. **Reference.** Run `reference.py` and take the five scans.

## Testing, before linking to the brain

Each step uses a **tape measure** as the truth. Don't go on until it passes.

1. **Still:** 20 matches with the rover not moving. They should all agree within 1 cm and 0.5°.
2. **Pushed by hand:** put the rover on 10 tape-measured spots. Within about 3 cm?
3. **Turned by hand:** turn it on the spot by known angles (protractor or floor marks). Within
   about 1–2°?
4. **Real turns:** 20 turns of 90° under power. Each ends within 3° after correcting?
5. **Real legs:** 1, 2 and 4 cells in each direction. Does the reported cell match the tape?
6. **Brake:** put a box in the way. Does it stop and say `BLOCKED` every time?

## Not decided yet

- Whether the team agrees to drop ROS for this.
- **Cell size** on the floor. Suggested 30–40 cm for a 31 cm rover.
- Option (a) or (b) for driving.
- The `DONE` / `SHORT` line: a quarter of a cell is a guess until tested.
- The safety brake distance (20 cm) and angle (±20°).
- Whether the LiDAR sits near enough to the turning centre. Far off-centre makes the turn check
  slightly worse.
- Which way "north" points at home.

[manual]: https://elecrow.com/download/product/SLD06360F/LD19_Development%20Manual_V2.3.pdf
[waveshare]: https://www.waveshare.com/wiki/DTOF_LIDAR_LD19
