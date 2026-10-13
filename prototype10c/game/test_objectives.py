"""The work: going alongside it, paying for it, and what it costs to get wrong.

    .venv/bin/python game/test_objectives.py

The load-bearing one is `test_an_objective_is_not_completed_by_driving_over_it`. Make
objectives drivable and every one of them gets done for free on the way past, the sol
has no decision left in it, and nothing looks broken -- the same shape of failure as an
omniscient planner.

`test_priority_and_cost_can_disagree` is the other one. Tie the two together and the
right order is a column to read rather than a judgement to make, which is the whole
thing this prototype is trying to watch.
"""

import sys

import config as C
import nav
import settings as S
import sight
import skills
from world import World

# Clear skies unless a suite asks otherwise. The weather is real and shipped on,
# but it is a scenario, not terrain -- letting one drift across an arena would make
# every route assertion here depend on STORM_RADIUS. `test_hazards.py` turns it on.
S.STORM_ON = False


def check(name, cond, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}{'   ' + detail if detail else ''}")
    return bool(cond)


def _at(w, o):
    """Put the rover beside `o` without spending the day getting there."""
    x, y = o.cell
    for cell in ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)):
        if not w.here.blocked(*cell):
            w.pos = cell
            w.here.reveal(*cell)
            return cell
    raise AssertionError(f"{o.cell} has no open cell beside it")


def test_an_objective_is_not_completed_by_driving_over_it():
    print("you have to stop and do the work")
    w = World()
    o = w.objectives[0]
    ok = check("it is solid, so a route cannot pass through it",
               w.here.blocked(*o.cell))
    # `goto` at a solid thing stops beside it and calls that arriving -- the base pad's
    # rule, reused rather than reinvented.
    r = nav.goto(w, *o.cell)
    ok &= check("goto stops beside it rather than on it",
                r.code == "DONE" and w.pos != o.cell, f"{r} pos={w.pos}")
    ok &= check("...and says so, because beside= alone reads as a failure",
                "IS arriving" in r.advice, r.advice)
    ok &= check("arriving did not do the work", not o.done and o.cell in w.here.objectives)
    ok &= check("...and cost nothing beyond the drive", w.steps == r.steps)
    return ok


def test_the_work_is_paid_for_once_and_the_objective_goes():
    print("execute")
    w = World()
    o = w.objectives[0]
    _at(w, o)
    before = w.steps
    c = skills.call(w, "execute", {"why": "it is the high one"})
    ok = check("it succeeds", c.result.startswith("EXECUTED"), c.result[:80])
    ok &= check("...and charges exactly the objective's cost",
                w.steps - before == o.cost, f"{w.steps - before} for a {o.cost}-step job")
    ok &= check("the objective is off the map", o.cell not in w.here.objectives)
    ok &= check("...so the cell is drivable again", not w.here.blocked(*o.cell))
    # Doing the work reveals nothing, so without this the sol's whole purpose reads to
    # `_stuck` as steps that bought nothing.
    ok &= check("work counts as gain, or the scold fires on the mission itself",
                c.gained > 0)

    again = skills.call(w, "execute", {})
    ok &= check("a second call has nothing to do there",
                again.result.startswith(("NOT_BESIDE_ONE", "NOTHING_TO_DO")),
                again.result[:60])
    ok &= check("...and spends nothing", again.steps == 0)
    return ok


def test_refusing_says_where_the_work_is():
    print("refusals carry the map she has, and no more")
    w = World()
    c = skills.call(w, "execute", {"why": "from the pad"})
    ok = check("standing nowhere near one, it refuses",
               c.result.startswith("NOT_BESIDE_ONE"), c.result[:60])
    ok &= check("nothing was spent", c.steps == 0 and not w.day_over)
    ok &= check("with none found, it names none",
                not any(f"({o.cell[0]},{o.cell[1]})" in c.result for o in w.objectives),
                c.result[:160])
    seen, *fogged = w.objectives
    w.here.reveal(*seen.cell)
    c = skills.call(w, "execute", {})
    # A code with no sentence after it is what `DONE(beside=...)` cost four days.
    ok &= check("...it names the one she has seen, with its cost",
                f"({seen.cell[0]},{seen.cell[1]}), {seen.cost} steps" in c.result,
                c.result[:160])
    ok &= check("...and none still under the fog",
                not any(f"({o.cell[0]},{o.cell[1]})" in c.result for o in fogged))
    _at(w, fogged[0])
    c = skills.call(w, "execute", {})
    ok &= check("doing one names only the found ones left",
                c.result.startswith("EXECUTED")
                and f"({seen.cell[0]},{seen.cell[1]})" in c.result
                and not any(f"({o.cell[0]},{o.cell[1]})" in c.result for o in fogged[1:]),
                c.result[:200])
    return ok


def test_priority_and_cost_can_disagree():
    print("the two axes")
    ok = True
    for name in ("30", "50"):
        C.use(name)
        w = World()
        by_priority = [o.priority for o in w.objectives]
        costs = [o.cost for o in w.objectives]
        ok &= check(f"{name}: every priority is on the map", set(by_priority) ==
                    {"high", "medium", "low"}, str(by_priority))
        # If the cheapest were also the highest priority there would be nothing to
        # weigh: the order would fall out of either column on its own.
        cheapest = min(w.objectives, key=lambda o: o.cost)
        ok &= check(f"{name}: the cheapest job is not the most important one",
                    cheapest.priority != "high",
                    f"cheapest is {cheapest.priority} at {cheapest.cost}")
        ok &= check(f"{name}: the costs actually differ", len(set(costs)) == len(costs),
                    str(costs))
    C.use(C.DEFAULT_ARENA)
    return ok


