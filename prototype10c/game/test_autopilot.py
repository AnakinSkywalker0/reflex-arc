"""The mission clock and the line: sols that open, run and roll over by themselves, and
the desk that can talk to her only from the pad or by urgent call.

    .venv/bin/python game/test_autopilot.py

The model is a script and threads run inline, as in `test_chat.py`. `fly` stands in for
`main.py`'s loop -- pump, tick the clock, roll the night over when it says so -- with
one frame a second of pretend time, so the settle, retry and line waits are counted
rather than slept through. Nobody is at the desk unless a test says so.
"""

import json
import sys
import tempfile
import types
from pathlib import Path

import autopilot
import chat
import prompts
import replay
import settings as S
import skills
from world import World

S.STORM_ON = False
S.DAY_MODE = "gemma"
S.COMMS = False


def check(name, cond, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}{'   ' + detail if detail else ''}")
    return bool(cond)


class Inline:
    def __init__(self, target, args=(), daemon=False):
        self._target, self._args = target, args

    def start(self):
        self._target(*self._args)


chat.threading = types.SimpleNamespace(Thread=Inline)


def call(name, **args):
    return {"name": name, "arguments": args}


END = ("Done for today.", [call("end")])


class Model:
    """Replies in order, shared across every sol's conversation. Past the end it ends.

    A reply that is the string "down" is a request that never reached the model.
    """

    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []

    def talk(self, conv):
        def stream(messages, allowed=None):
            self.sent.append(messages)
            reply = self.replies.pop(0) if self.replies else END
            if reply == "down":
                conv.q.put(("error", "URLError: connection refused"))
                return
            text, calls = reply
            if text:
                conv.q.put(("say", text))
            conv.q.put(("done", ({"prompt_eval_count": 100, "eval_count": 5}, calls)))
        conv._stream = stream
        return conv


def fly(w, model, frames=400, link=None):
    """`main.py`'s loop with the pygame taken out. Returns (convs, rows, nights)."""
    rows = []
    w.recorder = lambda kind, **f: rows.append({"kind": kind, **f})
    convs = [model.talk(chat.Conversation(w, link=link))]
    convs[0].open_day(w)
    pilot, nights = autopilot.Autopilot(), 0
    for t in range(frames):
        convs[-1].pump()
        if pilot.tick(convs[-1], w, now=float(t)) == "night":
            nights += 1
            if S.MISSION_SOLS and w.day >= S.MISSION_SOLS:
                break
            w.next_day()
            convs.append(model.talk(chat.Conversation(w, link=link)))
            convs[-1].open_day(w)
            pilot = autopilot.Autopilot()
    return convs, rows, nights


def said_by(conv, who):
    return [text for w, text in conv.lines if w == who]


def test_the_clock_opens_the_sol():
    print("the morning")
    w = World()
    convs, _, _ = fly(w, Model([END]), frames=1)
    opened = said_by(convs[0], "auto")
    ok = check("one turn opened, by the clock", len(opened) == 1, str(opened))
    ok &= check("labelled as the clock and never as the operator",
                not said_by(convs[0], "you"))
    ok &= check("with no orders, it says to explore", "explore" in opened[0])
    ok &= check("and says what closes the sol", "closes the sol" in opened[0])
    w = World()
    w.notes.order("finish objective 3 today")
    convs, _, _ = fly(w, Model([END]), frames=1)
    ok &= check("with orders, it points at them instead",
                "orders" in said_by(convs[0], "auto")[0]
                and "explore" not in said_by(convs[0], "auto")[0])
    return ok


def test_her_end_closes_the_sol_and_dusk_asks_for_the_note():
    print("end closes the sol")
    w = World()
    model = Model([("", [call("count", kind="rock")]), END,
                   ("", [call("remember", text="the C opens east")]), END])
    S.MISSION_SOLS = 1
    try:
        convs, rows, nights = fly(w, model)
    finally:
        S.MISSION_SOLS = 0
    c = convs[0]
    opened = said_by(c, "auto")
    ok = check("the day is over", w.day_over)
    ok &= check("with time still left, because she chose to stop", w.time_left > 0)
    ok &= check("two turns: the day and the dusk", len(opened) == 2, str(opened))
    ok &= check("the dusk turn asks for the note", "remember" in opened[1])
    ok &= check("and on the last sol, for a report", "report" in opened[1])
    ok &= check("the note was written", w.notes.memory == "the C opens east")
    ok &= check("the closing is on the tape, with why",
                any(r["kind"] == "sol_closed" and r["why"] == "she called end"
                    for r in rows), str([r for r in rows if r["kind"] == "sol_closed"]))
    ok &= check("then the night fell, once", nights == 1)
    return ok


