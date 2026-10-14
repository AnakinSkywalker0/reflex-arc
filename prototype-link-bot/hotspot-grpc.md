# The link — gRPC over a phone hotspot

How the laptop (the brain) and the rover (the bot) talk to each other: what network they use, what
they send, and what keeps the rover safe when the network fails.

**Status: proposed by Krish, not yet agreed with the team. Nothing here is built yet.**

This file is for the **dumb rover with no ROS**: the laptop decides, the Pi only executes one move at
a time and reports where it really ended up. It replaces the Nav2 parts of
[`grpc-link.md`](grpc-link.md).

## The idea in one picture

```
LAPTOP (the brain)                                       PI 4/5 (the bot), plain Python
Gemma decides → A* plans → "turn right 90°"
gRPC client  ────────── phone hotspot ──────────────►   gRPC server
                                                          ├─ does the move, LiDAR-checked, 10× a second
                                                          ├─ stops, measures the real position (scan-to-map)
             ◄────────── result + logs ─────────────────┘
moves the sim rover to the real position → A* plans again
```

Three rules hold the whole way through:

1. **The laptop sends one move at a time.** It never drives the wheels directly.
2. **The fast work stays on the Pi.** Turning and driving straight are checked against the LiDAR 10
   times a second on the Pi. Nothing in that loop goes over the network.
3. **The Pi always tells the truth.** After each move it sends where the rover *really* is, and the
   game re-plans from there. Errors are reported, not hidden.

## Why a phone hotspot

The college Wi-Fi has **client isolation**: devices on it cannot talk to each other, so the laptop
cannot reach the Pi on it. Changing the protocol does not fix that; only changing the network does.

A phone hotspot is the simplest network we have that works today:

- It already works with the laptop and the Pi.
- It also gives the laptop internet for the cloud model.
- Speed is not a problem. One move takes several seconds and needs one message. The hotspot adds
  roughly 5–30 ms (a guess until we measure it), which is nothing next to that.

## Why gRPC

gRPC lets the laptop call a function on the Pi, like `Move(turn 90°)`, and get the answer back. It
gives us, ready-made, the things we would otherwise build by hand:

- **One contract.** A single `rover.proto` file lists every message. Both sides are built from it,
  so they cannot disagree about the format.
- **Live updates.** One `Move` call can stream progress and log lines while the rover moves, then
  the final result.
- **Notices a dead link.** Keepalive pings find a dropped connection within seconds — but only if
  they are switched on and set short on both sides. The defaults are off.
- **Time limits and cancel.** Every call has a deadline, and cancelling on the laptop reaches the Pi
  at once.

Considered and not chosen:

| option | why not |
|---|---|
| Plain HTTP (Flask, like the old `rover_bridge`) | Works, but live updates, cancel and dead-link detection are all hand-built |
| WebSocket | Same: message format and reconnecting are hand-built |
| MQTT | Needs a broker running somewhere — one more thing to fail |

## Setting up the hotspot

**On the phone:**

- Turn off the hotspot's **auto-off timer** (set it to never).
- Use **5 GHz** if both the phone and the Pi support it.
- During runs: phone **charging**, on **Do Not Disturb**, **close to the play area**.
- Some phones also block devices from seeing each other. Test any new phone before relying on it.

**Give the Pi a name that never changes.** Android usually gives the Pi a new address each time the
hotspot starts. Install **Tailscale** on the laptop and on the Pi, signed into the same account. The
Pi then keeps the same name and address on any network, and the laptop always points gRPC at that.
Turn off key expiry for the Pi in the Tailscale admin page, or it can drop off the network later.

**On the laptop:** pause big downloads and updates during runs. They share the hotspot with the
rover.

**Check it works:**

```bash
ping <pi-tailscale-name>        # for 5 minutes
```

*Done when* every reply comes back, with no gaps of more than a second.

## The messages

The draft contract, `proto/rover.proto`. Change it only with both sides agreeing.

| call | laptop sends | Pi sends back |
|---|---|---|
| `Move` | a move number + one move: `TURN 90°` or `FORWARD 0.40 m` | progress while moving, then the result |
| `Stop` | nothing | "stopped" |
| `Status` | nothing | position, busy or idle, LiDAR OK, reference saved |
| `Reset` | nothing | saves the start scan; position becomes (0, 0, 0°) |

