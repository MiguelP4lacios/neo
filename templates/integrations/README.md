# Optional scouts

These are **templates, not active agents**. The plugin only registers what is in `agents/`; nothing here runs until you copy it into your workspace.

| Template | For | Playbook it owns |
|---|---|---|
| `neo-jira-scout.md` | Read-only view of an issue tracker (written for Jira through the Atlassian MCP server; also works for Linear or GitHub Issues after editing) | `playbooks/issue-tracker.md` |
| `neo-infra-scout.md` | Read-only state of Kubernetes clusters, a GitOps config repo and a log backend | `playbooks/infrastructure.md` |

## Enable one

From your workspace root (the folder where you ran `/neo:neo-init`):

1. Copy the agent: `cp <plugin dir>/templates/integrations/neo-jira-scout.md .claude/agents/`
   (Find `<plugin dir>` with `claude plugin details neo`, or copy the file from the GitHub repo.)
2. Copy its playbook if you do not have one: `cp <plugin dir>/templates/integrations/playbooks/issue-tracker.md .claude/agents/agent-notes/playbooks/`
3. Adapt the agent file — every `<ANGLE-BRACKET>` placeholder:
   - **Tracker scout**: board/project keys, the user's account, and the `tools:` list. MCP tool names are `mcp__<server name>__<tool>`; the list ships with the Atlassian server's names — replace them with your server's (run `/mcp` to see them). For GitHub Issues, replace the MCP tools with `Bash` and use `gh issue list/view`.
   - **Infra scout**: cluster contexts, namespaces, the GitOps repo directory, the log backend and how to reach it.
4. Register it: add a row to `.claude/agents/agent-notes/playbooks/README.md` (file table + scout table) and mention it in the **Neo agent roster** paragraph of the workspace `CLAUDE.md`.
5. Start a new session from the workspace root. Workspace agents are invoked by their bare name (`neo-jira-scout`), not `neo:`-prefixed.

Both templates keep the scout contract: read the owned playbook at start, append distilled facts at end, never mutate anything outside that playbook, always end with the fixed report format.
