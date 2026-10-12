"""Run me:  .venv/bin/python game/main.py [--arena 30|50] [--map grid|rle] [--sols N]
                                        [--model TAG] [--think] [--replay runs/<stamp>]

WASD drive (hold to keep going)   M map   X mark   T console
TAB talk to the planner   V what it sees   H hide/show its reasoning
O settings   P show/hide the scratchpad
N next sol (once one has ended)   Q end the sol   ESC quit
SPACE the rover has finished the leg -- pressed at every pause

Settings come from `registry.py`: the code's defaults, then `user_settings.json`, then
flags for this launch. README.md says when each kind of change lands.

A Martian plain, a landing pad at the centre, and gemma in the pane on the right. The
rover maps what it drives past, out to `VISION_RADIUS`, and that is the only thing that
lifts fog -- Ingenuity is cut, so a sol of driving is the only way the map fills in.

**Three things are written down, and they differ by who holds the pen.** She keeps a
list for today that `todo` adds to and `strike` crosses off, wiped at nightfall, and one
note that `remember` rewrites and the night does not take. The third is the operator's,
typed at TAB and read-only to her:

    /orders finish objective 3 today      her standing job. Stands until replaced;
                                          `/orders` alone clears it
    /place 21 8 high 40                   work put on the map: cell, priority, cost.
                                          Refused if the rover could never reach it
    /status                               the status line, as she reads it

**Live and replay.** Live, the model decides. `--replay` re-issues a kept run's calls
with no model in the loop and halts if the world stops matching the tape -- so a sol
that came out well is the demo, played back exactly. `replay.py` says why.

No human-only mode: the planner is the point.
"""

import argparse
import hashlib
import pathlib
import sys
import time

import pygame

import anim
import chat
import prompts
import config as C
import console
import logs
import nav
import registry
import render
import replay
import settings as S
import sight
from world import World

DIRS = {pygame.K_w: (0, -1), pygame.K_s: (0, 1), pygame.K_a: (-1, 0), pygame.K_d: (1, 0),
        pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_LEFT: (-1, 0),
        pygame.K_RIGHT: (1, 0)}


def read_flags(argv, prefs):
    """Puts every setting in force before anything reads one.

    Returns (args, script, carried): `carried` is the night a resumed run wakes from.

    The order is the precedence: the code's defaults, then the person's saved settings,
    then flags for this launch only, then -- on a replay -- the kept run's own values,
    which win because a replay under different settings is a different run.

    `--think` sets the trace and the sampler together, because a reasoning trace that
    starts repeating at temperature 0 has no noise to climb out with.
    """
    p = argparse.ArgumentParser(prog="game/main.py")
    p.add_argument("--map", choices=("grid", "rle"),
                   help="how the map is written into the view")
    p.add_argument("--arena", choices=tuple(C.ARENAS), help="which arena to land on")
    p.add_argument("--prompt", choices=tuple(prompts.PROMPTS), default=prompts.DEFAULT,
                   help=f"which system prompt to run (default: {prompts.DEFAULT})")
    p.add_argument("--model", help="any tag `ollama list` shows, or a `-cloud` one")
    p.add_argument("--executor", choices=("teleport", "plan"),
                   help="what a goto does; 'plan' writes the route and moves nothing")
    p.add_argument("--think", action="store_true",
                   help="reasoning trace on, and the sampler left to the model")
    p.add_argument("--pause", choices=("key", "none"),
                   help="who says the rover finished a leg; 'key' is SPACE at every pause")
    p.add_argument("--sols", type=int, help="sols in the mission; 0 is no limit")
    p.add_argument("--replay", metavar="RUN_DIR",
                   help="re-issue a kept run's calls with no model in the loop")
    p.add_argument("--resume", metavar="RUN_DIR",
                   help="carry on a kept run's expedition from the sol after it stopped")
    args = p.parse_args(argv)
    if args.replay and args.resume:
        p.error("--replay and --resume are two different runs; pick one")

    prefs.apply_all()
    for w in prefs.warnings:
        print("settings:", w)
    flags = {"MAP_FORMAT": args.map, "APP_ARENA": args.arena, "MODEL": args.model,
             "EXECUTOR": args.executor, "ROVER_PAUSE": args.pause,
             "MISSION_SOLS": args.sols}
    bad = registry.apply({k: v for k, v in flags.items() if v is not None})
    if bad:
        p.error(f"out of range: {', '.join(bad)}")
    if args.think:
        S.MODEL_THINK = True
        S.MODEL_TEMP = None

    # Loaded before pygame opens a window: a run directory that is missing or has no
    # calls in it should say so at the prompt, not behind a window that then closes.
    script = replay.load(pathlib.Path(args.replay)) if args.replay else None
    if script:
        script.use_settings(script.first_sol)
    carried = script.start if script else None
    if args.resume:
        try:
            carried = logs.load_night(pathlib.Path(args.resume))
        except ValueError as e:
            p.error(str(e))
    if carried:
        # The map belongs to the arena it was drawn on, whatever is saved or flagged.
        registry.apply({"APP_ARENA": carried["arena"]})

    # Before anything reads `config` -- the window is sized off it and so is the world.
    C.use(C.APP_ARENA)
    # Last: the prompt is built from the arena, the map format and the turn caps.
    prompts.use(args.prompt)
    return args, script, carried


