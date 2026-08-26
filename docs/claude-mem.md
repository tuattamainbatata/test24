# Claude-Mem

Setup notes for [Claude-Mem](https://github.com/thedotmack/claude-mem) (`claude-mem` v13.x,
Apache-2.0, by [@thedotmack](https://github.com/thedotmack)) — a persistent memory
compression system for Claude Code and other AI coding assistants.

Claude-Mem hooks into the assistant's session lifecycle, captures tool-usage observations,
compresses them into semantic summaries, and injects the relevant history back into future
sessions. Memory lives locally in SQLite (plus a Chroma vector index for hybrid search) under
`~/.claude-mem/`.

## Install

```bash
npm run mem:install
```

That wraps `npx claude-mem install`, an interactive installer that registers the plugin hooks,
sets up the worker service, and installs its runtime dependencies (Bun and `uv`) if they are
missing. Restart Claude Code afterwards — context from previous sessions then appears
automatically at the start of each new one.

Non-interactive variants:

```bash
npx claude-mem install --ide opencode                 # install for another IDE
npx claude-mem install --provider claude              # pick the LLM provider up front
npx claude-mem install --no-auto-start                # skip starting the worker
```

Supported IDE identifiers: `claude-code`, `cursor`, `opencode`, `openclaw`, `windsurf`,
`codex-cli`, `copilot-cli`, `antigravity`, `goose`, `roo-code`, `warp`.

### Alternatives

- **Plugin marketplace** (from inside Claude Code):

  ```
  /plugin marketplace add thedotmack/claude-mem
  /plugin install claude-mem
  ```

- **OpenClaw gateway**: `curl -fsSL https://install.cmem.ai/openclaw.sh | bash`

> **Do not** install it as a project or global npm dependency. Per upstream, `npm install -g
> claude-mem` pulls in the SDK/library only — it does not register the plugin hooks or set up
> the worker service. That is why this repo drives the CLI through `npx` instead of declaring
> `claude-mem` in `dependencies`.

## Everyday commands

| Task | npm script | Underlying command |
| --- | --- | --- |
| Install / re-run the installer | `npm run mem:install` | `npx claude-mem install` |
| Show worker status | `npm run mem:status` | `npx claude-mem status` |
| Start the worker service | `npm run mem:start` | `npx claude-mem start` |
| Stop the worker service | `npm run mem:stop` | `npx claude-mem stop` |
| Diagnose install/runtime health | `npm run mem:doctor` | `npx claude-mem doctor` |
| Update to the latest version | `npm run mem:update` | `npx claude-mem update` |
| Remove plugin and configs | `npm run mem:uninstall` | `npx claude-mem uninstall` |

Other useful CLI commands: `npx claude-mem restart`, `npx claude-mem search <query>`,
`npx claude-mem repair`, `npx claude-mem telemetry status|enable|disable` (telemetry is on by
default and opt-out), and `npx claude-mem server start|stop|status` for the server runtime.

The worker prints a local URL on startup that serves the web viewer — a real-time stream of
captured observations.

## Requirements

- Node.js >= 20 (the package declares `>=20.12.0`)
- Claude Code (or another supported IDE) with plugin support
- Bun — auto-installed by the installer if missing
- `uv` — auto-installed; used for the Python-backed vector search
- SQLite 3 — bundled

## Searching memory

Claude-Mem exposes three MCP search tools designed around a token-efficient three-layer
workflow:

1. `search` — full-text query over the memory index, filterable by type/date/project
   (~50–100 tokens per result)
2. `timeline` — chronological context around a specific observation or query
3. `get_observations` — full details for a batch of IDs (~500–1,000 tokens per result)

Search first, narrow to the interesting IDs, then fetch details — roughly a 10x token saving
over fetching everything up front. The bundled `mem-search` skill drives the same flow from
natural language.

## Configuration

Settings live in `~/.claude-mem/settings.json`, created with defaults on first run. It controls
the AI model, worker port, data directory, log level, and what context gets injected.

Workflow mode and observation language are set with `CLAUDE_MEM_MODE`:

```json
{ "CLAUDE_MEM_MODE": "code--zh" }
```

`code` is the English default; language variants follow `code--<ISO 639-1>` (e.g. `code--ja`,
`code--es`), and there are workflow modes such as `code--chill`. List what is installed with:

```bash
ls ~/.claude/plugins/marketplaces/thedotmack/plugin/modes/
```

Restart Claude Code after changing the mode.

Wrap anything sensitive in `<private>` tags to keep it out of stored memory.

## Troubleshooting

- `npm run mem:doctor` checks Bun, `uv`, and worker health.
- `npx claude-mem repair` re-runs the runtime setup if an install looks corrupted.
- Worker logs: `~/.claude-mem/logs/worker-$(date +%Y-%m-%d).log`
- The plugin also ships a troubleshoot skill — describing the problem to Claude triggers it.

## Links

- Repository: <https://github.com/thedotmack/claude-mem>
- Documentation: <https://docs.claude-mem.ai/>
- Issues: <https://github.com/thedotmack/claude-mem/issues>
