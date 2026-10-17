# Playbook — Branches, repos and CI naming

Where repos live, how branches are named and validated, and the git traps that produce false positives.

Standing facts about this workspace. Not dated events — see `agent-notes/YYYY/` for those. The bullets below are generic git behaviour, pre-filled; append this workspace's branch-naming rules, CI gates and repo quirks as you learn them.

- Resolve a repo's remote with `git -C <repo> remote get-url origin` — never hardcode owner/repo names.
- `git rev-list --left-right --count @{u}...HEAD` gives `"<behind> <ahead>"` fully read-only (uses cached remote-tracking refs, no fetch) — the default for ahead/behind.
- `git log --all --grep=X --grep=Y -i` ORs the patterns AND matches the full commit body, not just the subject — e.g. a keyword that also appears in commit trailers produces hundreds of false positives. For targeted keyword recon, pipe `git log --pretty=format:'%h|%ad|%an|%s'` through `rg -i` (subject only) or use `git log -S "<exact string>"` (pickaxe).
- A checked-out feature branch can already be merged upstream while `git status` still shows modified/untracked files — that is real local work on top of a merged branch, not checkout noise. Flag it.
- Companion PRs for the same ticket across two repos often share the exact same branch name — comparing `headRefName` across repos is a fast way to spot twin stale PRs.
- A release merge commit (e.g. `develop` → `main`) is only contained in the target branch; `git branch -r --contains <sha>` returning just `origin/main` is normal, not a skipped branch. Check `%P` (parent count) to confirm a real two-parent merge.
- One ticket can span many PRs across several repos — don't assume one PR is a ticket's full history; sweep every repo before picking "the" PR.
- A case-only branch rename fails on macOS with "already exists" (case-insensitive filesystem). Rename in two steps through a temporary name; do NOT delete the apparently-existing branch first.
- If CI validates branch names or PR titles (for example requiring an uppercase ticket key), note the exact regex here: `orca worktree create --name <slug>` derives the branch from the name, so a wrong slug makes every PR born red.
