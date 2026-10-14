# prototype-link-bot — the rover side, ready to meet the brain

This folder holds the software that runs on the rover's Raspberry Pi 5. It was taken from
Nithin's Pi (`PI_5`) as it stood when it last worked, and it is kept here unchanged so the team
has one copy to build the link on.

On its own, this stack can already do one useful thing: **map a room with the LiDAR, then drive
back to where it started, by itself.** What it cannot do yet is take orders from the language
model in [`../prototype10c/`](../prototype10c/). Building that link is the job this folder exists
for.

## Where this fits

Reflex Arc has three layers ([`../ARCHITECTURE.md`](../ARCHITECTURE.md)):

| layer | job | where it lives |
|---|---|---|
| language model | decides *what* is worth doing | `prototype10c/` on the laptop |
| planner | works out *how* to get there | A\* in `prototype10c/`, and Nav2 here |
| driver | actually moves the wheels | this folder, on the Pi |

The rule that matters most: **errors are reported, not corrected.** If the rover was sent to a
cell and stopped short, it does not sneak back. The model is told where the rover really is and
plans again from there. The LiDAR is what makes "where it really is" trustworthy, and it replaced
the overhead camera the older plan used ([`../README.md`](../README.md#current-plan)).

## What is in here

```
prototype-link-bot/
  README.md            this file — for people
  AGENTS.md            working rules for AI coding agents
  CLAUDE.md            the same, for Claude
  grpc-link.md         the planned link to the brain, in one room
  long-distance.md     running that link far apart, and the methods for it
  lidar.md             the LiDAR without ROS: where the rover really is after each leg
  can_do.md            tidy-ups to do after the demo, not before
  rover/
    rover              the command you type on the Pi: ~/rover start, map, nav, stop ...
    stack.sh           what `rover` actually runs, inside the Docker container
    l298n_node.py      turns speed commands into PWM for the motor driver
    scan_normalize.py  cleans up the LiDAR's scans so the rest of ROS can use them
    reseed.py          finds where the rover is on the saved map, before driving
    return_home.py     sends the rover back to its start point through Nav2
    tf_pose.py         reads the rover's pose (x, y, heading) and prints or saves it
    stop_cmd.py        sends "stop" so the motors don't keep running
    nav2_params.yaml   Nav2 settings: speeds, rover size, how close counts as "arrived"
    slam_loc.yaml      settings for finding itself on a saved map
    rf2o_params.yaml   settings for working out movement from the LiDAR alone
    no_shm.xml         a ROS messaging fix that stops nodes freezing
    maps/room.*        the saved map of the test room (5 cm per pixel)
```

## What it uses, and why

**The hardware.** Six wheels, a Raspberry Pi 5, a SmartElex 15D motor driver, a buck converter
and an 11.1 V LiPo, about a foot long. An LDROBOT **LD19** LiDAR spins on top and sees the room's
walls. In this stack the LiDAR is the rover's only sense of position: nothing reads the wheels.
(The 360° camera in [`../ROVER.md`](../ROVER.md) is not used here.)

**ROS 2 Humble, inside a Docker container (`rover_ros2`).** ROS gives us mapping, localisation
and path-following that already work, so we don't write them from scratch. That is a deliberate
exception to the project's "build it yourself" rule: the learning goal is the brain and the
policy, not re-implementing SLAM. Docker keeps the ROS install separate from the Pi's own system,
so it can be rebuilt without touching anything else.

**PWM to the motor driver (`l298n_node.py`).** The driver used to be talked to over serial, but
it took about **2 seconds** to accept each command, so the rover crawled and overshot. PWM
applies a new speed within about 2 ms. The file kept its old name so `stack.sh` didn't need
changing; inside, the ROS node is called `smart_elex_15d`. The PWM range was **measured** on this
rover: below 8.2 % duty it doesn't move at all, and the top is pinned at 15.4 % so Nav2's idea of
speed matches the floor. Before that fix the rover ran almost 3× faster than Nav2 thought and
missed every goal.

**Cleaning the LiDAR (`scan_normalize.py`).** The LD19 sends a slightly different number of
readings each turn (500–505). SLAM expects the same number every time and was throwing away most
scans. This node re-sorts every scan into exactly 504 fixed slots, so nothing downstream breaks.

**Movement from the LiDAR alone (`rf2o`).** With no wheel encoders, the rover needs another way
to know how far it moved between moments. rf2o compares one LiDAR scan with the next and works
that out. It runs at 10 Hz to match the LiDAR, and its logging is turned down because at full
volume it wrote about 330 MB a day.

**Making the map (`slam_toolbox`, mapping mode).** You drive the rover around the room once; it
builds the map. Wherever you put the rover down when mapping starts becomes the map's origin, so
"home" is that spot.

**Finding itself on the map (`slam_toolbox`, localisation mode, plus `reseed.py`).** We first
tried AMCL, ROS's usual tool for this. On this rover it wandered and sometimes flipped 180°, so
it was dropped. Now `reseed.py` compares a fresh scan with the saved map, picks the best match,
and hands that pose to slam_toolbox. If the scan and the map don't agree anywhere, it **refuses to
drive** rather than driving from a wrong guess.

**Driving to a goal (Nav2).** Nav2 plans a path on the map (NavFn) and follows it (DWB). It knows
the rover's real size (310 × 245 mm) and counts the goal as reached within 15 cm. `return_home.py`
is the script that gives Nav2 its goal, and it **cancels the goal on any exit**, so the rover
can't keep driving after the script dies.

**Watching it (Foxglove).** `foxglove_bridge` lets you see the map, scans and path from a laptop
at `ws://<pi-ip>:8765`, and drive the rover by hand while mapping.

**The freezing fix (`no_shm.xml`).** ROS's default messaging used shared memory, which in this
container sometimes locked up nodes during startup — rf2o froze mid-run. This file tells ROS to use
plain network messages instead. The cost is negligible on one machine.

**Stopping (`stop_cmd.py`).** The motor node's "stop if nothing heard for 2 s" safety is turned
off, so hand-driving holds its last command. That means something must say *stop* when Nav2 is
killed, or the rover keeps going. `stack.sh` runs this after every stop.

## How to run it

SSH into the Pi, then:

```bash
~/rover start        # LiDAR, scan cleaning, rf2o, motors, Foxglove
~/rover map          # put the rover at its home spot FIRST, then start mapping
                     # drive it round the room from Foxglove
~/rover map save     # saves maps/room.{pgm,yaml} and where the rover is now
~/rover nav          # finds itself on the map and drives back home
~/rover stop         # everything off, motors told to stop
~/rover status       # what's running
~/rover logs <node>  # e.g. ~/rover logs rf2o
~/rover speed <1-9>  # motor power ceiling
```

Measured result after the speed fix: two full return-home runs landed **13 cm / 2°** and
**12 cm / 7°** from home, first try.

## The link to the brain — not built yet

Today the brain and the rover are two separate programs that have never been joined.

- **The brain** (`prototype10c`) thinks in **grid cells**. After driving a leg in simulation it
  writes the moves it made to `runs/plan.txt`, one `N`, `E`, `S` or `W` per line, then waits
  for the rover. That wait (`_await_rover` in `game/nav.py`) is empty right now — nothing is on
  the other end.
- **The rover** thinks in **metres on a LiDAR map**, and Nav2 wants a goal pose, not a list of
  steps.

The link has to sit between those two. The pieces it is expected to reuse from here are
`return_home.py` (giving Nav2 a goal and waiting for it), `reseed.py` (knowing the pose is
trustworthy before driving) and `tf_pose.py` (reading where the rover actually ended up, to
report back).

An earlier link, `rover_bridge/` and `rover_link.py` on the team repo's `rover-bridge` branch,
drove by **timed pulses** with no sensing — "go forward 1 second" — so its errors added up with no
way to notice them. This stack replaces that with closed-loop driving on the LiDAR.

**How the laptop and the Pi talk is proposed, not yet agreed:** gRPC on a local router, in
[`grpc-link.md`](grpc-link.md) — why, the commands, safety and the build steps. Running it far
apart (Tailscale, 4G, and later the brain on the rover) is in
[`long-distance.md`](long-distance.md).

**A simpler rover side is proposed** in [`lidar.md`](lidar.md): no ROS. Plain Python reads the
LD19, matches each stop's scan against scans of the arena taken at setup, and reports the real
cell. It is not agreed yet; the ROS stack stays here until it is.

**Not decided yet:**

- **Cells to metres.** How big one grid cell is on the floor, and where cell (0, 0) sits on the
  room map.
- **What the brain sends.** Each leg as one Nav2 goal at its end cell, or each N/E/S/W step as its
  own goal.
- **How the rover reports back.** Its pose read through `tf_pose.py`, turned back into a cell —
  and what counts as "stopped short" versus "arrived".
- **Which prototype it joins.** The README says hardware integration (prototype 12) forks from
  10b, 10c or 11, decided after 11.

## Rebuilding the Pi

This folder is not everything the Pi needs. Also required, and **not in this repo yet**:

- the `rover_ros2` Docker image with ROS 2 Humble, Nav2, slam_toolbox, rf2o, the LD19 driver and
  foxglove_bridge;
- `rosbg.sh` (starts a node in the background), `grade_map.py`, and the patched
  `ld19.launch.py` that publishes `/scan_raw`;
- `gpiozero` and `lgpio` for PWM on the Pi 5, with the container run `--privileged`.

Files go in `/root/` inside the container, and `rover` in `~/` on the Pi. After any change to
tyres, load or battery, re-measure the motor duty range before trusting Nav2's goals.

What's left to tidy after the demo is in [`can_do.md`](can_do.md).
