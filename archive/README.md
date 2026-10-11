# Archive

`prototypes-1-9.tar.gz` holds prototypes 1 to 9 exactly as committed: code, tests and design notes,
with no run tapes and no virtual environments. What they settled is in
[`../docs/findings.md`](../docs/findings.md). Read that first; you rarely need the code.

To get one back:

```sh
tar -xzf archive/prototypes-1-9.tar.gz prototypes-1-9/prototype2    # one prototype
git checkout prototypes-1-9 -- prototype2                           # or straight from the tag
```

`local/` is ignored by git and exists only on Ishan's machine. It holds the run tapes the
prototypes recorded, which were never committed, and the uncommitted edits from two abandoned
worktrees.
