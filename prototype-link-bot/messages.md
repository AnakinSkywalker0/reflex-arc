# Messages — what the laptop sends and what the rover sends back

Every message that crosses the link, in plain words, with examples. The network and why we use gRPC
are in [`hotspot-grpc.md`](hotspot-grpc.md); the exact `.proto` is there too. This file is the
"what does each side say" view of the same contract.

**Status: proposed by Krish, not yet agreed with the team.**

## The short version

| the laptop sends | the rover sends back |
|---|---|
| `Reset` — "this spot is the start" | OK |
| `Move` — one move: turn or go forward | progress while moving, then **where it really ended up** |
| `Stop` — "stop now" | stopped |
| `Status` — "how are you?" | where it is, busy or not, LiDAR OK |

The laptop never sends wheel speeds, and the rover never decides where to go.

## Units and directions

The same on both sides, always:

- **Distance:** metres. **Angles:** degrees.
- **x** = forward from the start spot. **y** = to the left of the start spot.
- **heading** = how far the rover has turned from its start direction. **Anticlockwise is +**, so a
  left turn is `+90`, a right turn is `-90`.
- The start spot is (0, 0) facing 0°, set by `Reset`.

---

## 1. `Reset` — set the start

Sent **once, before a run**, with the rover on its start spot, facing grid north.

**Laptop sends:** nothing else.

**Rover does:** takes a LiDAR scan, saves it as the reference, sets its position to (0, 0, 0°).

**Rover sends back:**

```
ok:   true
note: "reference saved, 497 readings"
```

If the LiDAR isn't working: `ok: false`, `note: "no scan from LiDAR"`. Don't start the run.

---

## 2. `Move` — do one move

The main message. One per step of the route.

### Laptop sends

```
move_id:   17            # a new number every move, never reused
turn_deg:  -90           # OR
forward_m: 0.40          # exactly one of these two
```

- **`move_id`** is what keeps a move from ever being driven twice (see "Repeats" below).
- **`turn_deg`**: + is left, - is right. The rover turns on the spot.
- **`forward_m`**: how far to drive straight. Usually one cell.

### Rover sends back, while moving

A few times a second, until the move ends:

```
progress:  x 0.21 m, y 0.01 m, heading 1.2°
```

```
log:       "turn: 62° of 90°"
```

The laptop can show these on screen. It doesn't need them to run the mission.

### Rover sends back, at the end (always the last message)

```
move_id:   17
result:    DONE
pose:      x 0.40 m, y 0.03 m, heading -89.1°
fit:       source "map", error 0.02 m, matched 93 %
scan:      (optional) the last LiDAR scan
```

| field | meaning |
|---|---|
| `move_id` | which move this answers |
| `result` | how it went (table below) |
| `pose` | **where the rover really is now**, measured by the LiDAR against the start reference |
| `fit.source` | `map` = measured against the reference (trust it). `scan` = the reference check failed, this is the step-by-step estimate (less sure) |
| `fit.error` | average gap between the scan and the reference. Small is good |
| `fit.matched` | share of LiDAR dots that lined up, 0–100 % |
| `scan` | the last scan, only if asked for. For the screen and the run's tape |
| `note` | why, in words, when something went wrong: "busy with move 20", "LiDAR lost" |

### The results

| result | what it means | what the laptop does |
|---|---|---|
| `DONE` | reached the target, within the limit | move the sim rover to `pose`, carry on |
| `SHORT` | stopped early or off target; `pose` says where | move the sim rover to `pose`, re-plan |
| `FAILED` | couldn't do it or couldn't measure it (LiDAR lost, timed out, bad fit) | stop the run and show why |
| `LINK_LOST` | the rover stopped itself because the laptop went silent | after reconnecting, move the sim rover to `pose`, re-plan |

In every case the laptop **trusts `pose`, not the simulation**.

---

## 3. `Stop` — stop now

**Laptop sends:** nothing else. Wired to the STOP button on the game screen.

**Rover does:** stops the motors at once. If a move was running, it ends as `SHORT` with the real
position.

**Rover sends back:** `ok: true, note: "stopped"`

---

## 4. `Status` — how are you?

Safe to call any time, for example before a run or after a reconnect.

**Laptop sends:** nothing else.

**Rover sends back:**

```
pose:       x 1.20 m, y 0.40 m, heading 90.0°
busy:       false          # true while a move is running
lidar_ok:   true
reference:  true           # a start reference is saved
```

---

## Examples

### A normal move

```
laptop → rover   Move   move_id 17, forward_m 0.40
rover → laptop   progress  x 0.10, y 0.00, heading 0.3°
rover → laptop   progress  x 0.25, y 0.01, heading 0.8°
rover → laptop   log       "forward: 0.38 of 0.40 m"
rover → laptop   final     17, DONE, x 0.40, y 0.02, heading 1.1°, map 0.02 m 94 %
```

### A turn that came up short

The rover was told to turn right 90°, the tyres slipped, and it stopped at 60°:

```
laptop → rover   Move   move_id 18, turn_deg -90
rover → laptop   log       "turn: 60° of 90°, stuck"
rover → laptop   final     18, SHORT, x 0.40, y 0.02, heading -60.4°, map 0.02 m 91 %
```

The laptop sees the heading is 30° off. Headings are always corrected, so it sends a fix:

```
laptop → rover   Move   move_id 19, turn_deg -29.6
rover → laptop   final     19, DONE, x 0.40, y 0.02, heading -89.6°, map 0.02 m 92 %
```

### The hotspot drops in the middle of a move

```
laptop → rover   Move   move_id 20, forward_m 0.40
rover → laptop   progress  x 0.15 ...
                 ---- hotspot drops ----
rover            no word from the laptop for 2 s → stops the motors
                 saves: 20, LINK_LOST, x 0.22, y 0.01, heading 0.5°
                 ---- hotspot comes back ----
laptop → rover   Move   move_id 20, forward_m 0.40      (the same number again)
rover → laptop   final     20, LINK_LOST, x 0.22, y 0.01, heading 0.5°   (saved result, no driving)
```

The laptop moves the sim rover to (0.22, 0.01) and re-plans from there.

### Repeats

If the laptop sends a `move_id` the rover has already finished, the rover **sends back the saved
result and does not move**. That is what makes retrying after a drop safe.

### Busy

If a `Move` arrives while another move is running, the rover refuses it:

```
final:  move_id 21, FAILED, note "busy with move 20"
```

---

## The LiDAR scan, when it is sent

Only the **last scan of a move**, and only if asked for. About 1–2 KB:

```
time:         1697270400.123
angle_start:  0.0            # radians
angle_step:   0.01247        # radians, 2π / 504
range_mm:     [1820, 1810, 0, 1795, ...]    # 504 numbers, 0 = no reading
```

The LD19 counts angles **clockwise**; the rover flips them to anticlockwise before sending, so the
scan uses the same directions as everything else. All scans (10 a second) are saved to a file on
the rover and fetched after the run, not sent live.

## Time limits

| what | limit | then |
|---|---|---|
| one `Move` | 30 s | laptop treats it as a dropped link and retries with the same `move_id` |
| retries | 3 | laptop stops the run clearly |
| silence the rover accepts | 2 s | rover stops itself, result `LINK_LOST` |

Starting values, to be tuned once the hotspot is measured.

## Not decided yet

- How close counts as `DONE` rather than `SHORT` (for example within 5 cm and 3°).
- Whether the laptop sends single steps, or short straight runs like `forward_m 1.20`.
- Whether the last scan is sent after every move or only when asked for.
- Whether `Stop` during a move ends it as `SHORT` or as its own result.
