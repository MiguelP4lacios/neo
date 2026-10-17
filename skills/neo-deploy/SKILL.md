---
name: neo-deploy
description: Launch work INTO a target project so its own CLAUDE.md, agents, skills and gates fully apply - via an Orca worktree or terminal, with a completion watch scoped to this session's own deploys. Trigger - deploy, dispatch a task to a repo, work on project X from Neo, launch a task in <alias>, hand this to an agent in <project>, despliega, lanza una tarea en.
---

# neo-deploy

Neo coordinates; the project executes. Claude Code only loads a project's CLAUDE.md, `.claude/agents`, `.claude/skills` and `.mcp.json` when the session's cwd is inside that project — so deployment ALWAYS means a session rooted in the target directory.

Configuration (workspace root, worktree root, whether Orca is used, reply language) comes from the **Neo config** table in the workspace root's `CLAUDE.md` (already in context). Below, `<root>` and `<worktree root>` mean those values.

## Hard rules

1. Never edit target-project files from Neo's own session.
2. Subagents launched from Neo are read-only, and must Read the target's `CLAUDE.md` before drawing conclusions (they do not inherit it).
3. Deployed sessions obey the target's own conventions and gates (its sub-agents, spec/review workflows) — Neo never bypasses them.

## Step 1 — Resolve the target

Map the user's alias through the registry in `<root>/CLAUDE.md` (Directory and Alias columns; e.g. "api" → `acme-api`). If the alias is ambiguous or unknown, ask one question and stop.

## Step 2 — Pick the workspace

- Quick fix or exploration → the main repo checkout (agent in an existing checkout: `orca terminal create --worktree <explicit selector> --command "claude" --json`).
- Feature/ticket work → an Orca worktree (ordinary linked git worktrees, created under the worktree root). If the repo is not registered in Orca: `orca repo add --path "<absolute path>" --json`.
- Do NOT create a new worktree just for convenience or parallelism — only when the user asks or a filesystem conflict makes sharing unsafe.
- If the project's CI validates branch names (see `playbooks/branches-and-repos.md`), build `--name` so the derived branch passes — Orca derives the branch from the name.

## Step 3 — Launch (default = full handoff)

Deploy is fire-and-forget: ownership transfers to the launched agent. Check on it later via `orca worktree ps` / card status and the watch (Step 4) — do not peek at its terminal after delivering the prompt.

Write the brief first. A brief is self-contained, in English: goal, constraints, done-criteria, and "read this project's CLAUDE.md first". For anything longer than a couple of sentences, save it to a file in this session's state directory (Step 4) and pass a pointer instead of the text:

```bash
orca worktree create --repo "path:$HOME/<path under home>/<dir>" --name <task-slug> \
  --agent claude --prompt "Read <absolute brief path> and execute it exactly" \
  --setup run --json
```

Rules that bite — each one was paid for:

- **Use `$HOME`, never `~`, in any Orca path argument.** Orca does not expand `~`: it creates a literal `~` directory inside the repo and nests the worktree there. `"$HOME/..."` is expanded by the shell before Orca sees it. (If the root is not under home, pass the absolute path.)
- **Long briefs get truncated in transit** — the agent receives only the tail. Brief-in-a-file plus a one-line pointer, always, for anything non-trivial. Same for `orca terminal send`.
- **Always pass explicit `--repo` / `--worktree` selectors.** `active`/`current` resolve from cwd, which in Neo's session is the workspace root, not the target.
- **Lineage:** Orca records a new worktree as a child of the caller's context when it can infer one. Pass `--no-parent` when the work is independent of whatever Neo's session is attached to.
- With `--agent ... --json`, the new agent's terminal handle is `result.agentTerminalHandle` (older runtimes: `result.startupTerminal.handle`).

Add `--activate` to reveal it in the app when the user will drive it.

To prompt an existing terminal: `orca terminal send --terminal <handle> --text "<short brief or pointer>" --enter --json`.

- **The `--terminal` handle is the `handle` field (`term_…`) from `orca terminal list --json`, never the `paneKey` from `orca worktree ps`** — a paneKey is rejected as `terminal_handle_stale`, even with `--retry-request`.
- If the send reports `input_accepted` without `turn_started`, replay the same request id with `--retry-request <id> --wait-submit 30`; it confirms delivery instead of resending.

After launching, verify pickup ONCE via `orca worktree ps --json` reading **`.agents[].state`** (NOT a top-level `.agentState`, which does not exist and reads as null — see Step 4). That single check is part of delivery, not supervision. Then stamp the card so the work is visible:

```bash
orca worktree set --worktree <explicit selector> --comment "<one-line state>" --workspace-status in-progress --json
```

**Fallback when Orca is not used or not running:** `cd "<root>/<dir>" && claude -p "Read <brief path> and execute it exactly"` in the background (Bash `run_in_background`). Then there is no Orca watch — report the background task id instead.

## Supervised mode (ONLY when the user explicitly asks to supervise, wait, or coordinate)

Use Orca orchestration — never for plain handoffs:

```bash
orca orchestration run-create --objective "<objective>" --json      # keep run_id, pass --run everywhere
orca orchestration task-create --spec "<worker task>" --json
orca orchestration worker-start --task <task_id> --run <run_id> --worktree <selector> --agent claude --json
orca orchestration check --run <run_id> --wait --types worker_done,escalation,question --timeout-ms 540000 --json
orca orchestration worker-release --dispatch <dispatch_id> --json
```

