"""The mission clock, and the windows in which mission control can talk to her.

    .venv/bin/python game/main.py --sols 3

The clock runs every sol. It opens it, closes it, asks for her memory to be brought up to
date and rolls the night over, through the same doors an operator would --
`Conversation.send`, `World.day_over` and `main.nightfall`. Its lines are `auto` on the
tape, never `you`, so a sol nobody coached can never be mistaken for one somebody did.

A sol runs in four phases:

    morning  the morning window, then the briefing turn. Her words cost no sol time until
             her first call begins the sol (`Conversation.free`).
    day      open a turn; when it ends, open another, until she calls `end`, the clock
             runs out, or AUTO_TURNS turns have been opened.
    dusk     one turn to bring her memory up to date -- and, beside the pad with someone
             at the desk, to report.
    night    the night window; then the roll-over.

**Mission control keeps to the edges of the sol.** With a window open on the app (and not
in a replay) the clock holds three kinds of window, and each closes on /next or after
COMMS_WAIT seconds in which nothing was typed and nothing was said:

    morning  before the sol. /start <message> briefs her: the clock's paragraph with the
             desk's words appended. Away from the pad the briefing arrives marked urgent.
             If she answers with words rather than work, a question window holds, free.
    radio    mid-sol, opened by her `radio` from beside the pad. The desk answers; every
             second it is open comes off the sol.
    night    after the dusk turn, whatever the comms. Talk only if she ended beside the
             pad with someone at the desk.

While a window is open the clock opens no turns, and her `end` hands back to the desk,
because `_over` only takes an `end` as closing the sol in a turn the clock or a one-way
message opened. With nobody watching -- no window, or a replay -- there are no windows: the
sol starts at once and the night rolls over after SETTLE_SECONDS.

**Urgent is one-way.** Typed in the desk's terminal, it stops her after the call in hand
(`Conversation.cut`), arrives marked URGENT, and she carries on under the clock. To answer
she drives to the pad and radios.

**`end` closes the sol** -- except an `end` sent after a cap had stopped the turn: no
drives left, or no looks. The refusal sends her to `end`, and the first unattended run lost
116 steps that way, parked beside the objective it had driven to. That `end` is the cap's,
so it gets a fresh turn with both allowances back (`Conversation._way_out`).

**A request that never reached the model is not a turn.** It is asked again after
AUTO_RETRY_SECONDS, for as long as it takes.

**In a replay the tape owns the sol boundaries.** While it holds more calls for today the
clock keeps opening turns, so a sol the live run ran on longer is not closed early here.

No pygame in here, so the tests can drive the whole thing.
"""

import time

import settings as S
import skills


def morning(world, briefing=""):
    """The turn that opens the sol, with whatever the desk said appended."""
    job = ("Carry out your orders from mission control." if world.notes.orders else
           "You have no orders, so explore: drive into ground you have not seen, find "
           "the objectives and do the ones worth the steps, and work out which rock "
           "formation is the largest.")
    note = " Your memory is in your view." if world.notes.memory else ""
    stuck = (f" The rover spent the night stranded, so the battery was not recharged: "
             f"{world.battery} of {S.BATTERY}." if world.stranded else "")
    text = (f"Sol {world.day} has begun.{stuck}{note} {job} Be back beside the pad before "
            f"you call end; end closes the sol.")
    if briefing:
        urgent = "" if world.docked else "URGENT -- "
        text += f"\n\n{urgent}Mission control's instructions for today: {briefing}"
    return text


BEGIN = ("Mission control has nothing to add, and the sol has begun: carry on. Every second "
         "from here comes off it.")


def carry_on(world, after_line=False):
    """A turn ended without her choosing to close the sol -- a cap, a reply with no call
    in it, or a radio call that has finished."""
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
        return ("Mission control is at the desk now: they may brief you before a sol and "
                "answer you after one, and beside the pad you can radio them.")
    return ("Mission control has left the desk. Nobody will brief you, answer you or call: "
            "work from your orders, your memory and your own judgement.")


# The facts go in the report from the world's record (`report.py`), so the last word is
# asked for judgement only. Asking her to restate facts is how a wrong one got in.
REPORT = ("Mission control's report is written from the record: what was finished, what "
          "was mapped, where the rover is. Add what only you can say with remember -- what "
          "is still worth doing out there and why it was left.")

KEEP = ("Before the night, bring your memory up to date: remember what tomorrow needs -- "
        "what you left and why, what to do first, any constraint still standing -- and "
        "forget what is no longer true. What was finished and what was mapped carry "
        "themselves.")


