# Playbook — Worktrees and Orca

Orca's worktree model and the places its JSON does not say what it looks like it says.

Standing facts about this workspace. Not dated events — see `agent-notes/YYYY/` for those. The bullets below are generic Orca and git behaviour, pre-filled; append what you learn about this workspace.

- Orca-managed worktrees are ordinary linked git worktrees: `git -C <repo> worktree list` sees them, and `git log --all` in the parent repo already covers their commits.
- `orca worktree ps --json` has NO top-level `agentState`, `agentType` or `lastAssistantMessage` — they read as null. Real agent state is nested in the `.agents[]` array (`state`, `interrupted`, `prompt`, `toolName`, `lastAssistantMessage`). A watch built on the top-level field stays silent forever, which is indistinguishable from "still working".
- `displayName`/`branch` is not a unique key across worktrees — several repos can have their main checkout on the same branch (`main`, `develop`), so keying by name collapses them and emits endless false transitions. Key by `path` (or `worktreeId`), and filter deploys by path under the worktree root.
- `orca worktree ps` returns `lastAssistantMessage` truncated or empty intermittently. For an agent's full final report use `orca terminal read --terminal <handle> --json`.
- `lastAssistantMessage` fields can contain prior investigation context (ticket ids, decisions) directly relevant to a current recon task — search the raw JSON by keyword, don't just skim structured fields.
- Orca does not expand `~` in path arguments — it creates a literal `~` directory inside the repo. Always pass `"$HOME/..."` so the shell expands it first.
- The `--terminal` handle is the `handle` field (`term_…`) from `orca terminal list --json`, never the `paneKey` from `orca worktree ps` — a paneKey is rejected as `terminal_handle_stale`, even with `--retry-request`.
- `active`/`current` selectors resolve from the caller's cwd. From the workspace root they resolve to the root, not the target project — always pass explicit `--repo path:...` / `--worktree ...` selectors.
- Long `orca terminal send --text` payloads get truncated in transit (the agent receives only the tail). Write long briefs to a file and send a one-line pointer to it.
- A worktree branch can have **no upstream configured at all** (`git rev-parse @{u}` → `fatal: no upstream configured`) even while a live agent is working in it — the branch was never pushed. Report "no upstream yet", not "0 ahead".
- `linkedPR.state: "merged"` does not mean the worktree was cleaned up — merged-PR worktrees can sit around clean and idle indefinitely as reclaimable leftovers.
- `orca worktree rm` refuses to delete a worktree with untracked files. Tool-generated directories that are not gitignored (caches, local registries) block every routine cleanup until removed or ignored.
- Removing a worktree whose commits were never pushed leaves them unreferenced but still present: `git cat-file -e <sha>^{commit}` finds them, and `git branch rescue/<name> <tip-sha>` anchors them before `git gc` prunes them. Uncommitted work from a removed worktree may survive as a dangling stash commit visible via `git fsck --lost-found`.
- Not every worktree under the worktree root follows `<repo>/<branch-slug>` nesting — some are flat siblings. List the top level, then for each entry check whether it is a repo-name directory (descend) or already a worktree (has a `.git` file).
