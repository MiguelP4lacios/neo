---
name: neo-digest
description: Build the "what did I work on" digest across all projects in the workspace (git + Engram + optional issue tracker) and persist it to Engram. Trigger - what did I work on, daily digest, standup, weekly review, work summary, que hice hoy, que trabaje esta semana, resumen de trabajo.
---

# neo-digest

Answer "what did I work on" for a time window, across every project, and persist the digest to Engram so history accumulates.

Everything configurable comes from the workspace root's `CLAUDE.md` (already in context): the **Neo config** table (workspace root, git author filter, timezone and UTC offset, reply language, issue tracker and its base URL, Orca yes/no) and the **Canonical project registry**. Below, `<root>`, `<author>` and `<tz>` mean those values.

## Arguments

- `today` (default): since local midnight in `<tz>`.
- `week`: since last Monday 00:00 local.
- An explicit date or range (e.g. `2026-01-15` or `2026-01-12..2026-01-16`).

## Step 1 — Git sweep

For every registry directory with status `active` or `occasional` that is a git repo, run one script:

```bash
ROOT="<root>"; SINCE="<window start, local time, e.g. 2026-01-15 00:00>"
for dir in <registry dirs>; do
  repo="$ROOT/$dir"
  [ -d "$repo/.git" ] || continue
  log=$(git -C "$repo" log --all --since="$SINCE" --author="<author>" \
        --pretty=format:'%ad %h %d %s' --date=format:'%m-%d %H:%M' 2>/dev/null)
  [ -n "$log" ] && printf '### %s\n%s\n' "$dir" "$log"
done
```

Then enumerate worktrees per active repo (`git -C <repo> worktree list --porcelain`) — this covers the configured worktree root and `<repo>/.claude/worktrees/` automatically, since linked worktrees share the repo's refs. Orca-managed worktrees are ordinary linked git worktrees, so the sweep already covers their commits. When Orca is `yes`, `orca worktree ps --json` adds per-worktree agent status (`.agents[]`) and last activity on top of git history. For each listed worktree path, capture loose ends:

- Dirty files: `git -C <wt> status --porcelain | wc -l`
- Unpushed commits: `git -C <wt> rev-list --count @{upstream}..HEAD 2>/dev/null` (no output = never pushed)

Commits are already covered by `--all` on the main repo; worktrees are only checked for uncommitted/unpushed state.

## Step 2 — Engram sweep

Preferred: the MCP tools — `mem_context` and `mem_search` with `all_projects: true` for the window, then `mem_get_observation` for anything worth expanding.

Optional, faster for a wide window when `sqlite3` is available — read-only SQL against Engram's database (default `~/.engram/engram.db`; never write to it):

```bash
sqlite3 -readonly "$HOME/.engram/engram.db" \
  "SELECT project, type, title, substr(created_at,1,16) FROM observations \
   WHERE created_at >= '<window start in UTC>' ORDER BY project, created_at;"
```

`created_at` is stored in UTC — convert the local window start using the configured UTC offset before comparing. If the schema differs (Engram version), fall back to the MCP tools.

## Step 3 — Issue tracker correlation (optional — skip if the tracker is `none`)

Extract ticket keys matching `[A-Z][A-Z0-9]+-[0-9]+` (Jira/Linear style) or `#[0-9]+` (GitHub issues) from branch names and commit subjects found in Step 1. Deduplicate, then fetch status in as few calls as possible with whatever tracker integration is available (a tracker MCP server, `gh issue view`, or an optional tracker scout agent in `<root>/.claude/agents/`). Ask for a narrow field list (summary, status, assignee). If the tracker is unreachable, skip this step and say so in the digest — never block on it.

## Step 4 — Compose the digest

Reply in the configured language. Group by project (use the registry alias when one exists):

- Per project → per ticket (or "no ticket"): what the commits accomplished, one line each, with tracker status attached when known (e.g. `ACME-142 — In Review`).
- **Loose ends** section: dirty worktrees, unpushed or never-pushed branches, commits without a ticket key (only when a tracker is configured), Engram observations with no matching git activity (work discussed but not committed).

## Step 5 — Persist

Save the digest with `mem_save`: `project: "neo"`, `capture_prompt: false`, `title: "Digest <window>"`, `topic_key: "neo/digest-<YYYY-MM-DD>"` (add a `-week` suffix for weekly), content = the digest in compact form. Weekly digests first recall the week's daily digests (`mem_search`, `project: "neo"`, query `digest`) and build on them instead of re-deriving everything.
