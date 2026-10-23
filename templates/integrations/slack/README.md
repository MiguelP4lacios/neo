# Slack identity for Neo (optional)

Gives Neo its own Slack bot user. Slack becomes a trigger for what you already do by hand —
paste a thread link into Neo — and Neo answers in Slack as itself, never as you.

This is a **template, not an active part of the plugin**. Nothing runs until you set it up.

## What it does

| Event | What happens |
|---|---|
| **You** DM Neo, or mention `@Neo` in a thread | 👀 on your message, then a Neo session opens in an Orca terminal (or the thread's existing session gets the new message) and Neo DMs you the link |
| **Someone else** DMs Neo, mentions it, or mentions **you** | Nothing runs. Neo DMs you an excerpt with **Start session** / **Dismiss** |
| Someone else writes in a thread that already has a live session | You get the same DM, with **Add to session** instead of Start |
| The session wants to reply | `neo-say` queues a draft; the bridge DMs you a preview with **Post as Neo** / **Discard**. Only your click posts it |

One session per thread, one live draft per thread. Each session follows the
[`neo-slack-triage`](./skills/neo-slack-triage/SKILL.md) skill: triage, read-only investigation,
root cause with evidence, a proposed fix, and it **asks you** before deploying the fix to a worktree
with `neo-deploy`.

## Security model

Enforced in code, not only in prompts:

- **One owner** (`NEO_OWNER_ID`). Only your messages and your button clicks start sessions or post.
- Anyone else is **reported to you**, never acted on. Bots are ignored unless listed in
  `NEO_TRUSTED_BOTS`, and those only count when they mention you.
- The bridge never posts in channels on its own. Replies go out only after your **Post** click; each
  draft can be posted once.
- Other people's message text never goes into a session prompt: the session gets the link and reads
  the thread as data.
- Tokens live in the macOS Keychain, never in env vars, files or process arguments. The bridge is the
  only process that reads them: `neo-say` just writes a draft file, so a session never needs a token.
- Also deny Keychain reads to Claude Code in your Neo workspace (`.claude/settings.local.json`), so a
  session cannot fetch the bot token and post around the approval step:
  ```json
  { "permissions": { "deny": ["Bash(security find-generic-password:*)", "Bash(security find-internet-password:*)",
                                "Bash(security dump-keychain:*)", "Bash(security -i:*)"] } }
  ```
  Deny rules match the command prefix, so treat them as a guard against mistakes, not a hard boundary.

Mentions of you are found with user-level events: the bridge receives every message in **your**
channels and acts only on `<@you>`. Nothing is stored; the log keeps the event type only.

## Requirements

macOS, Orca with your Neo workspace registered, Claude Code,
[`uv`](https://docs.astral.sh/uv/), and a Slack workspace where you can install an app.

## Setup

### 1. Create the Slack app
[api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From a manifest** →
pick the workspace → paste [`slack-app-manifest.yaml`](./slack-app-manifest.yaml). Choose
"From a manifest", not the "AI agent" template. Set the name and icon in **Basic Information**
(the name is only a label; see `NEO_SLACK_NAME`).

### 2. Tokens
- **App-Level Token** (Basic Information → App-Level Tokens), scope `connections:write`. New apps
  may have **token rotation** on, and it cannot be turned off: then you get an access token
  `xoxe.xapp-…` (12 h) and a refresh token `xoxe-…`. The bridge refreshes it before it expires.
- **Bot User OAuth Token** `xoxb-…` (Install App → Install to Workspace). The install also asks you
  to authorize the user scopes; no user token needs to be stored.
- **Client ID** and **Client Secret** (Basic Information → App Credentials) — used only to refresh
  the rotating app token. The Client ID is digits with a dot; do not mix it up with the Signing
  Secret.

Store them in the Keychain **from the clipboard**. The interactive `security … -w` prompt silently
cuts input at 128 characters, which breaks the long `xoxe` tokens. Copy each value, then run in a
real terminal:

```sh
security add-generic-password -U -a "$USER" -s neo-slack-bot-token         -w "$(pbpaste)"
security add-generic-password -U -a "$USER" -s neo-slack-app-token         -w "$(pbpaste)"
security add-generic-password -U -a "$USER" -s neo-slack-app-refresh-token -w "$(pbpaste)"
security add-generic-password -U -a "$USER" -s neo-slack-client-id         -w "$(pbpaste)"
security add-generic-password -U -a "$USER" -s neo-slack-client-secret     -w "$(pbpaste)"
pbcopy < /dev/null
```

Never print a stored token to check it: `security find-generic-password -s <name>` (without `-w`)
shows that the item exists.

### 3. Install the files
```sh
mkdir -p ~/.config/neo-slack
cp -R bridge <your Neo workspace>/.claude/neo-slack-bridge
cp -R skills/neo-slack-triage <your Neo workspace>/.claude/skills/
echo '{"owner_id": "<YOUR_SLACK_USER_ID>", "slack_name": "Neo"}' > ~/.config/neo-slack/config.json
```
Copy `bridge/neo-say` to a directory on your `PATH` (e.g. `~/.local/bin`) and set `BRIDGE_DIR`
in it.

### 4. Find the Orca selector
A folder workspace only resolves in `orca terminal create` as `id:<worktreeId>`; `path:` does not
match folders. Get it from `orca worktree ps --json` (the `worktreeId` of your Neo workspace,
e.g. `folder:<uuid>` → selector `id:folder:<uuid>`).

### 5. Try it in the foreground
```sh
cd <bridge dir>
NEO_OWNER_ID=<YOUR_SLACK_USER_ID> NEO_WORKSPACE=id:folder:<uuid> uv run bridge.py
```
Expect `app token rotated` (first run) and `Neo bridge connected`. DM Neo a thread link: an Orca
terminal should open. Then stop it with Ctrl+C.

### 6. Run it as a service
Fill every `__PLACEHOLDER__` in [`launchd/com.neo.slack-bridge.plist`](./launchd/com.neo.slack-bridge.plist),
copy it to `~/Library/LaunchAgents/`, then:
```sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.neo.slack-bridge.plist
launchctl print gui/$(id -u)/com.neo.slack-bridge | grep -E 'state|pid'
tail -f ~/Library/Logs/neo-slack-bridge.log
```
Restart after a code change: `launchctl kickstart -k gui/$(id -u)/com.neo.slack-bridge`. After an
env change in the plist, `bootout` then `bootstrap` (kickstart does not reload env).

## Configuration

| Variable | Meaning |
|---|---|
| `NEO_OWNER_ID` | Your Slack user id. The only person Neo works for |
| `NEO_WORKSPACE` | Orca selector of your Neo workspace (`id:folder:<uuid>`) |
| `NEO_SLACK_NAME` | Name shown in Slack texts and buttons (default `Neo`); also `slack_name` in `config.json` for `neo-say` |
| `NEO_TRUSTED_BOTS` | Comma-separated user/bot ids whose mentions of you count (e.g. a ticket bot) |
| `NEO_MAX_SESSIONS_PER_HOUR` | Cap on new sessions (default 6) |
| `NEO_WATCHDOG_SECONDS` | Exit (and be relaunched) after this long with no events (default 900) |
| `NEO_ORCA_BIN`, `NEO_CLAUDE_CMD` | Absolute paths when running under launchd |

## Troubleshooting

- **Neo ignores a mention.** Find the message time and look for `event type=` at that second in the
  log. Present → it was filtered; absent → the connection was down.
- **A reply did not post.** The draft is kept and the DM keeps its buttons with the error; fix the cause
  (for example invite the bot) and click Post again.
- **Neo looks connected but nothing arrives.** The watchdog restarts it after `NEO_WATCHDOG_SECONDS`
  of silence. A deliberate stop (missing token, failed refresh) DMs you and exits without relaunch.
- **`invalid_refresh_token`.** Refresh tokens are single-use and the stored pair must match.
  Generate a new app-level token and store both values again from the clipboard.
- **`not_in_channel` when posting.** Invite the bot to that channel.
