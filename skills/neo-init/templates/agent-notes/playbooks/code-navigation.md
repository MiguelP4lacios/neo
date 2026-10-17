# Playbook — Reading code in this workspace

How to find out what code does, and the ways a static read lies.

Standing facts about this workspace. Not dated events — see `agent-notes/YYYY/` for those. The bullets below are generic, pre-filled; append per-repo quirks as you learn them.

- Read a project's `CLAUDE.md` before drawing any conclusion about it.
- Read shipped code from the remote branch — `git show origin/<branch>:<path>` — not the working tree. Local checkouts are often behind and on unrelated feature branches.
- Call volume is not evidence that something works. Measure what a thing RETURNS, not how often it is called.
- Multi-line route or handler registrations defeat a regex that requires method and path on the same line — search for the path string itself.
- A diff hunk that appends entries to a long array does not show the array's owning key, so a diff-only reader cannot tell `include` from `exclude`. Read the full file before judging such a change.
- Test runners configured with an explicit include allowlist (not a glob) silently skip new specs that are not listed — confirm a new test actually runs.
