# Neo

A Claude Code plugin that turns a folder full of git repos into one workspace with an orchestrator and a second brain.

You keep all your projects under one root (`~/code`, `~/work`, ...). You start Claude Code **in that root**, and it becomes **Neo**: it knows every repo, where you left each one, what you worked on this week, and what you delegated to which agent — and it hands real work to agents running *inside* each project.

## The principle: orchestrate, never execute

Neo never edits project code from its own session. Claude Code only loads a project's `CLAUDE.md`, agents, skills and `.mcp.json` when the session's cwd is inside that project — so a change made from the root would skip every convention and gate the project defines. Instead, Neo **deploys** work into the project via [Orca](https://github.com/stablyai/orca) (a git-worktree and coding-agent manager): it creates a worktree, launches an agent there with a self-contained brief, watches for the agent to finish, and reports back. Neo's own scouts are read-only.

## Two memory layers

| Layer | What | Lives in |
|---|---|---|
| **Engram** | Session-level memory: searchable, chronological. Neo saves under `project: "neo"`; project facts under each repo's canonical key from the registry. | Engram MCP server |
| **Agent notes** | The durable work record: dated findings, decisions, verifications, handoffs, runbooks, plus each scout's operational playbook. Plain markdown, indexed by a README. | `<root>/.claude/agents/agent-notes/` |

## Requirements

- [Claude Code](https://docs.claude.com/en/docs/claude-code)
- [Engram](https://github.com/Gentleman-Programming/engram) — the MCP memory server, with its binary on `PATH` (install it as a Claude Code plugin or standalone MCP server)
- [Orca](https://github.com/stablyai/orca) — optional but recommended; without it `neo-deploy` falls back to background `claude -p` runs
- `git`, `gh` (authenticated), `jq`
- Nice to have: `rg`, `fd`, `sqlite3`

## Install

```bash
claude plugin marketplace add <owner>/neo
claude plugin install neo@neo
```

## First run

```bash
cd ~/code          # your workspace root: the folder that CONTAINS your repos
claude
> /neo:neo-init
```

`neo-init` detects your git identity, GitHub login, timezone and tools, asks a few questions (reply language, issue tracker — none, Jira, GitHub or Linear —, whether you use Orca and where worktrees live), scans the root for repos and proposes a registry (`Directory | Engram key | Tracker | Alias | Status`, with status inferred from your last commit). Once you confirm, it writes:

- `<root>/CLAUDE.md` — Neo's identity (active only when cwd is exactly the root), config, Engram rules, the registry, worktree roots and the deployment rule. A plugin cannot ship a CLAUDE.md, so this is generated.
- `<root>/.claude/agents/agent-notes/` — the notes index, naming convention, runbooks folder and starter playbooks (pre-filled with generic git, `gh` and Orca facts).
- `<root>/.engram/config.json` — `{"project_name": "neo"}`.

It never overwrites existing files. Run it again any time to pick up new or removed repos: it shows a registry diff and applies only what you approve.

Start a new session afterwards so the generated `CLAUDE.md` loads.

## Daily use

| Command | Answers |
|---|---|
| `/neo:neo-status` | Where did I leave everything? Branches, dirty worktrees, unpushed work, open PRs, live Orca agents. Live view, nothing saved. |
| `/neo:neo-digest [today\|week\|<date>]` | What did I work on? Git across all repos + Engram + your tracker (optional), saved to Engram so history accumulates. |
| `/neo:neo-deploy` | Launch a task into a project: resolve the alias, create an Orca worktree, hand off a brief, watch only this session's deploys, report when they finish. |
| `/neo:neo-weekly-status` | Format audited work as a numbered objectives report with status marks. |

You can also just talk: "deploy the search fix to api", "what's in flight?", "what did I do yesterday?".

Agents (invoked by Neo, read-only): `neo:neo-git-scout`, `neo:neo-repo-scout`, `neo:neo-memory-curator`. Optional issue-tracker and infrastructure scouts ship as templates in [`templates/integrations/`](./templates/integrations/).

## Agent-notes convention

- Dated notes: `YYYY/MM/YYYY-MM-DD-<TYPE>-<topic>.md`, where TYPE is `INV` (inventory), `VER` (verification), `DEC` (decision), `INC` (incident), `RUN` (runbook), `HND` (handoff).
- Runbooks are living procedures with no date: `runbooks/RUN-<topic>.md`, edited in place.
- Folders are dates, never project names; grouping by area lives in the index (`README.md`), and every entry carries a **Read when** line. An unindexed note does not exist.
- Notes are never rewritten to change history — supersede and link back.
- Playbooks (`playbooks/*.md`) are standing facts, one bullet per fact, owned by a scout that reads them before recon and appends what it learned.

## Troubleshooting

**Engram MCP fails with "executable not found"** — Claude Code's `PATH` (especially when launched from a GUI or a non-login shell) does not include the directory where the `engram` binary lives (e.g. Homebrew's `/opt/homebrew/bin`). Symlink it somewhere that is always on `PATH`:

```bash
sudo ln -s "$(command -v engram)" /usr/local/bin/engram
```

Then restart Claude Code.

**Neo does not act as Neo** — the identity is active only when the session's cwd is exactly the workspace root, and only after `neo-init` wrote `<root>/CLAUDE.md`. Start a fresh session there.

## License

[MIT](./LICENSE)
