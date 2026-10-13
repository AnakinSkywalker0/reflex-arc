# Connecting the bot to the brain

The brain (Reflex Arc on the laptop) and the bot (ROS 2 on the Pi) talk over **gRPC**. When they
are in different places, the same gRPC runs inside a **Tailscale** private network. ROS stays
inside the rover; the brain never needs ROS.

```
LAPTOP (brain)                              PI (bot)
Reflex Arc game  ── gRPC (over Tailscale) ──►  bridge (gRPC server)
                 ◄── position, results ──        │
                                                 ▼
                                            ROS 2: Nav2, SLAM, LiDAR, motors
```

## Why gRPC

gRPC is a way for two programs on different computers to call each other's functions. It runs
on top of HTTP, so it is HTTP with the parts we need already built in:

- **A contract.** One `.proto` file lists every command and reply. Both sides are built from it,
  so they can't disagree about the message format.
- **Time limits.** Every call has a deadline. No waiting forever.
- **Cancel.** Cancelling a move on the laptop tells the Pi at once, so it can brake. This is
  what an urgent call from the desk needs.
- **Knows when the line is dead.** Small keepalive pings notice a dropped link within seconds.
- **Live updates.** One call can stream the rover's position while it drives.

With plain HTTP we would build all of these by hand, and hand-built safety is where bugs hide.

Rejected:

- **ROS 2 over Wi-Fi.** Its messaging (DDS) is unreliable on Wi-Fi; it already froze on the Pi.
  It would also put ROS on the laptop.
- **Plain HTTP, WebSocket.** Work, but cancel, timeouts and live updates are all hand-built.
- **MQTT.** Needs a broker running somewhere, one more thing to fail.
- **SSH commands, a shared file.** Hacks, not a connection.

## The commands

| Command | What it does |
|---|---|
| `Move(route)` | Drive this route, then reply with where the rover really ended up |
| `WatchPosition()` | Stream the position several times a second while driving |
| `Stop()` | Brake now |
| `Status()` | Where are you, are you busy, is the map loaded |

`Move` replies with one of:

- `DONE` — reached the cell
- `SHORT` — stopped early; here is the real cell
- `BLOCKED` — something in the way
- `FAILED` — something broke (lost position, no map)

The brain trusts the reply, not the simulation. If the real cell is different, the game moves
its rover there and the model replans from it.

## The network

Two separate links can fail:

1. **Laptop ↔ Pi** — moves and positions.
2. **Laptop ↔ internet** — the cloud model.

One phone hotspot carrying both is the weakest setup: it sleeps, drops on calls, and some block
devices from seeing each other. Better:

- **Same room:** a small travel router (or the Pi's own Wi-Fi) for laptop ↔ Pi. The laptop gets
  internet from a phone over a **USB cable**. Give the Pi a fixed address. Use 5 GHz if possible.
- **Far apart:** **Tailscale** on both the laptop and the Pi. It puts them in one private,
  encrypted network over the internet, each with an address that never changes. gRPC uses that
  address and nothing else changes. The Pi needs its own internet there (arena Wi-Fi or a 4G
  dongle). Never open a port on a router to reach the Pi.

If the internet drops, prototype10c already switches to the local model. Download it before a
run.

## Safety

These hold whatever the network does:

- **The rover brakes if it stops hearing from the laptop.** No laptop, no driving.
- **Every move has a number,** so a lost reply never drives the same move twice.
- **Obstacle avoidance stays on the Pi.** Nav2 checks the LiDAR many times a second, so a slow
  link never makes the rover drive blind.
- **When far away:** a STOP button on the game screen, lower speed, a closed-off arena, and if
  possible one person near the rover.

## Time

The rover takes about 7–10 s a leg; the network adds well under a second, even over Tailscale.
The mission clock charges a fixed `STEP_SECONDS` a cell, and waiting for the rover is free, the
same as the SPACE pause. So the real rover's speed doesn't change the sol, and replays still
match.

## How to build it

Each step ends with a check. Don't start the next one until it passes.

0. **Agree the basics.** Cell size, where cell (0, 0) is on the map, the rover facing grid north
   at the start, the reply codes, who builds which side. Talk to Abhishek and Ishu.
   *Done when* it is written here.
1. **Network.** Router or Pi Wi-Fi, fixed Pi address, laptop on it.
   *Done when* `ping` from the laptop works every time, under about 50 ms.
2. **Write the contract,** `proto/rover.proto`.
   *Done when* the team has read and agreed it. After this, change it only with both sides.
3. **A fake rover.** A pretend Pi server that follows the contract, waits two seconds and
   answers. The brain side can now be built without the robot.
   *Done when* it answers all four commands on the laptop.
4. **The brain side,** in a copy of prototype10c here. Fill `_await_rover`, add
   `ROVER_PAUSE = "grpc"` and the Pi's address, move the game's rover on `SHORT`, stop the run
   clearly on no reply. `SETTLE_SECONDS = 0` for real runs.
   *Done when* a full sol runs against the fake rover, and a forced `SHORT` makes her replan.
5. **The real bridge,** one piece at a time:
   `Status` (from `tf_pose.py`) → `Stop` (from `stop_cmd.py`) → `Move` one cell (from
   `return_home.py`) → `Move` a route → `WatchPosition` → the brake-on-silence.
   *Done when* each piece works on the rover before the next is added.
6. **Floor tests,** easy to hard: one cell N, E, S, W; an L-shaped route; along a wall; pushed
   off course by hand (`SHORT`); a box in the way (`BLOCKED`).
   *Done when* each passes five times in a row.
7. **Break it on purpose:** Wi-Fi off mid-drive, game closed, bridge restarted, urgent call,
   walking far from the router.
   *Done when* none of these leaves the rover driving on its own.
8. **Full missions:** one sol, then three in a row. Record each with its run directory and how
   often it was `SHORT`, `BLOCKED` or lost the link.
9. **Write it up** here and open a pull request.

## Later, for long distance

Not for the first build. In order of value:

1. **The brain on the rover.** The rover decides and drives by itself; the laptop becomes
   mission control. A dropped link then stops the talking, not the rover — the Mars idea, and
   10c's comms rules already fit it. Whether the Pi can carry it alongside SLAM and Nav2 is
   untested.
2. **A separate emergency stop** over LoRa radio, which reaches kilometres with no internet.
3. **Two ways online** on the rover, Wi-Fi and 4G, switching by itself.
4. **Zenoh** instead of a direct call, if links drop often: it is built for robots on poor
   networks and holds messages until the line comes back.
5. **Live video** over WebRTC, for watching only.

## Not decided yet

- Cell size and where cell (0, 0) sits on the room map.
- Whether a leg goes to Nav2 as one goal or one goal per cell.
- Exactly when a stop counts as `SHORT` rather than `DONE`.
- Which prototype the link joins (prototype 12 forks after 11).