def test_a_cut_off_turn_is_carried_on():
    print("a cap is not an end")
    w = World()
    model = Model([("I will look around.", []),          # prose, no call
                   ("", [call("count", kind="rock")]), END])
    convs, rows, _ = fly(w, model, frames=6)
    opened = said_by(convs[0], "auto")
    closed = [r for r in rows if r["kind"] == "sol_closed"]
    ok = check("a reply with no call gets another turn", len(opened) >= 2, str(opened))
    ok &= check("which says what is left", "steps of battery" in opened[1]
                and "seconds of the sol" in opened[1])
    ok &= check("and the sol only closes on her end, in the second turn",
                closed and closed[0]["why"] == "she called end"
                and closed[0]["turns"] == 2, str(closed))
    return ok


def test_an_end_the_drive_cap_asked_for_does_not_close_the_sol():
    """The first unattended run: twenty drives, parked beside the high-priority
    objective with 116 steps left, told by the refusal to call end -- and the sol shut."""
    print("out of drives is not out of day")
    w = World()
    keep = S.MOVE_HOPS
    S.MOVE_HOPS = 2
    try:
        model = Model([("", [call("goto", x=18, y=15)]), ("", [call("goto", x=15, y=18)]),
                       END,                                  # the cap's end
                       ("", [call("goto", x=15, y=15)]), END])  # her own
        convs, rows, _ = fly(w, model, frames=8)
    finally:
        S.MOVE_HOPS = keep
    opened = said_by(convs[0], "auto")
    closed = [r for r in rows if r["kind"] == "sol_closed"]
    ok = check("a second turn was opened", len(opened) >= 2, str(opened))
    ok &= check("with the drives back", "drives back" in opened[1])
    ok &= check("and the sol closed on the end she chose, in turn 2",
                closed and closed[0]["why"] == "she called end"
                and closed[0]["turns"] == 2, str(closed))
    return ok


def test_an_end_the_looks_cap_asked_for_does_not_close_the_sol():
    """Drives in hand, looks spent: the refusal used to say "call end to hand back",
    and with nobody on shift that end closed the sol."""
    print("out of looks is not out of day")
    w = World()
    keep = S.FREE_HOPS
    S.FREE_HOPS = 2
    try:
        model = Model([("", [call("count", kind="rock")]), ("", [call("count", kind="rock")]),
                       END,                                      # the cap's end
                       ("", [call("goto", x=15, y=12)]), END])   # her own
        convs, rows, _ = fly(w, model, frames=8)
    finally:
        S.FREE_HOPS = keep
    closed = [r for r in rows if r["kind"] == "sol_closed"]
    ok = check("the sol closed on the end she chose, in turn 2",
               closed and closed[0]["why"] == "she called end"
               and closed[0]["turns"] == 2, str(closed))
    return ok


def test_nobody_is_ever_told_to_hand_back():
    print("the way out, said truthfully")
    w = World()
    c = chat.Conversation(w)
    said = []
    c.moves, c.frees = S.MOVE_HOPS, S.FREE_HOPS
    said.append(c._left())
    c.frees = 0
    said.append(c._left())
    c.moves, c.frees = 0, S.FREE_HOPS
    c._deny({"name": "count", "arguments": {}}, move=False)
    c.moves = S.MOVE_HOPS
    c._deny({"name": "goto", "arguments": {}}, move=True)
    said += [m["content"] for m in c.messages if m["role"] == "tool"]
    blob = " ".join(said)
    ok = check("no note or refusal says hand back", "hand back" not in blob
               and "crew" not in blob, blob[:200])
    ok &= check("every one says the sol goes on",
                all("the sol goes on" in x for x in said), str(said))
    for comms in (False, True):
        S.COMMS = comms
        prompts.use(prompts.DEFAULT)
        schema = skills.tools_for(["end"])[0]["function"]["description"]
        for where, text in (("the end schema", schema), ("the prompt", prompts.SYSTEM)):
            flat = " ".join(text.split())
            ok &= check(f"comms {'on' if comms else 'off'}: {where} never says hand back "
                        f"or the crew", "hand back" not in flat
                        and "hand the conversation" not in flat and "crew" not in flat)
    S.COMMS = False
    prompts.use(prompts.DEFAULT)
    return ok


def test_a_planner_that_never_ends_cannot_hold_the_sol():
    print("AUTO_TURNS")
    w = World()
    model = Model([("Thinking about it.", [])] * 50)
    convs, rows, nights = fly(w, model, frames=40)
    closed = [r for r in rows if r["kind"] == "sol_closed"]
    ok = check("the sol was called", closed and w.day > 1, str(closed))
    ok &= check(f"after {S.AUTO_TURNS} turns",
                closed and closed[0]["turns"] == S.AUTO_TURNS, str(closed))
    return ok


def test_running_out_of_time_closes_the_sol():
    print("the clock runs out")
    w = World()
    w.charge(w.time_left - 1)
    model = Model([("", [call("goto", x=25, y=25)]), ("Out of steps.", [])])
    convs, rows, _ = fly(w, model, frames=8)
    closed = [r for r in rows if r["kind"] == "sol_closed"]
    ok = check("closed because the day was over",
               closed and closed[0]["why"] == "the day was over", str(closed))
    ok &= check("after a single turn", closed and closed[0]["turns"] == 1)
    return ok


