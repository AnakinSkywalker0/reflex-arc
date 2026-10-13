# AGENTS.md — prototype-link-bot

Working rules for any AI coding agent in this folder. The repo-wide rules in
[`../CLAUDE.md`](../CLAUDE.md) and [`../repo_rules.md`](../repo_rules.md) still apply; this file
adds what is specific to the rover side. What the folder is and why each piece exists is in
[`README.md`](README.md) — read that first, not the whole repo.

## What this folder is

The ROS 2 Humble stack from the rover's Raspberry Pi 5, copied as it last worked. It maps a room
with an LD19 LiDAR and drives back to its start point with Nav2. The job ahead is linking it to
the language-model planner in `../prototype10c/`. That link does not exist yet.

## The code runs on a robot, not here

- Nothing in `rover/` can be run or tested in this workspace. It needs the Pi, the `rover_ros2`
  Docker container, the LiDAR and the motors. Say so rather than claiming a change works.
- Paths inside the files are the **Pi's** paths (`/root/...` in the container, `~/rover` on the
  host). Do not rewrite them to repo paths.
- `l298n_node.py` drives real motors. A sign error, a wrong pin or a missing stop moves the rover
  into a wall. Treat edits there and to `stop_cmd.py` as high risk and point them out.

## Keep as-is unless asked

These files were brought over unchanged on purpose. Do not tidy, rename or refactor them as a side
effect of other work:

- **Measured numbers are load-bearing.** `MOTOR_MIN_DUTY` 0.082 and `MOTOR_MAX_DUTY` 0.154 in
  `stack.sh`, `max_vel_x`, the footprint and goal tolerances in `nav2_params.yaml`, and
  `freq: 10.0` in `rf2o_params.yaml` all came from measuring this rover. The comments say how.
  Change one only with a new measurement behind it.
- **`l298n_node.py` keeps its name.** It now drives a SmartElex 15D over PWM; the name is kept so
  `stack.sh` doesn't change.
- **AMCL is off on purpose.** It failed to converge on this rover. `slam_toolbox` in localisation
  mode plus `reseed.py` replaced it. Don't turn it back on to "fix" localisation.
- **`no_shm.xml` stays.** Removing it brings back nodes freezing at startup.
- **The deadman is off on purpose** (`deadman:=0.0`), so every path that kills Nav2 must run
  `stop_cmd.py` after. Keep that true.
- Tidy-ups that are wanted, later, are in [`can_do.md`](can_do.md). Not before the demo.

## Building the link

The brain writes one leg at a time to `runs/plan.txt` as `N`/`E`/`S`/`W` lines, in grid cells,
and blocks in `_await_rover` (`../prototype10c/game/nav.py`) until the rover has driven it. The
rover takes goals in metres through Nav2. The expected building blocks from here are
`return_home.py`, `reseed.py` and `tf_pose.py` — see "The link to the brain" in the README.

Hold to the project's rules while doing it:

- **Errors are reported, not corrected.** Send back where the rover actually stopped. Don't
  re-drive to hide a miss from the model.
- **The rover is only handed ground the simulation has already driven.** Don't send it a plan
  ahead of the sim.
- **The transport is proposed, not yet agreed: gRPC** — see [`grpc-link.md`](grpc-link.md),
  and build in the order it gives once the team agrees. Long distance is in
  [`long-distance.md`](long-distance.md) and comes after the one-room link works. Cell size, the cell-to-map
  origin and the exact `.proto` messages are still undecided. Ask; don't pick one silently and
  write it up as settled.

## Writing docs and commits

- Plain, simple words. Short. Say what is undecided as undecided.
- Commit messages say what changed and why, in one readable sentence.
- Branch and open a pull request for the team repo. Don't commit `HANDOFF.md`, `.claude/`,
  transcripts or run logs.