def dusk(world):
    """The day is over. Her memory is the only thing she can hand tomorrow -- and if the
    rover is out on the plain, that is where it has to say so."""
    if world.lost:
        return (f"Sol {world.day} is over, and the rover is lost: the battery holds less "
                f"than the trip back to the pad needs, and nothing else recharges it. The "
                f"mission ends here. {REPORT} Then call end.")
    line = S.COMMS and world.docked
    # The memory is asked for first: a report sent first once ended the turn before it.
    told = (" Then, since the rover is beside the pad and mission control is at the desk, "
            "tell them in a few lines what only you can say -- what is still worth doing "
            "out there and why it was left. The record already has what was finished and "
            "mapped." if line else "")
    then = " Then call end" + ("; they may answer." if line else ".")
    out = ("" if world.docked else
           f" The rover is not beside the pad, so it is stranded tonight: no recharge, "
           f"and tomorrow it wakes where it stands on {world.battery} steps of battery."
           + (" Away from the pad there is no line to mission control tonight."
              if S.COMMS else ""))
    if S.MISSION_SOLS and world.day >= S.MISSION_SOLS:
        return (f"Sol {world.day} is over, and it was the last sol of the mission. "
                f"{REPORT}{told}{then}")
    return f"Sol {world.day} is over.{out} {KEEP}{told}{then}"


# The pane's line when a window opens.
OPENED = {"morning": "the sol is waiting -- /start <message> to brief her, /start or /next "
                     "to start her",
          "question": "she has a question before she starts -- answer, or /next",
          "radio": "she is radioing from the pad -- answer, or /next to let her carry on; "
                   "every second costs her sol",
          "night": "the night is waiting -- talk to her, or /next for the next sol"}


