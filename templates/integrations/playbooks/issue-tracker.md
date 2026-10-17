# Playbook — Issue tracker and ticket state

What the board does and does not tell you about reality.

Standing facts about this workspace. Not dated events — see `agent-notes/YYYY/` for those. The bullets below are generic, pre-filled; append this workspace's board quirks as you learn them.

- Boards drift from reality: work can be live in production while its ticket still says To Do. Never report ticket status as project status — cross-check against git and the running system.
- A "discarded" status (e.g. `Trash`, `Won't do`) may sit in the `done` status category, so a `statusCategory != Done` filter hides it while a Done filter counts it as completed work. Read the status name, not just the category.
- A ticket's exit criteria can reference tickets that were later discarded. Verify each gate ticket still exists and is live before reporting a gate as open.
- Broad queries overflow the context. Always request a narrow explicit field list (e.g. `summary`, `status`, `assignee`, `updated`).
- Transient anti-bot or rate-limit pages can come back instead of JSON — retry later; never try to solve a challenge.