def test_a_dropped_connection_is_asked_again_not_counted():
    """Ollama itself down, so there is no fallback to go to either."""
    print("ollama down")
    w = World()
    model = Model(["down", "down", ("", [call("count", kind="rock")]), END])
    keep, keep_fb = S.AUTO_RETRY_SECONDS, S.MODEL_FALLBACK
    S.AUTO_RETRY_SECONDS, S.MODEL_FALLBACK = 10, S.MODEL
    try:
        early = Model(["down"])
        fly(World(), early, frames=5)
        convs, rows, _ = fly(w, model, frames=30)
    finally:
        S.AUTO_RETRY_SECONDS, S.MODEL_FALLBACK = keep, keep_fb
    c = convs[0]
    ok = check("both failures were noticed", c.failures == 2)
    ok &= check("and said so", sum("did not answer" in t for t in said_by(c, "auto")) == 2)
    ok &= check("the retry carried on the same turn rather than opening one",
                [r for r in rows if r["kind"] == "sol_closed"][0]["turns"] == 1)
    ok &= check("and was not resent the second the error landed",
                len(early.sent) == 1, str(len(early.sent)))
    ok &= check("the sol still finished", w.day == 2)
    return ok


def test_the_cloud_drops_for_a_sol_and_comes_back():
    """`--outage 2`, end to end but for the socket: the planner's model is routed to the
    dead host on sol 2, the fallback answers, and a probe brings the cloud back."""
    print("--outage 2")
    answered, probed = [], []

    class Cloud(Model):
        def talk(self, conv):
            def stream(messages, allowed=None):
                if conv._sent_host == S.OUTAGE_HOST:
                    conv.q.put(("error", "URLError: [Errno 111] Connection refused"))
                    return
                answered.append((conv.day, conv._sent_model))
                text, calls = self.replies.pop(0) if self.replies else END
                if text:
                    conv.q.put(("say", text))
                conv.q.put(("done", ({"prompt_eval_count": 1, "eval_count": 1}, calls)))
            conv._stream = stream
            return conv

    def probe(model, host):
        probed.append(host)
        return host != S.OUTAGE_HOST

    keep = S.OUTAGE_SOLS, S.PROBE_SECONDS, S.MISSION_SOLS
    S.OUTAGE_SOLS, S.PROBE_SECONDS, S.MISSION_SOLS = (2,), 0, 3
    try:
        replies = []
        for sol in (1, 2, 3):
            replies += [("", [call("count", kind="rock")]), END,
                        ("", [call("remember", text=f"sol {sol}")]), END]
        w = World()
        convs, rows, nights = fly(w, Cloud(replies), frames=60, link=chat.Link(probe))
    finally:
        S.OUTAGE_SOLS, S.PROBE_SECONDS, S.MISSION_SOLS = keep
    by_sol = {d: {m for dd, m in answered if dd == d} for d in (1, 2, 3)}
    ok = check("sol 1 on the cloud", by_sol[1] == {S.MODEL}, str(by_sol))
    ok &= check("sol 2 on the fallback, every request",
                by_sol[2] == {S.MODEL_FALLBACK}, str(by_sol))
    ok &= check("sol 3 is back on the cloud from its first request: the morning probes",
                by_sol[3] == {S.MODEL}, str(by_sol))
    ok &= check("probes failed while it was cut and answered once it was not",
                S.OUTAGE_HOST in probed and S.OLLAMA_HOST in probed)
    ok &= check("the drop was not a failure, so nothing waited out a retry",
                all(c.failures == 0 for c in convs) and nights == 3)
    ok &= check("the pane said it was dropped, and staged",
                any("simulated outage" in t for t in said_by(convs[1], "error")))
    ok &= check("and said when it came back",
                any("answered a probe" in t for c in convs for t in said_by(c, "note")))
    return ok


def test_three_sols_with_no_key_pressed():
    print("--auto --sols 3")
    w = World()
    replies = []
    for sol in (1, 2, 3):
        replies += [("", [call("todo", text=f"survey, sol {sol}")]),
                    ("", [call("count", kind="rock")]), END,
                    ("", [call("remember", text=f"note from sol {sol}")]), END]
    model = Model(replies)
    S.MISSION_SOLS = 3
    try:
        convs, rows, nights = fly(w, model, frames=200)
    finally:
        S.MISSION_SOLS = 0
    ok = check("three sols played", w.day == 3 and nights == 3, f"day {w.day}")
    ok &= check("every sol on a fresh conversation",
                len(convs) == 3 and all(c.day == n for n, c in zip((1, 2, 3), convs)))
    ok &= check("and none of yesterday's talk in it",
                not any("sol 1" in json.dumps(m) for m in convs[1].messages
                        if m["role"] != "user" or "WHAT YOU CAN SEE" not in m["content"]))
    ok &= check("the note crossed each night",
                any("note from sol 1" in json.dumps(m) for m in model.sent[5]))
    ok &= check("and the clock pointed her at it",
                "note from last night" in said_by(convs[1], "auto")[0])
    ok &= check("the last note is the report, and it is kept",
                w.carry()["memory"] == "note from sol 3")
    ok &= check("nothing was typed by an operator",
                not any(said_by(c, "you") for c in convs))
    return ok


