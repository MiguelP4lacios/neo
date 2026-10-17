# Playbooks — how this workspace actually behaves

Standing facts about the terrain: which command works, which output lies, which trap has already been paid for. **Not dated events** — those live in `agent-notes/YYYY/`.

A playbook is read **before** touching something. A note is read to understand what happened.

## Which file do I read?

| File | Covers | Read when |
|---|---|---|
| [worktrees-and-orca.md](./worktrees-and-orca.md) | Orca's worktree model and where its JSON misleads | Working with worktrees or reading agent state |
| [branches-and-repos.md](./branches-and-repos.md) | Repo locations, branch naming and CI validation, git traps | Naming a branch, or a `git log` search returns nonsense |
| [prs-and-gh.md](./prs-and-gh.md) | Reading PR state with `gh`, who actually merges here | Asking whether something merged or deployed |
| [code-navigation.md](./code-navigation.md) | Finding what code does, and how a static read lies | Reading an unfamiliar repo |

Add a row when you add a file (for example `issue-tracker.md` or `infrastructure.md` when you enable an optional scout, or a domain file such as `billing-domain.md`).

## Which scout owns which

Each scout reads its files at session start and appends what it learned at session end. One bullet per fact, no narrative, no timestamps.

| Scout | Reads |
|---|---|
| `neo-git-scout` | prs-and-gh, branches-and-repos, worktrees-and-orca |
| `neo-repo-scout` | code-navigation (plus any domain files you add) |
| `neo-memory-curator` | all of them — it prunes and deduplicates |

If a new fact does not fit an existing file, add it to the closest one rather than creating a file for a single bullet. Split only when a file stops being scannable.