def main():
    prefs = registry.Prefs()
    args, script, carried = read_flags(sys.argv[1:], prefs)
    pygame.init()

    def title():
        """The map format is here because nothing else on screen tells the two arms
        apart. Rewritten at nightfall, when the model or the format may change."""
        pygame.display.set_caption(
            f"Reflex Arc -- prototype 10b  ·  {C.VIEW_W}x{C.VIEW_H}  ·  {S.MAP_FORMAT} map"
            + (f"  ·  replay of {pathlib.Path(args.replay).name}" if args.replay else
               f"  ·  {S.MODEL}")
            + ("  ·  thinking" if S.MODEL_THINK else ""))

    title()
    # Before anything asks how big anything is: every other size is derived from
    # C.TILE and S.CHAT_W, so this has to run ahead of set_mode and the subsurfaces.
    render.fit_to_display()
    screen = pygame.display.set_mode(render.window_size())
    clock = pygame.time.Clock()
    fonts = render.Fonts()

    # The arena draws into a subsurface its own size, so every overlay fills exactly
    # the half it was written for and the pane beside it is never painted over.
    gw, gh = render.game_size()
    game = screen.subsurface(pygame.Rect(0, 0, gw, gh))
    pane = screen.subsurface(pygame.Rect(gw, 0, S.CHAT_W, gh))

    # The run starts recording immediately. Whether it is kept is asked at the end;
    # see logs.py for why that order and not the other one.
    runs = pathlib.Path(__file__).resolve().parent.parent / "runs"
    run = logs.Run(runs)

    def log_settings(sol):
        """Every setting in force, and a hash of the prompt they built, once a sol.
        Two runs of one probe once scored 22% and 56% and nothing on either tape said
        which prompt they had been asked under. Replay reads these rows back."""
        run.record("settings", sol=sol, values=registry.snapshot(),
                   prompt=hashlib.sha256(prompts.SYSTEM.encode()).hexdigest()[:12])

    w = World(recorder=run.record, carried=carried)
    if args.resume:
        run.save_start(carried, pathlib.Path(args.resume).resolve().name)
    elif script and script.start:
        run.save_start(script.start, pathlib.Path(args.replay).resolve().name)
    log_settings(w.day)
    nav.clear_plan(w)   # this session's route file starts empty, never yesterday's
    tape = chat.Tape(run.chat_path)

    def talker():
        """The thing on the other end of the pane: Ollama, or a kept run.

        One function so the two construction sites below cannot drift -- a replay whose
        second sol quietly went back to asking the model would be the hardest kind of
        wrong to see, because it would look exactly right until the bill arrived.
        """
        if script:
            return replay.Replay(w, script, tape)
        return chat.Conversation(w, tape)

    conv = talker()
    conv.open_day(w)

    reel = anim.Reel(w)
    # **The planner waits for the rover.** No request goes out while a drive is still
    # being drawn, so gemma sees the outcome of one call before it can make the next.
    # It costs wall clock and that is the point: a planner seconds away from the body
    # it drives is the architecture, and here you can watch it happen.
    #
    # The rover also sits still for `SETTLE_SECONDS` after the drawing stops. A 31B
    # answers in under two seconds, so without a pause the sol is a burst of teleports
    # with nothing legible between them. `settle` holds the earliest moment the next
    # request may go out, and is pushed forward for as long as anything is moving.
    settle = [0.0]

    def ready():
        now = time.monotonic()
        if reel.busy:
            settle[0] = now + S.SETTLE_SECONDS
            return False
        return now >= settle[0]

    conv.ready = ready
    mode = "world"
    cursor = w.pos
    held = None
    next_step = 0
    line, history = "", []
    said, typing, scroll, scroll_max = "", False, 0, 0
    pad_open = True
    picked, editing, notice, models = 0, None, "", None
    items = [("preset", label) for label in registry.PRESETS] + \
            [("setting", st) for st in registry.SETTINGS]

    def leave(keep):
        run.record("quit", kept=keep, day=w.day, steps=w.steps,
                   seconds=round(w.elapsed, 1))
        if keep:
            run.save_night(w)
        tape.close()
        run.keep() if keep else run.discard()
        pygame.quit()
        sys.exit()

    def place(world, text):
        """`/place X Y [high|medium|low] [cost]` -- work put on the map at nightfall.

        Priority and cost default to medium and 30, which is a crossing of the 30 and
        therefore the objective that is worth exactly one sol's travelling. Both are
        facts mission control hands over, so both are the operator's to say.

        The refusal wording comes back from `world.place_objective` rather than being
        written again here: the guard and the explanation of the guard belong together,
        and this is a console that types them out.
        """
        words = text.split()
        nums = [t for t in words if t.lstrip("-").isdigit()]
        if len(nums) < 2:
            return "PLACE NEEDS A CELL -- try  /place 21 8 high 40"
        cell = (int(nums[0]), int(nums[1]))
        priority = next((t for t in words if t.lower() in ("high", "medium", "low")),
                        "medium")
        cost = int(nums[2]) if len(nums) > 2 else 30
        if cost <= 0:
            return f"PLACE REFUSED -- {cost} steps of work is not work."
        o, why = world.place_objective(cell, priority.lower(), cost)
        if not o:
            return f"PLACE REFUSED -- {why}"
        return (f"PLACED -- objective {o.glyph} at ({cell[0]},{cell[1]}), "
                f"{o.priority} priority, {o.cost} steps of work. It is under fog until "
                f"she drives to it.")

    def orders(world, text):
        """`/orders ...` -- mission control writes, and the line the operator sees back.

        Typed at nightfall, read every request after it, and never cleared by a sol
        rolling over. Refused rather than cut when it is too long, for the same reason
        `remember` is: truncating an instruction loses the end, which is where the thing
        actually being asked for tends to sit.

        It goes on the tape as its own event. A replay has to reissue it, and an order
        recovered by parsing the message log would be indistinguishable from the
        operator having simply said something.
        """
        text = text.strip()
        if len(text) > S.ORDERS_CHARS:
            return (f"ORDERS REFUSED -- {len(text)} characters, and the cap is "
                    f"{S.ORDERS_CHARS}. Nothing changed. Say it shorter.")
        world.notes.order(text)
        world.record("orders", text=text)
        if not text:
            return "ORDERS CLEARED -- she has no standing instruction now."
        return f"ORDERS SET -- she reads this on every call until it is replaced: {text}"

    def await_rover(world, dirs):
        """Hold everything until the operator says the rover has driven the leg.

        `nav.goto` runs on this thread -- `chat._run` is deliberately main-thread, so a
        drive cannot land halfway through a redraw -- which means waiting here stops the
        game loop, redraw and events included. So this runs its own: it draws each frame
        and reads the keyboard itself, and takes only the key that ends the wait. The
        world must not change while the robot is a leg behind it, and refusing every
        other key is what guarantees that rather than hoping nothing is pressed.

        The screen still shows the rover where it was before this `goto`: the drive is
        animated from `world.reel` once the call returns. On the floor the machine is
        moving, which is the thing actually worth watching, and the HUD says what it
        was sent.
        """
        if S.ROVER_PAUSE != "key":
            return
        world.awaiting_rover = list(dirs)
        asking = False      # ESC asks the same keep-or-discard question as anywhere else
        try:
            while True:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        asking = True
                    if e.type != pygame.KEYDOWN:
                        continue
                    if asking:
                        asking = answer_quit(e)
                    elif e.key == pygame.K_SPACE:
                        return
                    elif e.key == pygame.K_ESCAPE:
                        asking = True
                clock.tick(C.FPS)
                render.draw_world(game, w, fonts, reel)
                if asking:
                    render.draw_quit(game, w, fonts, run, mission_over())
                render.draw_chat(pane, conv, w, fonts, said, typing, scroll,
                                 S.SHOW_THINKING, reel, None, pad_open)
                pygame.display.flip()
        finally:
            world.awaiting_rover = None

    nav._await_rover = await_rover

    def mission_over():
        return bool(S.MISSION_SOLS) and w.day_over and w.day >= S.MISSION_SOLS

    def answer_quit(e):
        """K keeps the run, D discards it, ESC goes back. Returns whether still asking."""
        if e.key == pygame.K_k:
            leave(True)
        elif e.key == pygame.K_d:
            leave(False)
        return e.key != pygame.K_ESCAPE

    def nightfall():
        """The sol rolls over. Settings waiting for it go in force first, then the
        prompt is rebuilt from them, so the new sol's planner is told the new numbers.

        A replay does the operator's half itself, and does it *before* the rollover:
        orders typed at nightfall are what the next sol opens holding.
        """
        nonlocal conv
        notes = []
        if script:
            for done in script.operator(w, w.day):
                conv.write("status", f"operator, sol {w.day} -- {done}")
            script.use_settings(w.day + 1)
        else:
            changed = prefs.nightfall()
            notes = [f"{k} {registry.show(v)}" for k, v in changed.items()]
        prompts.use(args.prompt)
        run.save_night(w)     # a crash tomorrow still resumes from tonight
        w.next_day()
        log_settings(w.day)
        title()
        conv = talker()
        conv.ready = ready
        conv.open_day(w)
        if notes:
            conv.write("note", "settings from this sol: " + ", ".join(notes))

    def settings_key(e):
        """One key on the settings screen. Returns False when the screen closes."""
        nonlocal picked, editing, notice
        kind, it = items[picked]
        locked = bool(script) and (kind == "preset" or it.tier != "now")
        if editing is not None:
            if e.key == pygame.K_ESCAPE:
                editing = None
            elif e.key == pygame.K_RETURN:
                notice = change(it, editing)
                editing = None
            elif e.key == pygame.K_BACKSPACE:
                editing = editing[:-1]
            elif e.unicode and e.unicode.isprintable():
                editing += e.unicode
            return True
        if e.key in (pygame.K_ESCAPE, pygame.K_o):
            return False
        if e.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
            d = -1 if e.key in (pygame.K_UP, pygame.K_w) else 1
            picked, notice = (picked + d) % len(items), ""
        elif locked and e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d,
                                  pygame.K_RETURN, pygame.K_r):
            notice = "a replay runs on the kept run's settings; only 'now' ones change"
        elif kind == "preset" and e.key == pygame.K_RETURN:
            prefs.preset(it)
            notice = f"loaded {it}; each value lands on its own tier"
        elif kind == "setting" and e.key in (pygame.K_LEFT, pygame.K_a,
                                             pygame.K_RIGHT, pygame.K_d):
            d = -1 if e.key in (pygame.K_LEFT, pygame.K_a) else 1
            notice = change(it, it.nudge(prefs.shown(it), d))
        elif kind == "setting" and e.key == pygame.K_RETURN:
            editing = "" if prefs.shown(it) is None else str(prefs.shown(it))
        elif kind == "setting" and e.key == pygame.K_r:
            notice = change(it, it.default)
        return True

    def change(st, v):
        try:
            v = prefs.set(st.name, v)
        except ValueError as err:
            return f"{st.name} not changed: {err}"
        if st.name == "MODEL" and models is not None and v not in models:
            return f"{v} is not in `ollama list`; pull it before the next sol"
        return f"{st.name} {registry.show(v)} -- {registry.TIER_NAMES[st.tier]}"

    while True:
        dt = clock.tick(C.FPS) / 1000.0
        now = pygame.time.get_ticks()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                mode, typing, held = "quit", False, None
            if e.type == pygame.KEYUP and e.key == held:
                held = None
            if e.type == pygame.MOUSEWHEEL:
                scroll = max(0, min(scroll_max, scroll + e.y * 3))
            if e.type != pygame.KEYDOWN:
                continue

            # The quit question outranks everything, including the text field, or
            # closing the window while mid-sentence would type into it.
            if mode == "quit":
                if not answer_quit(e):
                    mode = "world"
                continue

            # Typing to gemma eats every key, the same way the console does.
            if typing:
                if e.key == pygame.K_ESCAPE:
                    typing = False
                elif e.key == pygame.K_RETURN:
                    text = said.strip()
                    if text == "/status":
                        conv.send(sight.status_line(w), who="status")
                    elif text.startswith("/place"):
                        conv.send(place(w, text[len("/place"):]), who="status")
                    elif text.startswith("/orders"):
                        # Mission control, not conversation. It goes to the store rather
                        # than the message log, because the log is cleared at nightfall
                        # and an order typed at nightfall would be the first thing lost.
                        # `/orders` alone clears them; that has to be possible or a
                        # survey sol can never follow a sol with an objective on it.
                        conv.send(orders(w, text[len("/orders"):]), who="status")
                    elif text:
                        conv.send(text)
                    said, scroll = "", 0
                elif e.key == pygame.K_BACKSPACE:
                    said = said[:-1]
                elif e.unicode and e.unicode.isprintable():
                    said += e.unicode
                continue

            # The console eats every key, or WASD would drive instead of typing.
            if mode == "console":
                # T closes only on an empty line, so "goto" and "distance" type fine.
                if e.key == pygame.K_ESCAPE or (e.key == pygame.K_t and not line):
                    mode, held, line = "world", None, ""
                elif e.key == pygame.K_RETURN:
                    if line.strip():
                        history.extend(console.run(w, line))
                        del history[:-40]
                    line = ""
                elif e.key == pygame.K_BACKSPACE:
                    line = line[:-1]
                elif e.unicode and e.unicode.isprintable():
                    line += e.unicode
                continue

            if mode == "settings":
                if not settings_key(e):
                    mode, editing = "world", None
                continue

            # Looking at the view eats every key, the way the console does, or the arrow
            # keys would drive the rover out from under the block being read.
            if mode == "view":
                if e.key in (pygame.K_v, pygame.K_ESCAPE):
                    mode, scroll = "world", 0
                continue

            if e.key in DIRS:
                held, next_step = e.key, now + S.MOVE_DELAY_MS
                if mode == "world":
                    # Taking the wheel cuts the replay short rather than fighting it
                    # for where the rover is drawn.
                    reel.skip()
                    w.move(*DIRS[e.key])
                else:
                    cursor = clamp_cursor(cursor, DIRS[e.key], w.here)

            elif mode == "world":
                if e.key == pygame.K_SPACE:
                    reel.skip()
                elif e.key == pygame.K_m:
                    mode, cursor = "map", w.pos
                elif e.key == pygame.K_x:
                    w.toggle_mark()
                elif e.key == pygame.K_t:
                    mode, held = "console", None
                elif e.key == pygame.K_q:
                    w.day_over = True
                elif e.key == pygame.K_TAB:
                    typing, held = True, None
                elif e.key == pygame.K_h:
                    S.SHOW_THINKING = not S.SHOW_THINKING
                    scroll = 0
                elif e.key == pygame.K_p:
                    pad_open = not pad_open
                elif e.key == pygame.K_o:
                    mode, held, notice = "settings", None, ""
                    models = chat.installed_models()
                    registry.BY_NAME["MODEL"].choices = models
                # You start the sol, not the loop. The old conversation is dropped here
                # rather than carried, so anything gemma wanted to keep had to be said
                # while the sol it belonged to was still open. Carrying it is item 7.
                elif e.key == pygame.K_n and w.day_over and not mission_over():
                    nightfall()
                    scroll = 0
                # V overlays the view block; V again puts it away. A thing you open to
                # look at is a mode, not a message -- appending it instead once put
                # twenty-two copies of four thousand characters into one tape. Nothing is
                # written down here: every view gemma was sent is already a `view` row.
                elif e.key == pygame.K_v:
                    mode, scroll = "view", 0
                elif e.key == pygame.K_ESCAPE:
                    mode, held = "quit", None

            elif mode == "map":
                if e.key == pygame.K_x:
                    w.toggle_mark(cursor)
                elif e.key in (pygame.K_m, pygame.K_ESCAPE):
                    mode = "world"

        # hold-to-drive repeat
        if held and now >= next_step and not typing:
            keys = pygame.key.get_pressed()
            if keys[held]:
                next_step = now + S.MOVE_REPEAT_MS
                if mode == "world":
                    w.move(*DIRS[held])
                elif mode == "map":
                    cursor = clamp_cursor(cursor, DIRS[held], w.here)
            else:
                held = None

        if mode == "world":
            w.tick(dt)
        reel.tick(dt)

        render.draw_world(game, w, fonts, reel)
        if mode == "map":
            render.draw_map(game, w, fonts, cursor)
        elif mode == "console":
            render.draw_console(game, w, fonts, line, history)
        elif mode == "quit":
            render.draw_quit(game, w, fonts, run, mission_over())

        # Pumped every frame now: the hold lives in `conv.ready` above, which stops the
        # next *request* rather than the whole loop. Streaming text keeps arriving while
        # the rover drives, and no world change can slip in because nothing has been
        # asked for yet.
        conv.pump()
        scroll_max = render.draw_chat(pane, conv, w, fonts, said, typing, scroll,
                                      S.SHOW_THINKING, reel,
                                      sight.view(w) if mode == "view" else None, pad_open)
        if mode == "settings":
            render.draw_settings(screen, fonts, items, picked, prefs, editing, notice,
                                 models, bool(script))
        pygame.display.flip()


def clamp_cursor(cursor, d, area):
    return (max(0, min(area.w - 1, cursor[0] + d[0])),
            max(0, min(area.h - 1, cursor[1] + d[1])))


if __name__ == "__main__":
    main()
