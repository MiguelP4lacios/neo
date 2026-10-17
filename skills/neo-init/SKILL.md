---
name: neo-init
description: First-run setup for Neo in a workspace root that contains many git repos. Detects the user's identity, timezone and tools, scans for repos, proposes the project registry, then writes the workspace CLAUDE.md, the agent-notes scaffold and the Engram config. Idempotent and re-runnable to refresh the registry. Trigger - neo init, set up neo, initialize neo, configure neo workspace, refresh neo registry, new repo added.
---

# neo-init

Set up (or refresh) Neo in a workspace root: one folder that contains many git repos. Neo's identity, registry and rules live in `<root>/CLAUDE.md` — a plugin cannot ship a CLAUDE.md, so this skill writes it from a template.

**Templates live next to this file.** When this skill loaded you were told its base directory; every path below written as `templates/...` is relative to that directory. Read them from there — never re-type them from memory.

```
templates/CLAUDE.md.tmpl
templates/engram-config.json
templates/agent-notes/README.md
templates/agent-notes/NAMING-CONVENTION.md
templates/agent-notes/runbooks/README.md
templates/agent-notes/playbooks/README.md
templates/agent-notes/playbooks/worktrees-and-orca.md
templates/agent-notes/playbooks/branches-and-repos.md
templates/agent-notes/playbooks/prs-and-gh.md
templates/agent-notes/playbooks/code-navigation.md
```

## Hard rules

1. **Never overwrite** an existing `<root>/CLAUDE.md`, agent note, playbook, or `.engram/config.json`. Create what is missing; for what exists, propose a diff and apply only what the user approves.
2. **Ask, then stop.** Every question round ends your turn. Never assume an answer and continue.
3. Read-only against every repo. This skill writes only inside `<root>/CLAUDE.md`, `<root>/.claude/agents/agent-notes/` and `<root>/.engram/`.
4. Engram writes go through MCP tools only, under `project: "neo"`.

## Step 1 — Confirm the root and detect state

The root is the session's cwd. If cwd is itself a git repo (has `.git`), warn: Neo is meant to run from the folder that CONTAINS repos, not from inside one — ask whether to continue anyway.

Detect, in one Bash call (all read-only; tolerate missing tools):

```bash
ROOT="$PWD"
echo "root=$ROOT"
for f in CLAUDE.md .engram/config.json .claude/agents/agent-notes/README.md; do
  [ -e "$ROOT/$f" ] && echo "exists: $f" || echo "missing: $f"
done
echo "git_name=$(git config --global user.name)"
echo "git_email_domain=$(git config --global user.email | awk -F@ '{print $2}')"
command -v gh >/dev/null && echo "gh_login=$(gh api user --jq .login 2>/dev/null)"
if [ -n "$TZ" ]; then echo "tz=$TZ"
elif [ -L /etc/localtime ]; then echo "tz=$(readlink /etc/localtime | awk -F'zoneinfo/' '{print $2}')"
elif command -v timedatectl >/dev/null; then echo "tz=$(timedatectl show -p Timezone --value)"
fi
echo "utc_offset=$(date +%z)"
for t in orca engram gh jq git fd rg sqlite3; do command -v "$t" >/dev/null && echo "tool:$t=yes" || echo "tool:$t=no"; done
```

