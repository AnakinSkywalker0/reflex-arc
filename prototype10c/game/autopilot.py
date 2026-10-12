"""The mission clock: who opens and closes a sol when nobody is on shift.

    .venv/bin/python game/main.py --auto --sols 3

Off, which is how 10b ships, the operator does both: talks to the planner to start the
sol, presses Q to end it, talks again at nightfall and presses N. On, this does each of
those itself, through the same doors -- `Conversation.send`, `World.day_over` and
`main.nightfall` -- so an unattended sol is the attended one with the operator's lines
written by the clock. The tape labels them `auto` rather than `you`, so a sol nobody
coached can never be mistaken for one somebody did, or the other way round.

A sol runs in three phases:

    day     open a turn; when it ends, open another, until she calls `end`, the clock
            runs out, or AUTO_TURNS turns have been opened. Then the day is over.
    dusk    one turn asking for tomorrow's note. `remember` is a look, so it is still
            offered with the sol gone.
    night   hold SETTLE_SECONDS so the end of the sol is legible, then roll over.

A fresh conversation every morning and the note crossing the night is what the attended
game already does. This adds no store of its own.

**`end` closes the sol.** With an operator, `end` hands back and the sol waits for them.
With nobody there, waiting is a sol lost, and re-asking until the steps run out would
overrule the one judgement the prompt leaves her -- which work is worth the trip. So the
prompt says so (`prompts._sol_para`) and her `end` is taken at its word.

Except when a cap had stopped the turn: no drives left, or no looks. The refusal sends
her to `end`, and she goes -- the first unattended run lost 116 steps that way, parked
beside the high-priority objective it had driven to. That `end` is the cap's, not hers,
so it gets a fresh turn with both allowances back rather than the night, and the
refusal says so (`Conversation._way_out`) instead of telling her to hand back.

**A request that never reached the model is not a turn.** It is asked again after
AUTO_RETRY_SECONDS, for as long as it takes. Counting it would play out every remaining
sol in seconds the first time the connection dropped overnight.

**Taking over and handing back.** C in the app, or the setting, switches mid-sol and
lands at once. Off, this stops opening turns and the operator has the sol. On again,
it picks up from wherever the operator left it: an `end` only closes the sol in a turn
the clock opened, so an operator's turn that ended does not shut the day under them.
The prompt is rebuilt for whoever is on shift and she is told at her next turn
(`Conversation.send`), because `end` means something different to each of them.

**In a replay the tape owns the sol boundaries.** While it holds more calls for today
the clock keeps opening turns, so a sol the live run ran on longer -- an operator's
turn after her `end`, say -- is not closed early here.

No pygame in here, so the tests can drive the whole thing.
"""

import time

import settings as S


def morning(world):
    """The turn that opens the sol, where the operator would have spoken first."""
    job = ("Carry out your orders from mission control." if world.notes.orders else
           "You have no orders, so explore: drive into ground you have not seen, find "
           "the objectives and do the ones worth the steps, and work out which rock "
           "formation is the largest.")
    note = " Your note from last night is in your view." if world.notes.memory else ""
    stuck = (f" The rover spent the night stranded, so the battery was not recharged: "
             f"{world.battery} of {S.BATTERY}." if world.stranded else "")
    return (f"Sol {world.day} has begun, and nobody is on shift until the mission is "
            f"over.{stuck}{note} {job} Be back beside the pad before you call end; "
            f"end closes the sol.")


def carry_on(world):
    """A turn ended without her choosing to close the sol -- a cap, or a reply with no
    call in it."""
    return (f"Nobody is on shift to answer, so the sol goes on with a new turn and your "
            f"drives back: {world.time_left:.0f} seconds of the sol and {world.battery} "
            f"steps of battery are left. Carry on, or call end if nothing left is worth "
            f"them; that closes the sol.")


