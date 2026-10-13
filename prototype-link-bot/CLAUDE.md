# CLAUDE.md — prototype-link-bot

The rules for this folder are in [`AGENTS.md`](AGENTS.md), so every coding agent reads the same
ones. Follow them as written:

@AGENTS.md

Two things to add for Claude:

- **Read narrowly.** Start with [`README.md`](README.md) and open only the `rover/` files the task
  touches. `stack.sh`, `nav2_params.yaml` and `slam_loc.yaml` are long; search them instead of
  reading them whole.
- **You can't reach the Pi.** If a task needs the rover — a measurement, a run, a log — say what
  to run and what to look for, and let the person report back.