def test_objectives_are_found_rather_than_given():
    print("they sit in the fog")
    w = World()
    ok = check("none is visible from the landing site",
               not any(w.here.visible(*o.cell) for o in w.objectives))
    ok &= check("...so the view lists none of them yet", not sight.objectives(w))
    ok &= check("...and says so rather than showing an empty heading",
                "not found any objectives yet" in sight.view(w))

    o = w.objectives[0]
    w.here.reveal(*o.cell, r=1)
    lines = sight.objectives(w)
    ok &= check("once seen it is listed", len(lines) == 1, str(lines))
    ok &= check("...with its coordinate, priority and cost",
                all(s in lines[0] for s in
                    (f"({o.cell[0]},{o.cell[1]})", o.priority, str(o.cost))), lines[0])
    ok &= check("...and it appears under a heading the view can be cut back to",
                "OBJECTIVES YOU HAVE FOUND" in sight.view(w))
    return ok


def test_the_environment_does_not_rank_them():
    print("the ranking stays with the model")
    w = World()
    for o in w.objectives:
        w.here.reveal(*o.cell, r=1)
    lines = sight.objectives(w)
    ok = check("all three are listed", len(lines) == 3, str(len(lines)))
    # The order is the order config wrote them, not sorted by anything. Handing over a
    # sorted list answers the question the prototype exists to ask.
    ok &= check("...in the order the arena declares, not by priority or cost",
                [l.split()[0] for l in lines] == [o.priority for o in w.objectives],
                str([l.split()[0] for l in lines]))
    blob = " ".join(lines) + skills.call(w, "execute", {}).result
    for word in ("best", "nearest", "should", "recommend", "first"):
        ok &= check(f"nothing says {word!r}", word not in blob.lower())
    return ok


def test_a_battery_that_runs_flat_mid_task_still_pays_for_what_it_used():
    print("running flat is not a refund")
    w = World()
    o = w.objectives[0]
    _at(w, o)
    w.battery = 5                      # five steps of charge left, a 40-step job
    c = skills.call(w, "execute", {})
    ok = check("it does not finish", not o.done and o.cell in w.here.objectives)
    ok &= check("...says the battery ran flat", c.result.startswith("UNFINISHED")
                and "battery ran flat" in c.result, c.result[:90])
    ok &= check("...and the charge is gone", w.battery == 0 and c.steps == 5,
                f"{c.steps} spent, {w.battery} left")

    over = skills.call(w, "execute", {})
    ok &= check("flat, it refuses outright",
                over.result.startswith("BATTERY_FLAT"), over.result[:60])
    ok &= check("...and spends nothing", over.steps == 0)
    return ok


def test_a_sol_that_runs_out_mid_task_still_pays_for_what_it_used():
    print("the sol ending is not a refund")
    w = World()
    o = w.objectives[0]
    _at(w, o)
    w.charge(w.time_left - 5 * S.STEP_SECONDS)     # time for five steps, a 40-step job
    before = w.battery
    c = skills.call(w, "execute", {})
    ok = check("it does not finish", not o.done and o.cell in w.here.objectives)
    ok &= check("...says the sol ran out", c.result.startswith("UNFINISHED")
                and "sol ran out" in c.result, c.result[:90])
    ok &= check("...and five steps of charge went on it",
                c.steps == 5 and w.battery == before - 5 and w.day_over,
                f"{c.steps} spent, battery {w.battery}")

    over = skills.call(w, "execute", {})
    ok &= check("with the sol over it refuses outright",
                over.result.startswith("OUT_OF_TIME"), over.result[:60])
    ok &= check("...and spends nothing", over.steps == 0)
    return ok


def test_the_arena_survives_them_being_solid():
    print("no objective seals a corridor")
    ok = True
    for name in ("30", "50"):
        C.use(name)
        w = World()
        w.here.reveal_all()
        # Every objective must still be reachable with all the others standing, or one
        # of them is walled in by the rest and the sol cannot be finished.
        for o in w.objectives:
            path = nav.plan(w.here, C.SPAWN, o.cell)
            ok &= check(f"{name}: {o.priority} at {o.cell} can be reached",
                        path is not None and path[-1] != o.cell, str(path and path[-1]))
    C.use(C.DEFAULT_ARENA)
    return ok


if __name__ == "__main__":
    results = [test_an_objective_is_not_completed_by_driving_over_it(),
               test_the_work_is_paid_for_once_and_the_objective_goes(),
               test_refusing_says_where_the_work_is(),
               test_priority_and_cost_can_disagree(),
               test_objectives_are_found_rather_than_given(),
               test_the_environment_does_not_rank_them(),
               test_a_battery_that_runs_flat_mid_task_still_pays_for_what_it_used(),
               test_a_sol_that_runs_out_mid_task_still_pays_for_what_it_used(),
               test_the_arena_survives_them_being_solid()]
    print(f"\n{sum(results)}/{len(results)} groups passed")
    sys.exit(0 if all(results) else 1)
