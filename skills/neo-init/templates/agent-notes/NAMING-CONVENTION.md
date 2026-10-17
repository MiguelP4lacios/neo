# Agent Notes — Naming Convention

Neo's durable work record. One file per finding, decision, verification or procedure.

Read [README.md](./README.md) first: it is the index, and every entry carries a **Read when** line so you can pick the right file without opening any others.

## Design rule

**Nothing in the folder structure names a current project.** Directories are dates, which never need renaming. Type lives in the filename. Semantic grouping — by area, epic, ticket, whatever matters this quarter — lives in the **index**, because an index is free to re-group and a directory tree is not.

## Pattern

```
YYYY/MM/YYYY-MM-DD-<TYPE>-<descriptive-topic>.md
```

| Component | Format | Example |
|---|---|---|
| `YYYY/MM/` | year and month directory | `2026/01/` |
| `YYYY-MM-DD` | ISO 8601, the date the work was done | `2026-01-15` |
| `TYPE` | three uppercase letters, from the table below | `INV` |
| `descriptive-topic` | kebab-case, lowercase | `acme-api-endpoint-inventory` |

Example: `2026/01/2026-01-15-INV-acme-api-endpoint-inventory.md`

Date first means the filename sorts chronologically anywhere it appears — in a listing, in an index, in a search result.

## Types

| Type | What it holds | Written when |
|---|---|---|
| `INV` | Inventory or reconnaissance — what exists, measured | A survey was run against the real system |
| `VER` | Verification — evidence that something works, or does not | A claim was tested rather than assumed |
| `DEC` | Decision and its reasoning, including what was rejected | A fork was resolved and should not be re-litigated |
| `INC` | Incident and recovery — what broke, why, what fixed it | Something failed in a shared environment |
| `RUN` | Runbook — an executable procedure with its traps | A procedure will be repeated by someone else |
| `HND` | Handoff — the current state of a workstream | Someone else may need to pick this up |

## The one exception: `runbooks/`

A runbook is not a dated event; it is a living procedure. Filing it under the month it was written would bury the current version. Runbooks live in `runbooks/` with no date:

```
runbooks/RUN-<descriptive-topic>.md
```

Edit them in place. If a procedure changes materially, say so inside the file.

## Required header

Every note opens with a metadata line the index is built from:

```markdown
# <Title>

**Area:** <area> · **Date:** YYYY-MM-DD · **Tickets:** [KEY](url), ...

**Read when:** <the question this file answers>
```

`Area` is free text and deliberately not a directory — it is how the index groups, and it can be renamed without moving a single file. Omit `Tickets` when there is no tracker.

## Rules

- Facts and evidence, not narrative. If a number is quoted, say where it was measured.
- State whether a claim is **verified against the running system** or **inferred from an artifact**. Most wrong calls come from confusing the two.
- A file is never rewritten to change history. Supersede it with a new note and link back (and mark the old entry **SUPERSEDED** in the index). Runbooks are the exception — they are meant to be edited.
- **Add it to `README.md` with its Read when line.** An unindexed note does not exist.