def test_the_prompt_says_who_closes_the_sol_and_who_can_be_reached():
    print("the prompt, with and without someone at the desk")
    ok = True
    for comms in (False, True):
        S.COMMS = comms
        p = prompts.sighted()
        flat = " ".join(p.split())
        tag = "on" if comms else "off"
        offered = [n for n in skills.NAMES if comms or n not in ("radio", "sos")]
        ok &= check(f"{tag}: says end ends the turn and the sol with it",
                    "ends your turn" in p and "the sol with it" in p)
        ok &= check(f"{tag}: names every skill she is offered",
                    all(f"{n}(" in p for n in offered))
        ok &= check(f"{tag}: and only those", comms or ("radio(" not in p
                                                         and "sos(" not in p))
        ok &= check(f"{tag}: never says 'auto', which reads as avoid=auto", "auto" not in p)
        if comms:
            ok &= check("on: the pad is the link, and URGENT stops her",
                        "the pad is your link" in flat and "URGENT" in flat)
            ok &= check("on: on the line her end hands back",
                        "hands the turn back to them" in flat)
        else:
            ok &= check("off: nobody is at the desk", "Nobody is at mission control's desk"
                        in flat)
    S.COMMS = False
    prompts.use(prompts.DEFAULT)
    return ok


def test_in_a_replay_the_tape_says_where_a_sol_ends():
    print("replay with the clock on")
    rows = []
    # Three turns on sol 1 -- say she ended, then an operator spoke twice more. More
    # than the dusk turn could swallow by accident.
    for day, name in ((1, "count"), (1, "end"), (1, "count"), (1, "end"), (1, "count"),
                      (1, "end"), (2, "end")):
        rows.append({"day": day, "who": "call", "name": name, "args": {}, "ran": True})
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "chat.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
        script = replay.Script(Path(d))
        w = World()
        r = replay.Replay(w, script)
        r.open_day(w)
        pilot, night = autopilot.Autopilot(), None
        for t in range(20):
            r.pump()
            if pilot.tick(r, w, now=float(t)) == "night":
                night = t
                break
        ran = [c.name for c in r.calls]
        ok = check("all six of sol 1's calls ran in sol 1, not just up to the first end",
                   ran[:6] == ["count", "end"] * 3, str(ran))
        ok &= check("sol 2's was left for sol 2", script.peek()["day"] == 2)
        ok &= check("and the sol closed", night is not None and w.day_over)
        ok &= check("with nothing of sol 2's run early", len(ran) == 7 and
                    ran[6] == "end" and script.peek() is not None, str(ran))
    return ok


def test_the_clock_warns_about_a_stranding():
    print("stranded")
    w = World()
    w.pos = (3, 3)
    ok = check("dusk away from the pad says she is stranded", "stranded" in autopilot.dusk(w))
    w.next_day()
    ok &= check("the morning after says there was no recharge",
                "not recharged" in autopilot.morning(w))
    w2 = World()
    ok &= check("beside the pad, neither does", "stranded" not in autopilot.dusk(w2)
                and "stranded" not in autopilot.morning(w2))
    return ok


def test_thinking_runs_the_clock_and_the_tape_keeps_it():
    print("slow thinking is a short sol")
    w = World()
    written = []
    model = Model([("", [call("goto", x=15, y=10)]), END])
    c = model.talk(chat.Conversation(w, types.SimpleNamespace(write=written.append)))
    clock = iter(range(0, 1000, 4))            # every request takes four seconds
    real = chat.time.monotonic
    chat.time.monotonic = lambda: float(next(clock))
    try:
        c.send("drive north")
        c.pump()
    finally:
        chat.time.monotonic = real
    secs = [r["seconds"] for r in written if r["who"] == "cost"]
    drive = [r for r in written if r["who"] == "call" and r["name"] == "goto"][0]
    ok = check("each answer's seconds went on the clock, and so did the drive",
               w.time_left == S.DAY_SECONDS - sum(secs) - w.steps * S.STEP_SECONDS,
               f"{w.time_left} left, thought {secs}, drove {w.steps}")
    ok &= check("thinking cost no charge", w.battery == S.BATTERY - w.steps)
    ok &= check("the call row carries the clock it ran on",
                drive["clock"] == S.DAY_SECONDS - secs[0], str(drive.get("clock")))
    return ok