If `<root>/CLAUDE.md` exists, read it. If it contains `<!-- neo:registry:start -->`, this is a **refresh run** (go to Step 5's merge path). If it exists without Neo markers, it is the user's own file — Neo's content will be offered as an appended section, never a replacement.

## Step 2 — Ask the setup questions (one round)

Use the AskUserQuestion tool if available; otherwise ask in one message. Pre-fill every answer with what Step 1 detected so the user mostly confirms:

1. **Workspace root** — confirm `<root>`.
2. **Name / handle** for git author filtering — default `git config user.name`; the filter becomes a case-tolerant regex (e.g. `Jane Doe` → `[Jj]ane`). Also confirm the GitHub login (`gh api user`).
3. **Timezone** — detected IANA name and UTC offset.
4. **Reply language** — default: the language the user is writing in.
5. **Issue tracker** — `none` (default), `jira`, `github`, `linear`; if not `none`, the base URL used to link keys (e.g. `https://<site>.atlassian.net/browse/`, `https://github.com/<org>/<repo>/issues/`, `https://linear.app/<team>/issue/`).
6. **Orca** — whether they use it (default `yes` if `orca` is on PATH), and the **worktree root** (default `<root>/wt/`; Orca users: the folder Orca creates worktrees in).

Stop and wait for the answers.

## Step 3 — Scan for repos and propose the registry

```bash
ROOT="<root>"; AUTHOR="<author regex>"; WT="<worktree root>"
now=$(date +%s)
{ fd -H -t d -d 2 '^\.git$' "$ROOT" 2>/dev/null || find "$ROOT" -maxdepth 2 -type d -name .git; } | while IFS= read -r gitdir; do
  repo=$(dirname "${gitdir%/}")
  case "$repo/" in "$WT"*) continue ;; esac          # skip worktrees under the worktree root
  dir=${repo#"$ROOT"/}
  mine=$(git -C "$repo" log -1 --all --author="$AUTHOR" --format=%ct 2>/dev/null)
  any=$(git -C "$repo" log -1 --all --format=%ct 2>/dev/null)
  keys=$(git -C "$repo" for-each-ref --format='%(refname:short)' refs/heads refs/remotes 2>/dev/null \
         | rg -o '[A-Z][A-Z0-9]+-[0-9]+' | awk -F- '{print $1}' | sort | uniq -c | sort -rn | awk '{print $2}' | head -2 | paste -sd, -)
  printf '%s|%s|%s|%s\n' "$dir" "${mine:-0}" "${any:-0}" "${keys:--}"
done
```

(`fd` only matches directories here, so linked worktrees — whose `.git` is a file — are excluded automatically.)

Build one row per repo:

| Column | Rule |
|---|---|
| Directory | path relative to root |
| Engram key | directory name lowercased (keep an existing key from a refresh run) |
| Tracker | the dominant ticket prefix found in branch names, or `—`; always `—` when the tracker is `none` |
| Alias / product | leave blank for the user to fill (a nickname they use, e.g. "api" for `acme-api`) |
| Status | from the user's own last commit (`mine`): ≤30 days `active`, ≤180 days `occasional`, else `dormant`; if they never committed, use `any` and cap at `occasional` |

Show the proposed table and ask the user to confirm, edit aliases/statuses, or drop rows. Stop and wait.

## Step 4 — Write (fresh install)

Only for files that do not exist:

1. `<root>/CLAUDE.md` — read `templates/CLAUDE.md.tmpl`, replace every `{{PLACEHOLDER}}` (`WORKSPACE_ROOT`, `OWNER_NAME`, `GIT_AUTHOR_PATTERN`, `GITHUB_LOGIN`, `TIMEZONE`, `UTC_OFFSET` as `-05:00`-style, `REPLY_LANGUAGE`, `ISSUE_TRACKER`, `TRACKER_BASE_URL` (`—` when none), `ORCA_ENABLED` (`yes`/`no`), `WORKTREE_ROOT`, `REGISTRY_ROWS`), and write it. Verify no `{{` remains.
2. `<root>/.claude/agents/agent-notes/` — copy each file under `templates/agent-notes/` to the same relative path, skipping any target that exists. If Orca is `no`, still copy `worktrees-and-orca.md` (its git facts apply) — do not edit it.
3. `<root>/.engram/config.json` — copy `templates/engram-config.json`. If one exists with a different `project_name`, report it and leave it alone.
4. If `<root>` is itself inside a git repo, remind the user that these files may be committed by accident.

## Step 5 — Refresh path (CLAUDE.md already has Neo markers)

1. Parse the current table between `<!-- neo:registry:start -->` and `<!-- neo:registry:end -->`.
2. Diff against the Step 3 scan: **new** directories (add rows), **missing** directories (propose marking `dormant` or removing — never remove silently), and **status drift** (only suggest; the user may have set statuses by hand). Never touch Alias, Engram key or Tracker values the user wrote.
3. Show the diff as a small table (`+ row`, `- row`, `~ status`) and ask which to apply. Stop and wait.
4. Edit only the rows inside the markers. Leave every other line of CLAUDE.md untouched. Do the same for the config block (`neo:config` markers) only if the user changed an answer.
5. Create any agent-notes template file that is missing (never overwrite one that exists).

For a CLAUDE.md with no Neo markers: show the rendered template, ask whether to append it as a section, and append only on yes.

## Step 6 — Optional wiring

Offer (do not do unasked):

- **Orca**: `orca repo list --json`, and for each `active` repo not registered, offer `orca repo add --path "<absolute root>/<dir>" --json` (always an absolute path — if you build it from the home directory use `$HOME`, never `~`, which Orca does not expand).
- **Optional scouts**: the plugin ships issue-tracker and infrastructure scout templates under its `templates/integrations/` directory (two levels up from this skill's base directory). If the tracker is not `none`, mention that the user can copy `neo-jira-scout.md` into `<root>/.claude/agents/` and adapt it (see that directory's README).

## Step 7 — Persist and report

`mem_save` with `project: "neo"`, `type: "config"`, `topic_key: "neo/config"`, `capture_prompt: false`, title `Neo workspace configured`, content: root, tracker, Orca yes/no, worktree root, number of registry rows by status. (If the Engram MCP is unavailable, say so and continue — the files are the source of truth.)

Report in the reply language: files created, files skipped because they existed, registry rows by status, and the next commands: `/neo:neo-status`, `/neo:neo-digest`, `/neo:neo-deploy`. Tell the user to start a NEW session from `<root>` so the freshly written CLAUDE.md loads.
