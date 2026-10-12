"""Quit, come back, and wake on the next sol as though the night had passed.

    .venv/bin/python game/test_resume.py

The whole claim is one comparison: a world rebuilt from `carry()` must be the world
`next_day` would have produced, down to the view the model is sent.
"""

import json
import sys
import tempfile
from pathlib import Path

import config as C
import logs
import replay
import settings as S
import sight
import skills
from world import World

S.STORM_ON = True       # the storm is reseeded by sol, so a resumed sol must get the same one


def check(name, cond, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}{'   ' + detail if detail else ''}")
    return bool(cond)


def played():
    """A sol with something in every store the night keeps."""
    w = World()
    skills.call(w, "goto", {"x": 8, "y": 19})
    o = w.adjacent_objective()
    assert o and o.cell == (8, 20), f"the rover is not beside objective 2: {w.pos}"
    w.execute(o)
    for x, y in ((20, 8), (25, 25)):
        skills.call(w, "goto", {"x": x, "y": y})
    skills.call(w, "count", {"kind": "rock"})
    w.place_objective((21, 22), "high", 40)
    w.toggle_mark((3, 3))
    w.notes.add("an item the night wipes")
    w.notes.memory = "the C opens east"
    w.notes.order("finish objective 1")
    return w


def roundtrip(w):
    return json.loads(json.dumps(w.carry()))


def same(a, b):
    """Every piece of state the next sol can see."""
    return {
        "view": sight.view(a) == sight.view(b),
        "day": a.day == b.day,
        "pos": a.pos == b.pos,
        "seen": a.here.seen == b.here.seen,
        "visited": a.here.visited == b.here.visited,
        "marks": a.here.marks == b.here.marks,
        "objectives": {c: (o.glyph, o.priority, o.cost) for c, o in a.here.objectives.items()}
                      == {c: (o.glyph, o.priority, o.cost) for c, o in b.here.objectives.items()},
        "survey": (a.survey.owner, a.survey.size, a.survey._next)
                  == (b.survey.owner, b.survey.size, b.survey._next),
        "storm": a.here.storm_cells == b.here.storm_cells,
        "notes": (a.notes.memory, a.notes.orders, a.notes.todos)
                 == (b.notes.memory, b.notes.orders, b.notes.todos),
        "history": a.history == b.history,
    }


def test_a_resumed_world_is_the_one_that_slept():
    print("resume = next_day")
    w = played()
    kept = roundtrip(w)
    slept = w
    slept.next_day()
    woke = World(carried=kept)
    diff = [k for k, v in same(slept, woke).items() if not v]
    ok = check("identical, view included", not diff, str(diff))
    ok &= check("on the next sol", woke.day == 2)
    ok &= check("the finished objective stays finished", (8, 20) not in woke.here.objectives)
    ok &= check("the placed one is still there", (21, 22) in woke.here.objectives)
    ok &= check("the list did not survive", woke.notes.todos == [])

    # Twice over: a resumed sol carries again like any other.
    skills.call(woke, "goto", {"x": 2, "y": 2})
    skills.call(slept, "goto", {"x": 2, "y": 2})
    again = World(carried=roundtrip(woke))
    slept.next_day()
    diff = [k for k, v in same(slept, again).items() if not v]
    ok &= check("and a second night the same way", not diff and again.day == 3, str(diff))
    return ok


def test_the_wrong_arena_is_refused():
    print("the map belongs to its arena")
    kept = roundtrip(World())
    C.use("50")
    try:
        World(carried=kept)
        refused = False
    except ValueError:
        refused = True
    finally:
        C.use(C.DEFAULT_ARENA)
    return check("a 30 resumed on the 50 is an error, not a scrambled map", refused)


def test_a_replay_of_a_resumed_run_starts_where_it_did():
    print("replay")
    with tempfile.TemporaryDirectory() as d:
        run = Path(d)
        (run / "start.json").write_text(json.dumps(roundtrip(played())))
        (run / "chat.jsonl").write_text("")
        (run / "game.jsonl").write_text(
            json.dumps({"kind": "settings", "sol": 2, "values": {"DAY_STEPS": 140}}))
        script = replay.Script(run)
        keep = S.DAY_STEPS
        try:
            ok = check("it knows the state it began from", script.start["day"] == 1)
            ok &= check("and its first sol", script.first_sol == 2)
            script.use_settings(script.first_sol)
            ok &= check("whose settings it takes", S.DAY_STEPS == 140)
        finally:
            S.DAY_STEPS = keep
    return ok


def test_the_night_is_written_down():
    print("on disk")
    with tempfile.TemporaryDirectory() as d:
        run = logs.Run(Path(d), stamp="20261011-120000")
        w = played()
        run.save_night(w)
        ok = check("night.json is written while the run is still pending",
                   (run.dir / "night.json").exists())
        kept = run.keep()
        back = logs.load_night(kept)
        ok &= check("and read back from the kept run", back["memory"] == "the C opens east")
        ok &= check("a directory with no night says so",
                    _raises(lambda: logs.load_night(Path(d))))
    return ok


def _raises(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    results = [t() for t in tests]
    print(f"\n{sum(results)}/{len(results)} groups passed")
    sys.exit(0 if all(results) else 1)
