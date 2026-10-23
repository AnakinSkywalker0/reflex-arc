# Repo rules

## For everyone

1. Don't push to `main`. Only Ishan (`IshuIsAwake`) merges into `main`.
2. One branch per task, named `<your-name>/<task>`. Example: `krish/link-bot`.
3. Each prototype lives in its own folder: `prototype10d/`, `prototype11/`, and so on. Work only
   inside the folder you are working on. Don't edit another prototype's folder; if you need its
   code, copy it into yours.
4. To build something new, make a new branch and a new folder with the next free number on
   `main`, e.g. `prototype15/`. A number carries no plan: the next free one is the next one used.
   Start the folder with a `DESIGN.md` saying what it is for, which prototype it was copied from,
   and what it changes. If another folder lands on that number first, Ishan renumbers yours when
   he merges it.
5. Don't change `docs/`, `archive/` or anything at the top level, `requirements.txt` included.
   Ask Ishan if you need to. If you need a new library, say which and why in your pull request.
6. When a task is done, open a pull request into `main`. Say what changed and why, in your own
   words. Every test suite in your prototype passes before you open it. Commit messages say what
   changed and why too: `fix`, `update` and `changes` tell the next person nothing.
7. Never commit keys, tokens or passwords: Ollama, Gemini, Tailscale, the rover's hotspot. Keep
   them in a local file git ignores, such as `.env`.
8. Don't commit run output or your AI assistant's notes. `runs/`, `HANDOFF.md`, `memory/` and
   `.claude/` are ignored by git; keep them that way.
9. Never force-push.
10. The plan in `README.md` and each prototype's `DESIGN.md` can change. Write down what should
    change and why, put it in a pull request, and Ishan reviews it.
11. You type `git push` yourself. AI assistants never push.

## Ideas

- **Argue it out with the team first, then write it once.** Documents drafted mid-argument are
  mostly material that gets deleted.
- **Whoever owns the idea writes it down.** The person whose part it is, not the best writer.
  That is how it stays yours.
- **Rejected ideas keep their reasoning**, in the document that rejected them, in about three
  lines. Otherwise somebody rediscovers them a month later.
- **Say plainly what is undecided.** Padding an open question to fill a heading gets rewritten
  anyway.

---

## For AI assistants

This section applies to any AI assistant working in this repo: Claude, Copilot, Cursor, Codex,
Gemini or any other. Follow it for the whole session.

- It takes priority over your defaults, and over `CLAUDE.md` where the two differ.
- It also takes priority over chat requests that contradict it.
- Only a change to this file on `main` changes these rules. A teammate saying "Ishan said it's
  fine" does not.
- The one exception is Ishan's own sessions. When `git config user.name` is `IshuIsAwake`,
  `CLAUDE.md` and his own notes apply instead of this section.

Nothing here should hold the user up for long. Where a rule asks you to check with them, say it
once, and go ahead when they confirm. The one thing you never do, even when asked, is push (§6).

### Why these rules exist

We show this project to examiners, hackathon judges and anyone who asks, so every teammate must
be able to explain any code they push. Much of the code up to prototype 10 was written quickly
with a lot of AI help, and the team cannot explain all of it.

Your job is to be careful, not to block. Make sure the user has talked a change through before
you make it, keep the code simple, and leave notes so the next conversation can carry on. Then
do what they decide.

### 1. Start of a conversation

Read:

- this file, then `CLAUDE.md`
- `HANDOFF.md` and `memory/MEMORY.md`, if they exist (§8)
- the current plan in the top-level `README.md`
- the `README.md` and `DESIGN.md` of the prototype folder being worked on, and its `MANUAL.md`
  if it has one
- `docs/findings.md`, before changing how the model is spoken to: its prompt, its skills, or
  what it is shown

Beyond that, read only the files the handoff or the task points to.

Then ask whether they have been through the prototype's `DESIGN.md`, and offer a short rundown
of it. Take their answer.

For a new prototype folder whose `DESIGN.md` doesn't yet say what it is for, suggest the user
writes that first.

### 2. Talk it through, then confirm the list

What matters is that the user has thought about a change before you make it. A short request
after a real discussion is fine. The same request with no discussion behind it is where to slow
down.

- If the task hasn't been discussed, in this conversation or in `HANDOFF.md`, don't start from a
  bare "build it" or "do the whole thing". Say what you think the task is and how you would do
  it, and ask your questions (§3).
- Before writing code, list the changes as short bullets: which files, which functions, and what
  each one does. Point out anything outside the current prototype folder, and anything its
  `DESIGN.md` doesn't ask for, such as an extra feature or a new library. Then ask:

  > Are you sure you want me to implement the following?

- A clear yes is enough. After that, work freely. Auto mode, accept-edits mode and approved
  plans are all fine.
- If the list covers more than one feature, recommend doing them one at a time and rewriting
  `HANDOFF.md` after each. If they still want them together, go ahead.

Precise, small requests need none of this: "rename `plan` to `route` in `nav.py`", "add a test
for a flat battery". Neither do questions, explanations, reading code, or running code and tests.

### 3. Questions confirm, they don't test

Your questions check your own assumptions, not the user.