Rules that bite: rolling waits ≤9 min (a Bash call caps at 10; a timeout is a checkpoint, not a failure — coding tasks run 15–60 min); `check --wait` prints keepalive JSON to stderr every 15 s (`jq 'select(._keepalive|not)'`); ack every delivery (`check --ack <delivery_id>`) or it replays; a valid `worker_done` auto-completes the task — do not `task-update` after it; account for every settled worker (`worker-release`/`worker-retain`, never `terminal close`); read a worker without stealing its terminal via `orca orchestration worker-read --dispatch <id> --json`.

## Step 4 — Arm the completion watch (so Neo reports, instead of the user asking)

A deployed agent's completion reaches the Orca app, not Neo's conversation: its lifecycle hooks fire inside its own session. Without a watch, the only way Neo learns a delegation finished is the user asking "how did it go?" — which re-sends Neo's whole context just to read a status. The watch inverts that cost: polling runs in the shell for free, and only a real state transition becomes a message.

**State directory:** use this session's scratchpad directory if the system prompt names one; otherwise create one with `mktemp -d` once and reuse that exact path for the rest of the session. Call it `<state dir>`.

**The watch must cover ONLY the worktrees this session deployed.** A watch that scans every worktree under the worktree root wakes this session for work another session owns. Record each deploy's absolute path as you make it, and watch exactly those:

```bash
echo "<absolute worktree path>" >> "<state dir>/deployed-worktrees.txt"
```

Arm ONE watch after the first deploy; later deploys only append to the list (the watch re-reads it every cycle). Never filter by excluding other sessions' worktrees by name — that breaks the next time somebody else deploys.

```bash
MINE="<state dir>/deployed-worktrees.txt"
Q='.result.worktrees[]? | select(.path | IN($mine[])) | . as $w | ((($w.agents // []) | if length == 0 then [{state:"no-agent", interrupted:false}] else . end)[]) | "\($w.repo)/\($w.displayName // $w.branch) -> \(.state)\(if .interrupted then " [INTERRUPTED]" else "" end)"'
LIST=$(mktemp); prev=$(mktemp); cur=$(mktemp)
# Re-read the deploy list on every cycle so worktrees deployed AFTER arming are picked up.
# Use a temp file, never <(...): a process substitution is closed before jq reads it,
# and "| jq -s ." would double-wrap the array so IN($mine[]) matches nothing.
snap() { jq -R . "$MINE" > "$LIST"; orca worktree ps --json 2>/dev/null | jq -r --slurpfile mine "$LIST" "$Q" 2>/dev/null | sort; }
snap > "$prev" || true
# 0 initial entries means the filter is broken, not that nothing is deployed. Fix before trusting it.
echo "WATCH: $(wc -l < "$prev" | tr -d ' ') initial entries: $(tr '\n' ';' < "$prev")"
while true; do
  sleep 45
  snap > "$cur" || true
  if [ -s "$cur" ]; then
    comm -13 "$prev" "$cur" | awk '{print "NOW:  " $0}'
    comm -23 "$prev" "$cur" | awk '{print "GONE: " $0}'
    cp "$cur" "$prev"
  fi
done
```

Run it with the `Monitor` tool (persistent) when available — each printed line becomes an event; otherwise Bash with `run_in_background`. Five things this took several broken attempts to get right — do not re-derive them:

- **`.agentState`, `.agentType` and `.lastAssistantMessage` do not exist at the top level of `orca worktree ps --json`.** They read as `null`, always. Real state is nested in `.agents[]`: `state`, `interrupted`, `lastAssistantMessage`, `prompt`, `toolName`. A watch built on the top-level field stays silent forever, and silence is indistinguishable from "still working" — the worst available failure mode.
- **Scope the watch to this session's own deploys.** The owner of a deployment is the session that made it. Keep the path list; do not scan the directory.
- **`displayName` / `branch` is not a unique key.** Many repos keep their main checkout on the same branch name, so keying by name collapses them and emits endless fake transitions. Key by `path`, which also excludes main checkouts that sit `in-progress` for unrelated reasons.
- **Portable shell only.** The script may run under zsh, and macOS `/bin/bash` is 3.2: no associative arrays, no `${!arr[@]}`. Keep state in temp files compared with `comm`, as above.
- **Emit on every transition, not only `done`.** A filter that matches success alone is mute through a crash, an interrupt, or a worktree that disappears.

When an event lands, read the finished agent's own final report without opening its terminal — this preserves the handoff:

```bash
orca worktree ps --json | jq -r '.result.worktrees[]? | select(.path == "<absolute worktree path>") | .agents[]? | select(.state=="done") | .lastAssistantMessage'
```

If it is empty or truncated (this happens intermittently), use `orca terminal read --terminal <handle> --json`. Then report to the user proactively, in the reply language. Send a push notification only when the news changes what they would do next. The watch is session-scoped — it dies with Neo's session, so re-arm it after a restart (the path list in the state directory survives only if the directory does).

## Step 5 — Log the dispatch

After launching, `mem_save` with `project: "neo"`, `capture_prompt: false`, `topic_key: "neo/deploy-log"`, recording: target project (Engram key), workspace used (worktree path or main checkout), task summary, brief path, and how it was launched. This is what makes "what did I delegate and where" answerable later. If something durable was learned about Orca's behaviour, append one bullet to `.claude/agents/agent-notes/playbooks/worktrees-and-orca.md`.