def test_a_replay_runs_on_the_tapes_clock():
    print("replay sets the clock")
    rows = [{"day": 1, "who": "call", "name": "goto", "args": {"x": 15, "y": 10},
             "ran": True, "clock": 42.5}]
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "chat.jsonl").write_text(json.dumps(rows[0]))
        w = World()
        r = replay.Replay(w, replay.Script(Path(d)))
        r.send("go")
        r.pump()
        ok = check("the drive ran from the recorded clock, not from a full sol",
                   w.time_left == 42.5 - w.steps * S.STEP_SECONDS, str(w.time_left))
    w = World()
    w.charge(1.0)
    w.set_clock(0.0)
    ok &= check("a recorded clock at nought ends the sol", w.day_over)
    w.set_clock(30.0)
    ok &= check("and setting it back up never reopens one", w.day_over)
    return ok


def test_flat_away_from_the_pad_ends_the_mission():
    print("lost")
    w = World()
    w.pos = (3, 3)
    w.battery = 2            # not flat: the run that played sixteen empty sols
    text = autopilot.dusk(w)
    ok = check("the dusk turn says the rover is lost", "lost" in text, text)
    ok &= check("and asks for judgement, not facts: the report is the record's",
                "written from the record" in text and "what you found" not in text)
    return ok


def test_a_replay_keeps_each_sols_calls_to_that_sol():
    print("replay finds the sol boundaries")
    rows = [{"day": 1, "who": "call", "name": "count", "args": {"kind": "rock"},
             "ran": True}, {"day": 1, "who": "result", "text": "x"},
            {"day": 2, "who": "call", "name": "end", "args": {}, "ran": True},
            {"day": 2, "who": "result", "text": "y"}]
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "chat.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
        s = replay.Script(Path(d))
        first = s.next_turn(1)
        ok = check("sol 1 gets its own call", first and first["name"] == "count")
        ok &= check("and not sol 2's", s.next_turn(1) is None and not s.spent)
        ok &= check("which is still there for sol 2", s.next_turn(2)["name"] == "end")
    return ok


def live_then_replay(replies, sols=1):
    """A live run on the clock, kept to a tape, then replayed from it with the clock on.
    Returns (live world, live calls, replay world, replay)."""
    keep = S.MISSION_SOLS
    S.MISSION_SOLS = sols

    def run(w, conv):
        conv.open_day(w)
        pilot = autopilot.Autopilot()
        for t in range(200):
            conv.pump()
            if getattr(conv, "diverged", None):
                break
            if pilot.tick(conv, w, now=float(t)) == "night":
                break
        return conv

    try:
        with tempfile.TemporaryDirectory() as d:
            tape = chat.Tape(Path(d) / "chat.jsonl")
            w = World()
            conv = run(w, Model(replies).talk(chat.Conversation(w, tape)))
            tape.close()
            w2 = World()
            r = run(w2, replay.Replay(w2, replay.Script(Path(d))))
    finally:
        S.MISSION_SOLS = keep
    return w, conv.calls, w2, r


def test_a_drive_at_dusk_replays_as_refused():
    """She closed the sol with time left, then asked for a drive in the dusk turn. Live
    refuses it; the replay used to run it, and diverged."""
    print("replay: a drive after the sol closed")
    w, calls, w2, r = live_then_replay([
        ("", [call("count", kind="rock")]), END,
        ("", [call("remember", text="note")]),
        ("", [call("goto", x=15, y=10)]), END])
    drive = [c for c in calls if c.name == "goto"][0]
    ok = check("live: the dusk drive was refused", drive.result.startswith("OUT_OF_TIME"),
               drive.result)
    ok &= check("and says the sol is over rather than that it ran out",
                "already over" in drive.result and "ran out" not in drive.result)
    ok &= check("the replay agrees, call for call", not r.diverged and
                [c.result for c in r.calls if c.name != "end"]
                == [c.result for c in calls if c.name != "end"], str(r.diverged))
    ok &= check("and the rover is where the live one stopped", w2.pos == w.pos)
    return ok


def test_a_turn_the_cap_ended_replays_as_two():
    """A turn ended by refusals rather than by `end`. The replay has to end it at the
    same call, or the next turn's drive is refused against the old turn's allowance."""
    print("replay: turn boundaries without an end")
    keep = S.MOVE_HOPS, S.MOVE_GRACE
    S.MOVE_HOPS, S.MOVE_GRACE = 1, 1
    try:
        w, calls, w2, r = live_then_replay([
            ("", [call("goto", x=15, y=12)]),
            ("", [call("goto", x=15, y=10)]),        # refused: the turn is ended for her
            ("", [call("goto", x=18, y=12)]),        # the clock's next turn
            ("", [call("goto", x=15, y=14)]), END])
    finally:
        S.MOVE_HOPS, S.MOVE_GRACE = keep
    ok = check("live: two drives ran, in two turns",
               [c.name for c in calls].count("goto") == 2, str([c.name for c in calls]))
    ok &= check("the replay ran the same calls to the same results", not r.diverged and
                [(c.name, c.result) for c in r.calls if c.name != "end"]
                == [(c.name, c.result) for c in calls if c.name != "end"], str(r.diverged))
    ok &= check("and ended where the live rover did", w2.pos == w.pos, f"{w2.pos} {w.pos}")
    return ok