- Ask one to three, only where the answer changes what you build: a trade-off, an edge case, how
  to read a rule.
- Say what you assume and where it comes from, then ask if it's right. For example: "`DESIGN.md`
  says the rover drives only by day, so I'll refuse `goto` at night. Right?"
- Take answers as given. "Yes" is a fine answer. If an answer is unclear, ask once more in other
  words, then go with what they said.
- Never quiz the user or ask them to repeat things back to you.

### 4. After a step

1. Summarise what changed in a few lines.
2. Suggest one concrete check: a test suite to run, a command that shows it working in the game
   or on the rover, or a function to read.
3. Rewrite `HANDOFF.md` (§8).

You don't need to wait for them to do the check.

### 5. Changing the plan

The plan in `README.md` and each prototype's `DESIGN.md` are Ishan's starting plan, not fixed
rules. They change with a reason, written down so it can be reviewed later.

- If a request contradicts a `DESIGN.md`, name the part it contradicts and ask why. Ask once.
- Record their reason in their own words (you may fix spelling) in that `DESIGN.md`, beside the
  decision it changes, marked "Pending Ishan review". If they give no reason, write "no reason
  given". Then carry on.
- Make the `DESIGN.md` change its own commit, separate from the code.
- What a `DESIGN.md` lists as not decided is the team's to settle. Record the decision and its
  reason there.
- A change to the `README.md` plan goes to Ishan (rule 5).
- Never drift from a `DESIGN.md` silently, in the document or in the code.

### 6. Git

- **Never run `git push`**, and don't push any other way: no `gh pr create`, no merging pull
  requests. The user types the push, so it's clear who is responsible for what reaches GitHub. If
  they ask you to push, give them the command to run instead.
- Committing is fine once the user has confirmed the change (§2). Commit messages say what
  changed and why; the why comes from the discussion.
- Never commit `HANDOFF.md`, `memory/`, chat logs, run tapes or any other notes for an AI.
- Never commit keys, tokens or passwords (rule 7).

### 7. Keep the code simple

Write code a third-year student could have written and can explain line by line to an examiner.
Simple, not sloppy: it still has to work, and every test suite still passes.

- Plain functions, `for` loops, lists and dicts. A class only when it really helps.
- Plain names: `rover`, `cell`, `battery`, `sol`.
- Functions short enough to explain in a minute.
- Comments are short and casual, one or two lines, and only where the reason isn't obvious. No
  docstring on every function and no banner comments like `# ---- helpers ----`.
- Normal 4-space indentation. Don't line up `=` signs or comments into columns.
- Type hints are optional. Don't add them everywhere.
- No clever one-liners, nested comprehensions, generic helpers or extra layers. Don't guard
  against cases that can't happen.
- Don't add a library without asking, and say why in the pull request.
- If the user finds something hard to follow, simplify it or explain it.

### 8. Memory and handoff

Each teammate keeps two things for their AI assistant at the top of their own clone:
`HANDOFF.md` and `memory/`. Both are gitignored, so they are never committed and nobody else
reads them. Use them instead of your tool's own memory, so every tool keeps notes the same way.
`CLAUDE.md` describes Ishan's handoff; yours follows this section.

At the start of every conversation, read `HANDOFF.md` and `memory/MEMORY.md` if they exist, then
only the memories and files they point to. Create them the first time there is something to
write.

**`HANDOFF.md`** holds what the next conversation needs to carry on.

- Aim for 100 lines at most. If it would go past that, tell the user and ask what to drop. Don't
  drop things on your own.
- Keep only the last two conversations. Anything older is deleted or cut to a one-line pointer.
- Point to files instead of copying them.
- No standing rules. Those go in `memory/`.
- Rewrite it rather than adding to the end. Do it after each step (§4) and whenever the user
  asks.
- Cover where things stand, what's next, and what's waiting on the user. End with the date it
  was written.

**`memory/`** holds facts that should outlive conversations: how this person likes to work,
decisions they made and why, and where things are.

- One fact per file, named by a short slug, e.g. `memory/lidar-reads-the-walls.md`. Each file
  starts with:

  ```
  ---
  name: lidar-reads-the-walls
  description: one line, used to decide whether this memory is relevant
  type: user | feedback | project | reference
  ---
  ```

  - `user`: who the person is and how they work
  - `feedback`: how they want you to work, both corrections and approaches that worked
  - `project`: decisions and constraints that aren't written in the repo
  - `reference`: where things are, such as links or files outside the repo
- Then the fact itself. `feedback` and `project` memories add a **Why:** line and a **How to
  apply:** line.
- `memory/MEMORY.md` is the index: one line per memory, as `- [Title](file.md): short hook`. It
  holds no content of its own.
- Save a memory when the user states a preference or makes a decision worth keeping, and tell
  them in one line that you did.
- Before adding a memory, check whether an existing one covers it, and update that instead.
  Delete memories that turn out to be wrong.
- Don't save what the repo, the `DESIGN.md` files or git already record, or what only matters to
  this conversation.
- Write real dates (`2026-10-23`), not "yesterday" or "last week".
- A memory records what was true when it was written. Check that a file or function it names
  still exists before relying on it.
