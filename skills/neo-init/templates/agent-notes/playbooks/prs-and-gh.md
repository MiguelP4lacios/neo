# Playbook — Pull requests and the gh CLI

Reading PR state without guessing, and who actually merges what here.

Standing facts about this workspace. Not dated events — see `agent-notes/YYYY/` for those. The bullets below are generic `gh` behaviour, pre-filled; append this workspace's merge and release conventions as you learn them.

- Ahead/behind a PR branch vs. base, read-only: `gh api repos/<owner>/<repo>/compare/<base>...<head> --jq '{status, ahead_by, behind_by}'`.
- Full PR detail in one call: `gh pr view <n> --repo <owner>/<repo> --json number,title,state,isDraft,mergeable,mergeStateStatus,reviews,baseRefName,headRefName,url`.
- `mergeStateStatus`: `BLOCKED` = a required approval is missing (bot comment-reviews count as `COMMENTED`, not approval); `UNSTABLE` = non-required checks failing or pending; `BEHIND` = behind base; `UNKNOWN` = GitHub has not recomputed it — a stale-PR signal.
- Merge details: `gh pr view <n> --json state,mergedAt,mergeCommit,mergedBy` — `mergeCommit` is a nested `{oid}` object.
- `gh search prs --json` does not support `mergedAt` — cross-check merge dates per PR with `gh pr view`.
- When feature PRs merge into an integration branch and a separate release PR promotes to production, "who deployed X" is the release PR's `mergedBy`, not the feature PR's.
- `gh search prs --owner <org> "<exact phrase>"` searches title, body and comments across every repo the token can see, including repos not cloned here — the next escalation before concluding "no evidence".
- `gh search prs --author @me --state open` is the one-shot cross-repo view of your open PRs; fall back to per-repo `gh pr list --author @me` if search fails on auth or scope.
- `gh ... --jq '<expr with spaces>'` can fail with `unknown argument` — use the `--jq='<expr>'` form.
