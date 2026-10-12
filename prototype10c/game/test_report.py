"""The mission report: the world's record first, her note after it as hers.

    .venv/bin/python game/test_report.py
"""

import sys

import report
import settings as S
import skills
from world import World

S.STORM_ON = False
S.DAY_MODE = "gemma"


def check(name, cond, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}{'   ' + detail if detail else ''}")
    return bool(cond)


def played():
    """Sol 1: objective 2 finished, then home. Sol 2: out on the plain."""
    w = World()
    skills.call(w, "goto", {"x": 8, "y": 19})
    w.execute(w.adjacent_objective())
    skills.call(w, "goto", {"x": 15, "y": 15})
    skills.call(w, "count", {"kind": "rock"})
    w.next_day()
    skills.call(w, "goto", {"x": 20, "y": 8})
    # The note she might write, wrong on purpose: the report must not take its word.
    w.notes.memory = "No objectives were found during the expedition."
    return w


def test_the_facts_come_from_the_world():
    print("facts")
    w = played()
    text = report.build(w)
    done = w.finished[0]
    ok = check("the finished objective is there, with its sol",
               f"- sol 1: {done['priority']} priority at ({done['at'][0]},{done['at'][1]})"
               in text, text[:400])
    ok &= check("the rest are listed as still out there",
                all(f"({o.cell[0]},{o.cell[1]})" in text.split("## Work still")[1]
                    for o in w.objectives if not o.done))
    seen = len(w.here.seen)
    ok &= check("the map is counted", f"{seen} of {w.here.w * w.here.h} cells seen" in text)
    ok &= check("and the largest formation seen, with its size",
                "Largest seen: 5 cells, middle (14,8)" in text, text.split("## The map")[1][:300])
    ok &= check("each sol's ending is a row: home on sol 1, out on sol 2",
                "| 1 |" in text and "beside the pad" in text and "| 2 |" in text)
    return ok


def test_her_note_is_hers():
    print("the note")
    text = report.build(played())
    note = text.split("## The planner's note")[1]
    ok = check("her note is under its own heading, marked unchecked",
               "not checked against the record" in note
               and "No objectives were found" in note)
    ok &= check("and only there: the record above says otherwise",
                "No objectives were found" not in text.split("## The planner's note")[0])
    return ok


def test_writing_it_changes_nothing():
    """`count` hands out formation ids and reports merges, and replay compares what it
    says. A report that assigned ids would change her next count."""
    print("read-only")
    w = played()
    sv = w.survey
    before = (dict(sv.owner), dict(sv.size), list(sv.merges), sv._next)
    report.build(w)
    return check("the survey is untouched",
                 before == (dict(sv.owner), dict(sv.size), list(sv.merges), sv._next))


def test_a_lost_rover_says_so():
    print("lost")
    w = World()
    w.pos, w.battery, w.day_over = (3, 3), 2, True
    return check("the ending says lost", "was lost on sol 1" in report.build(w))


if __name__ == "__main__":
    results = [test_the_facts_come_from_the_world(), test_her_note_is_hers(),
               test_writing_it_changes_nothing(), test_a_lost_rover_says_so()]
    print(f"\n{sum(results)}/{len(results)} groups passed")
    sys.exit(0 if all(results) else 1)