```proto
syntax = "proto3";
package rover;

service Rover {
  rpc Move   (MoveRequest)  returns (stream MoveUpdate);  // progress..., then one final result
  rpc Stop   (Empty)        returns (Ack);
  rpc Status (Empty)        returns (StatusReply);
  rpc Reset  (Empty)        returns (Ack);
}

message Empty {}
message Ack { bool ok = 1; string note = 2; }

message MoveRequest {
  uint64 move_id = 1;               // never reused; a repeat returns the saved result
  oneof move {
    float turn_deg    = 2;          // + = left (anticlockwise), - = right
    float forward_m   = 3;          // + = forward
  }
}

message Pose {
  float x_m         = 1;            // forward from the start spot
  float y_m         = 2;            // left of the start spot
  float heading_deg = 3;            // anticlockwise from the start heading
}

message Fit {
  string source     = 1;            // "map" (scan-to-map) or "scan" (scan-to-scan, less sure)
  float  error_m    = 2;            // average gap between scan and reference; small = good
  float  matched    = 3;            // share of LiDAR dots that lined up, 0..1
}

enum Result {
  RESULT_UNSET = 0;
  DONE      = 1;                    // reached it
  SHORT     = 2;                    // stopped early; pose says where
  FAILED    = 3;                    // could not measure, LiDAR lost, timed out
  LINK_LOST = 4;                    // braked because the laptop went silent
}

message MoveUpdate {
  oneof kind {
    Pose   progress = 1;            // while moving, a few times a second
    string log      = 2;            // a log line from the Pi
    Final  final    = 3;            // the last message of every Move
  }
}

message Final {
  uint64 move_id = 1;
  Result result  = 2;
  Pose   pose    = 3;
  Fit    fit     = 4;
  Scan   scan    = 5;               // optional: the last scan, for the screen and the tape
}

message Scan {
  double time        = 1;
  float  angle_start = 2;           // radians
  float  angle_step  = 3;           // radians
  repeated uint32 range_mm = 4;     // 0 = no reading
}

message StatusReply {
  Pose   pose        = 1;
  bool   busy        = 2;
  bool   lidar_ok    = 3;
  bool   reference   = 4;           // start scan or map is loaded
}
```

**Units and directions, the same on both sides:** metres and degrees in messages. x is forward from
the start spot, y is to the left, heading turns anticlockwise. The LD19 itself counts angles
**clockwise**, so the Pi flips them before anything else uses them.

**What a scan is.** The LD19 sends 47-byte packets of 12 readings (distance in mm, plus strength),
about 450–500 readings a turn, 10 turns a second. The Pi collects one turn into fixed slots (for
example 504) so every scan is the same size. Only the **last** scan of a move is sent, and only if
asked for (about 1–2 KB). All scans are saved to a file on the Pi and fetched after the run.

## Safety

These hold whatever the hotspot does:

- **The Pi stops the rover by itself if the laptop goes silent.** If the `Move` call breaks or no
  keepalive arrives for 2 s, the Pi stops the motors and keeps the result as `LINK_LOST`.
- **A move is never driven twice.** Each move has a number. If the laptop resends a number after a
  reconnect, the Pi sends back the saved result and does not move.
- **One laptop at a time.** If a second caller sends `Move` while a move is running, it is refused.
- **The motor watchdog stays on.** The motors stop if no command arrives for 0.5 s, so a crashed Pi
  program cannot leave them running.
- **A STOP button on the game screen** that calls `Stop()`.
- **Nothing on the rover avoids obstacles.** The floor must be clear, and someone stays beside the
  rover during runs.

## Settings to start with

Starting points, to be tuned once we measure the hotspot:

| setting | value | where |
|---|---|---|
| keepalive ping | every 1 s | both sides |
| keepalive timeout | 2 s | both sides |
| `Move` deadline | 30 s | laptop |
| retries after a drop | 3, with the same move number | laptop |
| motor watchdog | 0.5 s | Pi |

## How to build it

Each step ends with a check. Don't start the next one until it passes.

1. **Network.** Hotspot set up as above, Tailscale on both.
   *Done when* `ping` works for 5 minutes with no gaps.
2. **The contract.** Write `proto/rover.proto` from the draft above.
   *Done when* the team has read and agreed it.
3. **A fake rover.** A pretend Pi server that follows the contract: waits 2 seconds, then answers.
   It can also fake `SHORT` and `LINK_LOST` on purpose.
   *Done when* it answers all four calls, on the laptop alone.
4. **The laptop side.** Fill in `_await_rover` in the game: send the move, wait for the result, move
   the sim rover to the real position, stop clearly if there is no reply.
   *Done when* a full sol runs against the fake rover, and a forced `SHORT` makes the game re-plan.
5. **The fake rover on the Pi.** Same fake server, now on the Pi, over the hotspot.
   *Done when* a full sol runs over the hotspot.
6. **The real Pi side,** one piece at a time: `Status` → `Stop` → `Reset` → `Move` with one turn →
   `Move` forward → the stop-on-silence.
   *Done when* each piece works on the rover before the next is added.
7. **Break it on purpose.** Hotspot off mid-move, game closed mid-move, Pi program restarted, phone
   carried far away.
   *Done when* none of these leaves the rover moving, and each comes back as `LINK_LOST` or
   `FAILED`.
8. **Full missions:** one sol, then three in a row. Note how often each move came back `SHORT`,
   `FAILED` or `LINK_LOST`.

## When to move off the hotspot

The code does not change for any of these — only the Pi's address does, and with Tailscale not even
that.

| situation | network |
|---|---|
| building and testing | phone hotspot |
| demo or judged run | the Pi's own Wi-Fi (laptop gets internet from the phone over USB), or a small travel router |
| bench testing on a desk | Ethernet cable, laptop to Pi |
| on college Wi-Fi with no phone | Tailscale over college Wi-Fi — gets around the isolation, but may be slow if relayed; test first |

One rule for deciding: if `LINK_LOST` shows up often during runs, it is time to move off the hotspot.

## Not decided yet

- gRPC itself, until the team agrees it.
- Whether the laptop sends one step at a time, or short legs with no turns inside them.
- The exact keepalive and timeout values, until the hotspot is measured.
- Whose Tailscale account the laptop and Pi use.
- Whether the last scan is sent after every move, or only when asked for.
- Which phone is the team's hotspot for runs and demos.