class Desk:
    """Someone at the desk for the length of a `with`, and `MISSION_SOLS` set alongside."""

    def __init__(self, on=True, sols=0):
        self.on, self.sols = on, sols

    def __enter__(self):
        self.keep = S.COMMS, S.MISSION_SOLS
        S.COMMS, S.MISSION_SOLS = self.on, self.sols
        prompts.use(prompts.DEFAULT)

    def __exit__(self, *exc):
        S.COMMS, S.MISSION_SOLS = self.keep
        prompts.use(prompts.DEFAULT)


def sol(w, model, rover=None):
    """One sol's conversation and clock, as `main.py` holds them. `rover`, a one-item
    list, says whether the rover has finished its leg -- False holds the next request."""
    rows = []
    w.recorder = lambda kind, **f: rows.append({"kind": kind, **f})
    c = model.talk(chat.Conversation(w))
    if rover is not None:
        c.ready = lambda: rover[0]
    c.open_day(w)
    return c, autopilot.Autopilot(), rows


def until(c, pilot, w, test, start=0, frames=300):
    """Frames until `test(result)` holds. Returns (frame, result), or (None, None)."""
    for t in range(start, start + frames):
        c.pump()
        got = pilot.tick(c, w, now=float(t))
        if test(got):
            return t, got
    return None, None


def test_the_night_line_opens_beside_the_pad_and_waits():
    print("the night line")
    with Desk():
        w = World()
        c, pilot, rows = sol(w, Model([END, ("", [call("remember", text="n")]), END]))
        opened, _ = until(c, pilot, w, lambda got: pilot.line)
        ok = check("after her report the line is open for the night",
                   opened is not None and pilot.line == "night" and w.day_over)
        ok &= check("the dusk turn told her so, and asked for the report",
                    "line is open tonight" in said_by(c, "auto")[-1])
        early, _ = until(c, pilot, w, lambda got: got == "night", start=opened + 1,
                         frames=int(S.COMMS_WAIT) - 1)
        ok &= check("nobody answering, it waits out COMMS_WAIT", early is None)
        late, _ = until(c, pilot, w, lambda got: got == "night", start=opened + int(S.COMMS_WAIT))
        ok &= check("then the night falls by itself", late is not None, str(late))
        ok &= check("and the tape has the line opening and closing",
                    [r.get("opened") or r.get("closed") for r in rows if r["kind"] == "line"]
                    == ["night", "night"])
    return ok


def test_no_line_away_from_the_pad_or_with_nobody_at_the_desk():
    print("no line")
    with Desk():
        w = World()
        w.pos = (3, 3)
        c, pilot, _ = sol(w, Model([END, END]))
        t, _ = until(c, pilot, w, lambda got: got == "night", frames=20)
        ok = check("stranded, the night falls with no line", t is not None and not pilot.line)
        ok &= check("and dusk told her only sos gets through",
                    "no line tonight" in said_by(c, "auto")[-1])
    with Desk(on=False):
        w = World()
        c, pilot, _ = sol(w, Model([END, END]))
        t, _ = until(c, pilot, w, lambda got: got == "night", frames=20)
        ok &= check("with nobody at the desk, no line beside the pad either",
                    t is not None and not pilot.line)
    return ok


def test_the_desk_talks_on_the_night_line_and_n_closes_it():
    print("talking at night")
    with Desk():
        w = World()
        model = Model([END, END])
        c, pilot, _ = sol(w, model)
        opened, _ = until(c, pilot, w, lambda got: pilot.line)
        model.replies += [("Understood: east first.", [call("remember", text="east")]),
                          END]
        ok = check("the desk speaks", pilot.say(c, "tomorrow, go east first"))
        ok &= check("as the operator, not urgent", c.turn_by == "you")
        t, got = until(c, pilot, w, lambda got: got == "night", start=opened + 1, frames=5)
        ok &= check("her end on the line hands back rather than rolling the night",
                    t is None and pilot.line == "night" and w.notes.memory == "east")
        pilot.hang_up()
        t, _ = until(c, pilot, w, lambda got: got == "night", start=opened + 10, frames=2)
        ok &= check("N closes it at once, well inside COMMS_WAIT", t is not None)
    return ok


