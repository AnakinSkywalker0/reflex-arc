# Long distance — when the brain and the bot are far apart

The [gRPC link](grpc-link.md) is built for one room: laptop and rover on the same router. This
file is about running them on **different networks** — another building, or another city — and
the ways to do it, from what we can use first to what comes later.

**Status: none of this is built or tested.** It is not part of the first build. Same room comes
first; long distance starts once the gRPC link passes its floor tests.

There are two ways to go far:

1. **Stretch the link.** Keep the same gRPC link and carry it across the internet. Tailscale is
   the first choice. The rover still needs the laptop to drive.
2. **Change who decides.** Put the brain on the rover, so a dropped link stops the talking, not
   the driving. That is the Mars idea, and the bigger step.

## First, what "far" means — not decided

Each case needs a different setup, and we haven't said which one we are planning for.

| case | example | what it needs |
|---|---|---|
| Same building, another room | laptop in the lab, rover down the hall | a stronger router or a second access point may be enough |
| Another building on campus | judges in a hall, rover in the lab | Tailscale, with the rover on campus or arena Wi-Fi |
| Another city | demo online, rover at home | Tailscale, the rover on its own 4G, and someone beside it |

## Stretching the link: Tailscale

Tailscale joins the laptop and the Pi into one private, encrypted network over the internet. Each
device gets an address that never changes, wherever it is. gRPC uses that address and **nothing
else in the code changes.** No router port has to be opened, and one never should be.

**Setting it up:**

- Install Tailscale on the **laptop** and on the **Pi itself**, not inside the Docker container.
  The container uses the Pi's own network, so the gRPC server inside it can be reached on the
  Pi's Tailscale address.
- Sign both into **the same Tailscale account.** Decide whose account it is, so it isn't one
  person's laptop login the whole team depends on.
- **Turn off key expiry for the Pi.** Tailscale makes devices sign in again after a while (180
  days for a new account), and an expired device silently drops off the network. It can be turned
  off per device on the Machines page of the admin console
  ([Tailscale docs](https://tailscale.com/kb/1028/key-expiry)). Otherwise the Pi could vanish the
  week of a demo.
- Point the brain at the Pi's Tailscale name or address instead of its router address.

**Direct or relayed.** Tailscale tries to connect the two devices directly. When a network blocks
that, it passes the traffic through its own relay servers, which is slower. `tailscale ping`
shows which one you got. "Well under a second a leg" is a guess until it's measured on the real
networks.

**The brake timer.** In one room, the rover brakes after 1–2 s of silence. Over 4G or arena
Wi-Fi, short gaps are normal, so the same timer will stop the rover often and the model will see
a lot of `LINK_LOST`. Whether far-away runs use a longer timer, or accept more stops for safety,
is undecided.

**How to test it** (not yet in the build steps):

1. Pi and laptop on **different networks** (for example, the Pi on a phone hotspot, the laptop on
   campus Wi-Fi). `tailscale ping` the Pi: note direct or relayed, and the time.
2. Run the fake rover over Tailscale, then one full sol.
3. On the real rover: one cell, then a route, then pull the Pi's internet mid-drive. *Done when*
   it brakes every time and reports `LINK_LOST`.

### Other ways to stretch the link

| method | how | verdict |
|---|---|---|
| **Tailscale** | ready-made private network, no setup on routers | ✅ first choice |
| ZeroTier | the same idea from another company | fine; no reason to pick it over Tailscale |
| Plain WireGuard | the encryption Tailscale is built on, set up by hand | needs our own server with a public address |
| Opening a router port | expose the Pi to the internet directly | ❌ never — anyone could drive the rover |

## The rover's own internet

Far away, the Pi needs its own internet; the laptop can't lend it one.

- **Arena or campus Wi-Fi.** Free, but it may block devices from talking, sign-in pages break it,
  and it drops when the rover moves away.
- **A 4G dongle or phone on the rover.** Works anywhere with signal. It draws power from the
  rover's battery and uses mobile data; neither has been measured.
- **Both, switching by itself.** See "Later" below.

The laptop still needs internet for the cloud model. If it drops, prototype10c switches to the
local model, so download that before a run.

## Safety, far away

The [gRPC link's safety rules](grpc-link.md#safety) all still hold. On top of them:

- **A person beside the rover, who can pick it up or switch it off.** For a robot driven from
  another place this should be required, not "if possible". Not yet agreed.
- **Lower speed** (`rover speed` set lower) and **a closed-off area** for it to drive in.
- **The STOP button on the game screen.** It only works while the link works, which is why a
  separate emergency stop is high on the list below.

## The fake Mars delay

The work plan asks for the link to keep working with an **artificial delay** on it, to feel like
Mars. Long distance is where that belongs. A setting on the Pi that holds every reply for a few
seconds would let us test it in one room. Not designed yet.

## Later

Not for the first build. In order of value:

1. **The brain on the rover.** The rover decides and drives by itself; the laptop becomes mission
   control. A dropped link then only stops the talking — the Mars idea, and 10c's comms rules
   already fit it. The cloud model needs internet on the rover, and the local fallback model
   (9.6 GB) is likely too big for the Pi beside SLAM and Nav2. Untested.
2. **A separate emergency stop over LoRa radio,** which reaches kilometres with no internet. It
   still works when Wi-Fi, 4G and Tailscale have all failed.
3. **Two ways online** on the rover, Wi-Fi and 4G, switching by itself when one drops.
4. **Zenoh** in place of a direct call, if links drop often. It is made for robots on poor
   networks and holds messages until the line comes back.
5. **Live video over WebRTC,** for watching only, never for driving.

**When to move to these** is not decided. One idea: if `LINK_LOST` happens more than a set number
of times in a sol over Tailscale, move to item 1 or 4.

## Not decided yet

- Which "far" case we are actually planning for.
- Whose Tailscale account the Pi and laptop sign into.
- The brake timer over long distance: the same 1–2 s, or longer.
- Whether a person beside the rover is required.
- The rover's internet: arena Wi-Fi, 4G, or both — and the 4G dongle's power and data.
- The design of the artificial delay.
- What would make us move to the "Later" items.
