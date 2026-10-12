"""The mission clock, and the line to mission control.

    .venv/bin/python game/main.py --sols 3

The clock runs every sol. It opens the sol with a turn of its own, closes it, asks for
tomorrow's note and rolls the night over, through the same doors an operator would --
`Conversation.send`, `World.day_over` and `main.nightfall`. Its lines are `auto` on the
tape, never `you`, so a sol nobody coached can never be mistaken for one somebody did.

A sol runs in three phases:

    day     open a turn; when it ends, open another, until she calls `end`, the clock
            runs out, or AUTO_TURNS turns have been opened. Then the day is over.
    dusk    one turn asking for tomorrow's note -- and, beside the pad with someone at
            the desk, her report. `remember` is a look, so it is still offered.
    night   the line, if there is one; then SETTLE_SECONDS; then the roll-over.

**The line.** COMMS says whether anyone is at the desk. With it on, a line opens

    at night, after she has reported from beside the pad;
    when the desk calls -- TAB beside the pad, U (urgent) from anywhere, by day;
    when she calls -- `radio` beside the pad, `sos` from anywhere.

While a line is open the clock opens no turns. The desk's messages open them, and her
`end` hands back to the desk, because `_over` only takes an `end` as hers in a turn the
clock opened. A call from the desk stops her after the call in hand (`Conversation.cut`).
The line closes on N, or after COMMS_WAIT seconds in which nothing was typed and nothing
was being said. By day the clock then has the sol back and tells her so; at night the
next sol opens. A replay never opens one: nobody on a tape can be talked to.

**`end` closes the sol.** Waiting is a sol lost, and re-asking until the battery runs out
would overrule the one judgement the prompt leaves her -- which work is worth the trip.
So the prompt says so (`prompts._sol_para`) and her `end` is taken at its word.

Except when a cap had stopped the turn: no drives left, or no looks. The refusal sends
her to `end`, and she goes -- the first unattended run lost 116 steps that way, parked
beside the high-priority objective it had driven to. That `end` is the cap's, not hers,
so it gets a fresh turn with both allowances back rather than the night, and the
refusal says so (`Conversation._way_out`).

**A request that never reached the model is not a turn.** It is asked again after
AUTO_RETRY_SECONDS, for as long as it takes. Counting it would play out every remaining
sol in seconds the first time the connection dropped overnight.

**In a replay the tape owns the sol boundaries.** While it holds more calls for today
the clock keeps opening turns, so a sol the live run ran on longer -- a talk on the
line after her `end`, say -- is not closed early here.

No pygame in here, so the tests can drive the whole thing.
"""

import time

import settings as S
import skills


def morning(world):
    """The turn that opens the sol."""
    job = ("Carry out your orders from mission control." if world.notes.orders else
           "You have no orders, so explore: drive into ground you have not seen, find "
           "the objectives and do the ones worth the steps, and work out which rock "
           "formation is the largest.")
    note = " Your note from last night is in your view." if world.notes.memory else ""
    stuck = (f" The rover spent the night stranded, so the battery was not recharged: "
             f"{world.battery} of {S.BATTERY}." if world.stranded else "")
    return (f"Sol {world.day} has begun.{stuck}{note} {job} Be back beside the pad "
            f"before you call end; end closes the sol.")


def carry_on(world, after_line=False):
    """A turn ended without her choosing to close the sol -- a cap, a reply with no
    call in it, or a line to mission control that has closed."""
    back = ("The line to mission control is closed, and the sol is yours again. "
            if after_line else "")
    return (f"{back}The sol goes on with a new turn and your drives back: "
            f"{world.time_left:.0f} seconds of the sol and {world.battery} steps of "
            f"battery are left. Carry on, or call end if nothing left is worth them; "
            f"that closes the sol.")


def desk(on):
    """What she is told, with her next turn, when someone sits down at the desk or
    leaves it."""
    if on:
        return ("Mission control is at the desk now. Beside the pad you can radio them, "
                "and away from it sos gets through.")
    return ("Mission control has left the desk. Nobody will answer and nothing you send "
            "reaches them: work from your orders and your own judgement.")


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
    line = S.COMMS and world.docked
    told = (" The rover is beside the pad and mission control is at the desk, so the "
            "line is open tonight: tell them in a few lines what only you can say -- "
            "what is still worth doing out there and why it was left. The record "
            "already has what was finished and mapped." if line else "")
    out = ("" if world.docked else
           f" The rover is not beside the pad, so it is stranded tonight: no recharge, "
           f"and tomorrow it wakes where it stands on {world.battery} steps of battery."
           + (" Away from the pad there is no line tonight; only sos gets through."
              if S.COMMS else ""))
    if S.MISSION_SOLS and world.day >= S.MISSION_SOLS:
        return (f"Sol {world.day} is over, and it was the last sol of the mission.{told} "
                f"{REPORT}")
    return (f"Sol {world.day} is over.{out}{told} Before the night, rewrite the note that "
            f"survives with remember: what you left and why, and what to do first "
            f"tomorrow. What was finished and what was mapped carry themselves. Then "
            f"call end" + ("; they may answer." if line else "."))


# The pane's line when one opens, by who opened it and why.
OPENED = {"night": "the line is open for the night -- TAB to talk, N for the next sol",
          "urgent": "URGENT -- she stops after the call in hand; say what she must do",
          "pad": "the line is open -- she stops after the call in hand",
          "radio": "she is calling from the pad -- TAB to answer, N to let her carry on",
          "sos": "SOS from the rover -- TAB to answer, N to let her carry on"}