def test_urgent_stops_her_after_the_call_in_hand():
    print("U, mid-drive")
    with Desk():
        w = World()
        model = Model([("", [call("goto", x=15, y=12)]),
                       ("", [call("goto", x=18, y=12)])])     # what she would do next
        rover = [True]
        c, pilot, rows = sol(w, model, rover)
        pilot.tick(c, w, now=0.0)                   # the morning turn goes out
        rover[0] = False                            # ...and the rover drives its leg
        c.pump()
        ok = check("one drive ran, the next request is held for the rover",
                   len(c.calls) == 1 and c.waiting)
        ok &= check("U gets through from away from the pad",
                    not w.docked and pilot.talk(c, w, urgent=True, now=1.0) is None)
        rover[0] = True
        c.pump()
        ok &= check("and she stopped after that call: nothing more was asked",
                    len(model.sent) == 1 and len(c.calls) == 1 and not c.waiting,
                    f"{len(model.sent)} sent")
        model.replies = [("Heading home.", [call("goto", x=15, y=14)]), END]
        pilot.say(c, "return to the pad now")
        c.pump()
        ok &= check("the desk's first word is marked urgent, to her and on the tape",
                    c.turn_by == "urgent" and c.messages[-1]["role"] != "user"
                    and any(str(m.get("content", "")).startswith("URGENT")
                            for m in c.messages))
        t, _ = until(c, pilot, w, lambda got: pilot.line is None, start=2, frames=5)
        ok &= check("her end hands back: the line stays open, the sol goes on",
                    t is None and not w.day_over)
        pilot.hang_up()
        until(c, pilot, w, lambda got: pilot.line is None, start=10, frames=2)
        until(c, pilot, w, lambda got: said_by(c, "auto")[-1:] != said_by(c, "auto")[:1],
              start=12, frames=2)
        ok &= check("closed, the clock has the sol back and tells her",
                    "line to mission control is closed" in said_by(c, "auto")[-1])
        t, _ = until(c, pilot, w, lambda got: w.day_over, start=14, frames=5)
        ok &= check("and her own end closes the sol again", t is not None and
                    [r["why"] for r in rows if r["kind"] == "sol_closed"]
                    == ["she called end"])

    # Mid-request: the reply that was already coming runs its one call, then stops.
    w = World()
    c = chat.Conversation(w)
    asked = []
    c._want = lambda: asked.append(1)
    c.busy = True
    c.cut()
    c._t0 = chat.time.monotonic()
    c.q.put(("done", ({"prompt_eval_count": 1, "eval_count": 1},
                      [call("goto", x=15, y=12)])))
    c.pump()
    ok &= check("cut mid-request: the call in hand ran and nothing more was asked",
                [x.name for x in c.calls] == ["goto"] and not asked and c.ended)
    return ok


def test_her_calls_to_the_desk():
    print("radio and sos")
    w = World()
    c = chat.Conversation(w)
    with Desk():
        ok = check("beside the pad she is offered radio and sos",
                   w.docked and {"radio", "sos"} <= set(c._allowed()))
        w.pos = (3, 3)
        ok &= check("away from it, sos only", "sos" in c._allowed()
                    and "radio" not in c._allowed())
    with Desk(on=False):
        ok &= check("with nobody at the desk, neither",
                    not {"radio", "sos"} & set(c._allowed()))
    with Desk():
        w = World()
        w.pos = (3, 3)
        model = Model([("", [call("radio", text="anyone?")]),       # no link out here
                       ("", [call("sos", text="a wheel is stuck")]), END])
        c, pilot, rows = sol(w, model)
        opened, _ = until(c, pilot, w, lambda got: pilot.line)
        ok &= check("radio away from the pad does not get through, and her turn goes on",
                    c.calls[0].result.startswith("NO_LINK") and c.calls[1].name == "sos")
        ok &= check("her sos opens the line", pilot.line == "sos"
                    and any(r["kind"] == "sos" and r["text"] == "a wheel is stuck"
                            for r in rows))
        t, _ = until(c, pilot, w, lambda got: pilot.line is None, start=opened + 1)
        ok &= check("nobody answers: after COMMS_WAIT it closes", t is not None
                    and t - opened >= S.COMMS_WAIT, str(t))
        until(c, pilot, w, lambda got: w.day_over, start=t + 1, frames=5)
        ok &= check("and she carries on, told the line is closed",
                    "line to mission control is closed" in said_by(c, "auto")[1])
    return ok


def test_when_the_desk_can_and_cannot_reach_her():
    print("TAB and U, refused out loud")
    w = World()
    c = chat.Conversation(w)
    with Desk(on=False):
        pilot = autopilot.Autopilot()
        ok = check("comms off: refused, and says how to turn them on",
                   "C turns them on" in (pilot.talk(c, w) or ""))
    with Desk():
        pilot = autopilot.Autopilot()
        w.pos = (3, 3)
        ok &= check("away from the pad, TAB is refused and points at U",
                    "U" in (pilot.talk(c, w) or "") and not pilot.line)
        pilot.phase = "dusk"
        ok &= check("once the sol is over, U is refused too",
                    "sol is over" in (pilot.talk(c, w, urgent=True) or ""))
        pilot = autopilot.Autopilot()
        w = World()
        c = chat.Conversation(w)
        ok &= check("beside the pad by day, TAB opens the line",
                    w.docked and pilot.talk(c, w) is None and pilot.line == "pad")
        tape = autopilot.Autopilot(live=False)
        ok &= check("a replay never opens one", tape.talk(c, w, urgent=True)
                    and not tape.open_line(c, "urgent"))
    return ok


