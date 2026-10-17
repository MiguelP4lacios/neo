# Neo — Agent Notes Index

Neo's durable work record: what was found, what was decided, what was verified, and how to repeat it.

**Start here.** Every entry carries a **Read when** line. Scan the index, open the one file that answers your question. Do not grep the directory.

Naming rules: [NAMING-CONVENTION.md](./NAMING-CONVENTION.md). Files live under `YYYY/MM/` and never move; this index does the grouping, so areas can be renamed or merged without touching a file.

## Where else things live

| Where | Holds | Read it when |
|---|---|---|
| `agent-notes/` (here) | The work record: findings, decisions, verifications, handoffs, runbooks | You need the state of something, or how it was decided |
| [`playbooks/`](./playbooks/) | Each scout's **operational playbook** — which command works here, which traps to avoid | You are about to run recon and want to skip a known mistake |
| Engram (`project: "neo"`) | Session-level memory, searchable, chronological | You remember something happened but not where it was written |

---

# By area

<!--
Add one `## <Area>` section per workstream. Optional one-line **State:** under the heading.
Each entry looks like this (fictional example — delete it once you have real notes):

## Search performance

**State:** fix shipped and verified; nothing pending.

- [2026-01-15 · VER · acme-api search index is live](./2026/01/2026-01-15-VER-acme-api-search-index-live.md)
  - **Key facts:** p95 search latency fell from 1.8 s to 140 ms, measured on the production dashboard; the old full-scan query path reads zero calls since the deploy
  - **Read when:** someone asks whether the search fix is live, or you want the pattern for proving a migration took
-->

_No areas yet. The first note you write creates the first area._

---

# Runbooks

Living procedures, not dated events. Edit in place. See [runbooks/README.md](./runbooks/README.md).

_None yet._

---

# Playbooks

How this workspace actually behaves: which command works, which output lies, which trap has already been paid for. Living documents, no dates. A playbook is read **before** touching something; a note is read to understand what happened.

**[playbooks/README.md](./playbooks/README.md)** is the map — topic files plus which scout owns which.

---

# Chronological

<!-- One line per month, e.g.: - **2026/01** — [`2026/01/`](./2026/01/) — search index verification, release checklist -->

_Empty._

---

## Writing a new note

1. `YYYY/MM/YYYY-MM-DD-<TYPE>-<topic>.md`, or `runbooks/RUN-<topic>.md` for a procedure.
2. Open with the header: `**Area:** … · **Date:** … · **Tickets:** …` then a `**Read when:**` line.
3. Say where each number was measured, and whether a claim is **verified against the running system** or **inferred from an artifact**.
4. Add it here under its area, with its Read when line. An unindexed note does not exist.