class Autopilot:
    """One sol's worth of clock, and its line. `main.py` makes a new one every morning.

    `live=False` is a replay: the clock runs, and no line ever opens.
    """

    def __init__(self, live=True):
        self.live = live
        self.phase = "day"
        self.turns = 0          # turns opened this sol, against AUTO_TURNS
        self.mark = 0           # len(conv.calls) when the latest turn or line opened
        self.failures = 0       # conv.failures already answered for
        self.retry_at = None    # when to ask again after a request that got no answer
        self.night_at = None
        self.line = None        # why the line is open, or None: a key of OPENED
        self.spoken = False     # the desk has said something on this line
        self.quiet_since = None # when the line last went quiet, against COMMS_WAIT
        self.closing = False    # N was pressed: close as soon as she has finished
        self.after_line = False # the next turn the clock opens says the line closed

    def tick(self, conv, world, now=None, typing=False):
        """One frame. Acts on `conv` and `world` once a turn is over, and returns
        "night" when the sol is finished and the roll-over is the caller's to do.
        `typing`: the desk is writing, so nothing is said over it and the line waits."""
        now = time.monotonic() if now is None else now
        # Mid-turn, or held while the rover is still driving: nothing is over yet.
        if typing or conv.busy or conv.waiting or not conv.ready():
            self.quiet_since = None
            return None
        if self.line:
            return self._on_line(conv, world, now)
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
        called = self._called(conv)
        if called and self.phase == "day":
            self.open_line(conv, called, now)
            return None
        if self.phase == "night":
            return "night" if now >= self.night_at else None
        if self.phase == "dusk":
            self.phase, self.night_at = "night", now + S.SETTLE_SECONDS
            if world.docked or called == "sos":
                self.open_line(conv, "night" if world.docked else "sos", now)
            return None

        why = self._over(conv, world)
        if why is None:
            text = (morning(world) if conv.turn_by is None else
                    carry_on(world, self.after_line))
            self.after_line = False
            self._open(conv, text)
            return None
        world.day_over = True
        world.record("sol_closed", by="autopilot", why=why, turns=self.turns)
        self.phase = "dusk"
        self._open(conv, dusk(world))
        return None

    # --- the line --------------------------------------------------------
    def talk(self, conv, world, urgent=False, now=None):
        """The desk wants to speak: TAB, or U for `urgent`. Opens the line if it may,
        and returns None; otherwise returns why not, for the pane."""
        if not self.live:
            return "a replay is a tape -- nobody on it can be talked to"
        if not S.COMMS:
            return "comms are off -- nobody is at the desk, so nothing reaches her. C turns them on"
        if self.line:
            return None
        if self.phase != "day":
            return ("the sol is over, and the rover is away from the pad -- no link tonight"
                    if not world.docked else
                    "she is writing her report -- the line opens when she has")
        if urgent:
            self.open_line(conv, "urgent", now)
            return None
        if world.docked:
            self.open_line(conv, "pad", now)
            return None
        return "she is away from the pad -- only an urgent call reaches her: U"

    def open_line(self, conv, why, now=None):
        """Someone is on the line. She stops after the call in hand, if she was mid-turn,
        and the clock opens nothing until it closes."""
        if self.line or not (self.live and S.COMMS):
            return False
        self.line, self.spoken, self.closing = why, False, False
        self.quiet_since = None
        self.mark = len(conv.calls)
        # A request still owed a retry belongs to the turn the line has just ended.
        self.retry_at, self.failures = None, conv.failures
        conv.cut()
        conv.world.record("line", opened=why)
        conv.write("note", OPENED[why])
        return True

    def say(self, conv, text, who="you"):
        """The desk speaks on the open line. The first word of an urgent call is marked
        as one, to her and on the tape. False if she is still answering."""
        if not self.line or conv.busy:
            return False
        urgent = who == "you" and self.line == "urgent" and not self.spoken
        sent = conv.send(f"URGENT from mission control: {text}" if urgent else text,
                         who="urgent" if urgent else who)
        if sent:
            self.spoken = True
            self.quiet_since = None
        return sent

    def hang_up(self):
        """N. The line closes once she has finished what she is saying."""
        if self.line:
            self.closing = True
        return bool(self.line)

    def wait_left(self, now=None):
        """Seconds before a quiet line closes, or None while it is not counting."""
        if not self.line or self.quiet_since is None:
            return None
        now = time.monotonic() if now is None else now
        return max(0.0, S.COMMS_WAIT - (now - self.quiet_since))

    def _on_line(self, conv, world, now):
        if self.quiet_since is None:
            self.quiet_since = now
        # The desk went away mid-line: there is nobody left on it to wait for.
        if not (self.closing or not S.COMMS or now - self.quiet_since >= S.COMMS_WAIT):
            return None
        why, self.line = self.line, None
        self.mark = len(conv.calls)
        self.failures = conv.failures
        world.record("line", closed=why)
        conv.write("note", "the line is closed")
        if self.phase != "day":
            return "night"
        self.after_line = True
        return None

    def _called(self, conv):
        """The turn just over ended on her calling the desk, and the call got through:
        "radio" or "sos". None otherwise."""
        if len(conv.calls) <= self.mark:
            return None
        c = conv.calls[-1]
        return c.name if self.live and S.COMMS and skills.got_through(c) else None

    # --- the clock -------------------------------------------------------
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

    def _open(self, conv, text):
        if self.phase == "day":
            self.turns += 1
        self.mark = len(conv.calls)
        conv.send(text, who="auto")