def test_the_desk_leaving_mid_sol_tells_her():
    print("C, mid-sol")
    with Desk():
        w = World()
        c = chat.Conversation(w)
        S.COMMS = False
        prompts.use(prompts.DEFAULT)
        c.send("carry on", who="auto")
        ok = check("her prompt now says nobody is at the desk",
                   "Nobody is at mission control's desk" in c.messages[0]["content"])
        ok &= check("and she was told at her next turn",
                    any("left the desk" in str(m["content"]) for m in c.messages))
        ok &= check("and sos is no longer offered", "sos" not in c._allowed())
    return ok


def test_a_replay_of_an_urgent_call_matches():
    """An urgent call cut a turn with no `end` in it. With two drives a turn, the replay
    only agrees if it ends that turn where the live one ended."""
    print("replay: an urgent call")
    keep = S.MOVE_HOPS
    S.MOVE_HOPS = 2
    try:
        with Desk(sols=1), tempfile.TemporaryDirectory() as d:
            tape = chat.Tape(Path(d) / "chat.jsonl")
            w = World()
            model = Model([("", [call("goto", x=15, y=12)]),
                           ("", [call("goto", x=18, y=12)]),
                           ("", [call("goto", x=15, y=10)]), END, END, END])
            rover = [True]
            c = model.talk(chat.Conversation(w, tape))
            c.ready = lambda: rover[0]
            c.open_day(w)
            pilot = autopilot.Autopilot()
            pilot.tick(c, w, now=0.0)
            rover[0] = False
            c.pump()
            pilot.talk(c, w, urgent=True, now=1.0)
            rover[0] = True
            pilot.say(c, "two more drives, then hand back")
            c.pump()
            pilot.hang_up()
            until(c, pilot, w, lambda got: got == "night", start=2, frames=40)
            tape.close()
            live = [(x.name, x.result) for x in c.calls if x.name != "end"]
            w2 = World()
            r = replay.Replay(w2, replay.Script(Path(d)))
            r.open_day(w2)
            until(r, autopilot.Autopilot(live=False), w2,
                  lambda got: got == "night" or r.diverged, frames=60)
    finally:
        S.MOVE_HOPS = keep
    ok = check("live: three drives ran, across the cut", len(live) == 3, str(live))
    ok &= check("the replay ran them to the same results", not r.diverged and
                [(x.name, x.result) for x in r.calls if x.name != "end"] == live,
                str(r.diverged))
    ok &= check("and ended where the live rover did", w2.pos == w.pos)
    return ok


if __name__ == "__main__":
    results = [test_the_clock_opens_the_sol(),
               test_her_end_closes_the_sol_and_dusk_asks_for_the_note(),
               test_a_cut_off_turn_is_carried_on(),
               test_an_end_the_drive_cap_asked_for_does_not_close_the_sol(),
               test_an_end_the_looks_cap_asked_for_does_not_close_the_sol(),
               test_nobody_is_ever_told_to_hand_back(),
               test_a_planner_that_never_ends_cannot_hold_the_sol(),
               test_running_out_of_time_closes_the_sol(),
               test_a_dropped_connection_is_asked_again_not_counted(),
               test_the_cloud_drops_for_a_sol_and_comes_back(),
               test_three_sols_with_no_key_pressed(),
               test_the_prompt_says_who_closes_the_sol_and_who_can_be_reached(),
               test_in_a_replay_the_tape_says_where_a_sol_ends(),
               test_the_clock_warns_about_a_stranding(),
               test_thinking_runs_the_clock_and_the_tape_keeps_it(),
               test_a_replay_runs_on_the_tapes_clock(),
               test_flat_away_from_the_pad_ends_the_mission(),
               test_a_replay_keeps_each_sols_calls_to_that_sol(),
               test_a_drive_at_dusk_replays_as_refused(),
               test_a_turn_the_cap_ended_replays_as_two(),
               test_the_night_line_opens_beside_the_pad_and_waits(),
               test_no_line_away_from_the_pad_or_with_nobody_at_the_desk(),
               test_the_desk_talks_on_the_night_line_and_n_closes_it(),
               test_urgent_stops_her_after_the_call_in_hand(),
               test_her_calls_to_the_desk(),
               test_when_the_desk_can_and_cannot_reach_her(),
               test_the_desk_leaving_mid_sol_tells_her(),
               test_a_replay_of_an_urgent_call_matches()]
    print(f"\n{sum(results)}/{len(results)} groups passed")
    sys.exit(0 if all(results) else 1)