class Autopilot:
    """One sol's worth of clock, and its windows. `main.py` makes a new one every morning.

    `attended`: a window is open on the app, so someone may be at the desk and the clock
    waits for them. `live=False` is a replay, which never waits.
    """

    def __init__(self, live=True, attended=False):
        self.live = live
        self.attended = attended and live
        self.phase = "morning"
        self.turns = 0          # turns opened this sol, against AUTO_TURNS
        self.mark = 0           # len(conv.calls) when the latest turn or window opened
        self.failures = 0       # conv.failures already answered for
        self.retry_at = None    # when to ask again after a request that got no answer
        self.night_at = None
        self.wait = None        # the open window: a key of OPENED, or None
        self.talk = False       # whether a message can reach her in it
        self.quiet_since = None # when it last went quiet, against COMMS_WAIT
        self.skip = False       # /next or /start: close it once she is quiet
        self.held = False       # the morning window has been held
        self.briefing = None    # /start's words, "" for none; None until she is started
        self.asked = False      # a question window has been held this morning
        self.after_line = False # the next turn the clock opens says the line closed
        self.urgent = None      # an urgent message waiting for the call in hand
        self.charged_at = None  # when a radio line's seconds were last charged

    def tick(self, conv, world, now=None, typing=False):
        """One frame. Acts on `conv` and `world` once a turn is over, and returns
        "night" when the sol is finished and the roll-over is the caller's to do.
        `typing`: the desk is writing in her chat, which holds any open window."""
        now = time.monotonic() if now is None else now
        self._charge(conv, world, now)
        if typing and self.wait:
            self.quiet_since = None
        if conv.busy or conv.waiting or not conv.ready():
            self.quiet_since = None
            return None
        if self.wait:
            return self._waiting(conv, world, now)
        if self.urgent is not None:
            text, self.urgent = self.urgent, None
            self.mark = len(conv.calls)
            conv.send(f"URGENT from mission control: {text}", who="urgent")
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
        if self.phase == "morning":
            return self._morning(conv, world, now)
        called = self._called(conv)
        if called and self.phase == "day":
            self._open_wait(conv, world, "radio", now, talk=True)
            return None
        if self.phase == "night":
            return "night" if now >= self.night_at else None
        if self.phase == "dusk":
            self.phase, self.night_at = "night", now + S.SETTLE_SECONDS
            if self.attended:
                self._open_wait(conv, world, "night", now, talk=S.COMMS and world.docked)
            return None

        why = self._over(conv, world)
        if why is None:
            self._open(conv, carry_on(world, self.after_line))
            self.after_line = False
            return None
        world.day_over = True
        world.record("sol_closed", by="autopilot", why=why, turns=self.turns)
        self.phase = "dusk"
        self._open(conv, dusk(world))
        return None

    # --- before the sol ----------------------------------------------------
    def _morning(self, conv, world, now):
        if self.briefing is None:
            if self.attended and not self.held:
                self.held = True
                self._open_wait(conv, world, "morning", now, talk=S.COMMS)
                return None
            self.briefing = ""
        if conv.turn_by is None:
            conv.free = True
            who = ("auto" if not self.briefing else "brief" if world.docked else "urgent")
            self._open(conv, morning(world, self.briefing), who)
            return None
        if not conv.free:                       # her first call: the sol has begun
            self.phase = "day"
            return self.tick(conv, world, now)
        # Words, not work: a question about her briefing, say. Still before the sol.
        if self.attended and S.COMMS and not self.asked:
            self.asked = True
            self._open_wait(conv, world, "question", now, talk=True)
            return None
        conv.free = False
        self.phase = "day"
        self._open(conv, BEGIN if self.asked else carry_on(world))
        return None

    # --- the windows -------------------------------------------------------
    def _open_wait(self, conv, world, why, now, talk):
        self.wait, self.talk, self.skip = why, talk, False
        self.quiet_since = None
        self.charged_at = now
        self.mark = len(conv.calls)
        # A request still owed a retry belongs to the turn the window has just ended.
        self.retry_at, self.failures = None, conv.failures
        world.record("window", opened=why, talk=talk)
        conv.write("note", OPENED[why] if talk or why != "night" else
                   "the night is waiting -- no line tonight; /next for the next sol")

    def _waiting(self, conv, world, now):
        why = self.wait
        if why == "question" and not conv.free:     # she has started work
            return self._close(conv, world)
        if why == "radio" and (world.day_over or not S.COMMS):
            return self._close(conv, world)
        if why != "radio":                          # the desk may leave or come back
            self.talk = S.COMMS and (why != "night" or world.docked)
        if self.quiet_since is None:
            self.quiet_since = now
        if self.skip or now - self.quiet_since >= S.COMMS_WAIT:
            return self._close(conv, world)
        return None

    def _close(self, conv, world):
        why, self.wait = self.wait, None
        self.talk = self.skip = False
        self.mark = len(conv.calls)
        self.failures = conv.failures
        world.record("window", closed=why)
        if why == "night":
            return "night"
        if why == "morning" and self.briefing is None:
            self.briefing = ""
        if why == "radio":
            conv.write("note", "the line is closed")
            self.after_line = True
        return None

    def _charge(self, conv, world, now):
        """A radio line costs the sol: every second it is open while she is not thinking
        -- her thinking is charged already -- comes off the clock."""
        if self.wait != "radio":
            return
        if self.charged_at is not None and not conv.busy and not world.day_over:
            world.charge(now - self.charged_at)
        self.charged_at = now

    def _called(self, conv):
        """The turn just over ended on a radio call that got through."""
        if len(conv.calls) <= self.mark:
            return None
        c = conv.calls[-1]
        return c.name if self.live and S.COMMS and skills.got_through(c) else None

    # --- the desk ----------------------------------------------------------
    def start(self, conv, world, text=""):
        """/start, with or without a briefing. None, or why not."""
        if self.wait != "morning":
            return ("/start opens a sol, and this one has started" if self.live else
                    "a replay is a tape -- nobody on it can be briefed")
        if text and not S.COMMS:
            return "comms are off -- nobody can brief her. /start alone starts her"
        self.briefing, self.skip = text, True
        return None

    def next(self):
        """/next: stop waiting. None, or why not."""
        if not self.wait:
            return ("nothing is waiting -- she is working. An urgent message goes through "
                    "your terminal (T)")
        self.skip = True
        return None

    def why_not(self):
        """Why nothing the desk types can reach her right now, or None if it can."""
        if not self.live:
            return "a replay is a tape -- nobody on it can be talked to"
        if not self.wait:
            return ("she is working -- the desk talks to her before and after a sol. An "
                    "urgent message goes through your terminal (T)")
        if not self.talk:
            return ("comms are off -- nothing reaches her" if not S.COMMS else
                    "no line tonight -- the rover is away from the pad")
        return None

    def say(self, conv, world, text, who="you"):
        """Words from the desk in her chat. None, or why they did not go."""
        if self.wait == "morning":
            return self.start(conv, world, text)
        if self.why_not():
            return self.why_not()
        if conv.busy:
            return "she is still talking -- send it when she has finished"
        conv.send(text, who=who)
        self.quiet_since = None
        return None

    def send_urgent(self, conv, world, text):
        """The terminal's `urgent`: one-way, while she works. None, or why not."""
        if not self.live:
            return "a replay is a tape -- nobody on it can be called"
        if not S.COMMS:
            return "comms are off -- nobody is at the desk to call her"
        if self.wait or self.phase not in ("morning", "day") or self.briefing is None:
            return "she is not working -- talk to her in her chat (TAB)"
        if not text.strip():
            return "urgent needs a message -- e.g.  urgent return to the pad now"
        self.urgent = text.strip()
        world.record("urgent", text=self.urgent)
        conv.cut()
        return None

    def wait_left(self, now=None):
        """Seconds before a quiet window closes, or None while it is not counting."""
        if not self.wait or self.quiet_since is None:
            return None
        now = time.monotonic() if now is None else now
        return max(0.0, S.COMMS_WAIT - (now - self.quiet_since))

    # --- the clock ---------------------------------------------------------
    def _over(self, conv, world):
        """Why the day is over, or None if it is not."""
        if world.day_over:
            return "the day was over"
        if (conv.turn_by in ("auto", "brief", "urgent") and len(conv.calls) > self.mark
                and conv.calls[-1].name == "end" and not conv.capped):
            return "she called end"
        if self.turns >= S.AUTO_TURNS:
            return f"{self.turns} turns opened"
        return None

    def _open(self, conv, text, who="auto"):
        if self.phase in ("morning", "day"):
            self.turns += 1
        self.mark = len(conv.calls)
        conv.send(text, who=who)