def handover(on):
    """What she is told, with her next turn, when whoever is on shift changes."""
    if on:
        return ("The operator has handed the rover back to the mission clock. Nobody is "
                "on shift from here: your end now closes the sol.")
    return ("The operator has taken over. From here your end hands back to them and "
            "does not close the sol.")


# The facts go in the report from the world's record (`report.py`), so the last note is
# asked for judgement only. Asking her to restate facts is how a wrong one got in.
REPORT = ("Mission control's report is written from the record: what was finished, what "
          "was mapped, where the rover is. Add what only you can say with remember -- what "
          "is still worth doing out there and why it was left. Then call end.")


def dusk(world):
    """The day is over. The note is the only thing she can hand tomorrow -- and if the
    rover is out on the plain, the note is where it has to say so."""
    if world.lost:
        return (f"Sol {world.day} is over, and the rover is lost: the battery holds less "
                f"than the trip back to the pad needs, and nothing else recharges it. The "
                f"mission ends here. {REPORT}")
    out = ("" if world.docked else
           f" The rover is not beside the pad, so it is stranded tonight: no recharge, "
           f"and tomorrow it wakes where it stands on {world.battery} steps of battery.")
    if S.MISSION_SOLS and world.day >= S.MISSION_SOLS:
        return (f"Sol {world.day} is over, and it was the last sol of the mission. "
                f"{REPORT}")
    return (f"Sol {world.day} is over.{out} Before the night, rewrite the note that "
            f"survives with remember: what you left and why, and what to do first "
            f"tomorrow. What was finished and what was mapped carry themselves. Then "
            f"call end.")


class Autopilot:
    """One sol's worth of clock. `main.py` makes a new one every morning."""

    def __init__(self):
        self.phase = "day"
        self.turns = 0          # turns opened this sol, against AUTO_TURNS
        self.mark = 0           # len(conv.calls) when the latest turn opened
        self.failures = 0       # conv.failures already answered for
        self.retry_at = None    # when to ask again after a request that got no answer
        self.night_at = None

    def tick(self, conv, world, now=None):
        """One frame. Acts on `conv` and `world` once a turn is over, and returns
        "night" when the sol is finished and the roll-over is the caller's to do."""
        now = time.monotonic() if now is None else now
        # Mid-turn, or held while the rover is still driving: nothing is over yet.
        if conv.busy or conv.waiting or not conv.ready():
            return None
        if conv.failures > self.failures:
            self.failures = conv.failures
            self.retry_at = now + S.AUTO_RETRY_SECONDS
            conv.write("auto", f"the model did not answer -- asking again in "
                               f"{S.AUTO_RETRY_SECONDS:g}s")
            return None
        if self.retry_at is not None:
            if now >= self.retry_at:
                self.retry_at = None
                conv.retry()
            return None
        if conv.holds_sol:
            self._open(conv, carry_on(world))
            return None
        if self.phase == "night":
            return "night" if now >= self.night_at else None
        if self.phase == "dusk":
            self.phase, self.night_at = "night", now + S.SETTLE_SECONDS
            return None

        why = self._over(conv, world)
        if why is None:
            self._open(conv, morning(world) if conv.turn_by is None else carry_on(world))
            return None
        world.day_over = True
        world.record("sol_closed", by="autopilot", why=why, turns=self.turns)
        self.phase = "dusk"
        self._open(conv, dusk(world))
        return None

    def _over(self, conv, world):
        """Why the day is over, or None if it is not."""
        if world.day_over:
            return "the day was over"
        if (conv.turn_by == "auto" and len(conv.calls) > self.mark
                and conv.calls[-1].name == "end" and not conv.capped):
            return "she called end"
        if self.turns >= S.AUTO_TURNS:
            return f"{self.turns} turns opened"
        return None

    def resume(self, conv):
        """Handed back mid-sol. A failure while the operator had it was theirs to see."""
        self.failures, self.retry_at = conv.failures, None

    def _open(self, conv, text):
        if self.phase == "day":
            self.turns += 1
        self.mark = len(conv.calls)
        conv.send(text, who="auto")
