---
name: neo-status
description: Live snapshot of where every project in the workspace stands right now - branches, dirty worktrees, unpushed work, open PRs, live Orca worktrees and agents. Trigger - where did I leave things, status of my projects, what do I have open, work in flight, donde deje todo, estado de mis proyectos.
---

# neo-status

A live snapshot — no history, no persistence. Answers "where did I leave everything?".

Everything configurable comes from the workspace root's `CLAUDE.md` (already in context): the **Neo config** table (workspace root, worktree root, Orca yes/no, reply language) and the **Canonical project registry**. Below, `<root>` means the configured workspace root.

## Step 1 — Repo state

For every `active` directory in the registry (add `occasional` when the user asks for full detail):

```bash
ROOT="<root>"
for dir in <registry dirs>; do
  repo="$ROOT/$dir"
  [ -d "$repo/.git" ] || continue
  branch=$(git -C "$repo" branch --show-current)
  dirty=$(git -C "$repo" status --porcelain | wc -l | tr -d ' ')
  counts=$(git -C "$repo" rev-list --left-right --count @{upstream}...HEAD 2>/dev/null || echo 'no-upstream')
  wts=$(git -C "$repo" worktree list | tail -n +2)
  printf '%s | %s | dirty:%s | behind/ahead:%s\n%s\n' "$dir" "$branch" "$dirty" "$counts" "$wts"
done
```

For each linked worktree listed, also report its dirty count and ahead count — in-flight worktrees are where work gets lost. A branch with no upstream is "never pushed", not "0 ahead".

## Step 2 — Open PRs

One cross-repo call first: `gh search prs --author=@me --state=open --json repository,title,number,url,updatedAt`. If `gh search` fails (auth or scope), fall back to `gh pr list --author=@me --state=open` inside each active repo. If `gh` is not installed, say so and skip.

## Step 3 — Orca live view (the richest source; skip when Orca is `no`)

One call covers every Orca-tracked worktree across all repos:

```bash
orca worktree ps --json
```

Per-worktree fields worth reporting: `branch`, `status`, `workspaceStatus` (card: todo / in-progress / in-review / completed), `liveTerminalCount`, `lastActivityAt`, `linkedPR {number, state}`, `comment`, and `agents[]` (`agentType`, `state` working/done, `interrupted`, `prompt`, `lastAssistantMessage`). Agent state lives ONLY in `.agents[]` — there is no top-level `agentState`. This is live state that git cannot see — merge it with Step 1 as the primary in-flight view. Output can be large: filter with `jq` to non-archived (`isArchived != true`), recently active entries instead of dumping it whole. Never use cwd-derived selectors (`active`/`current`) from Neo's session — always explicit `--repo`/`--worktree` selectors.

Optionally delegate Steps 1–3 to the `neo:neo-git-scout` agent when the registry is large; it returns a compact table.

## Step 4 — Report

Reply in the configured language. One compact table: `project | branch | dirty | ahead | open PRs | live worktrees`. Then an **Attention** list, most urgent first: dirty worktrees with no recent commits, branches ahead of upstream (or never pushed) with no PR, PRs waiting on review, interrupted agents, dormant worktrees that look abandoned (merged PR, clean, idle). Do not persist anything — this is a live view.
