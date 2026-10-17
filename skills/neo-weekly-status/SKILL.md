---
name: neo-weekly-status
description: Format a weekly objectives status report in English - numbered objectives, a/b/c sub-items, outcome-first lines with linked ticket keys and a closing status mark. Governs output shape only; audit with neo-digest first. Trigger - weekly status, status report, weekly objectives, planning prep, 1:1 prep, what did I accomplish this week, objetivos de la semana.
---

# neo-weekly-status

Turn audited objective data (git + issue tracker + Engram + artifacts) into the standard weekly status format. Audit first (see `neo-digest`); this skill governs the OUTPUT shape only.

Ticket links use the **Issue tracker base URL** from the Neo config table in the workspace root's `CLAUDE.md`. When the tracker is `none`, lines carry no keys or links.

## Format contract

- **English**, always — regardless of conversation language.
- **Top level**: objectives numbered `1.` `2.` `3.` in the exact order they were given.
- **Sub-items**: lettered `a.` `b.` `c.`, indented under their objective.
- **Line shape**: outcome-first, one-sentence description, then the hyperlinked ticket key, then the status mark CLOSING the line:
  `Search index migration merged in acme-api (#212) and acme-web [ACME-142](<tracker base URL>ACME-142) ✅`
- Work **without a ticket**: description + status mark, no link — never invent a key.
- Multiple tickets on one line: link each key before the closing mark.
- 🔴 lines name the blocker inside the description; the mark still closes the line.

## Status marks

| Mark | Meaning |
|---|---|
| ✅ | Done / shipped / verified |
| 🟡 | Partial or in progress |
| ❌ | Not touched |
| 🔴 | Blocked — the line MUST name the blocker |

A parent objective takes the weakest meaningful mark of its children (a 🔴 child worth surfacing bubbles up as context, not necessarily as the parent mark).

## Content rules

1. **Evidence only**: every status comes from a verified source (git log, the tracker, Engram, artifacts) — never from conversational memory alone. If the tracker disagrees with git (e.g. merged PR but ticket still To Do), report the truth and flag the stale ticket.
2. **Outcomes, not activity**: "p95 search latency cut from 1.8 s to 140 ms", not "worked on search". Metrics whenever they exist.
3. **Adjacent-work rule**: work that advances an objective under different ticket numbers is listed as a sub-item of that objective with its own linked keys — broad objectives get credit for real work done near them.
4. **Unplanned / focus leaks** section at the end: support bugs, incidents, investigations and reviews that were not in the week's objectives, each with its linked key when one exists. This feeds the "what's pulling you off focus" 1:1 question.
5. Close with a **Priorities for next week** block when the report is for planning: at most 3, each with the metric it moves.
6. **Status marks are for reports, never for plans.** A forward-looking plan uses the same numbering, links and line shape but carries NO status marks — marks appear only when reporting what already happened.
