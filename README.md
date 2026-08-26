# OmniRoute

Local setup for [OmniRoute](https://github.com/diegosouzapw/OmniRoute), an open-source AI
gateway that aggregates 290+ AI providers (90+ with free tiers) behind a single
OpenAI-compatible endpoint.

## Install

```bash
npm install
```

## Run

```bash
npm start
```

This launches OmniRoute via its `omniroute` CLI. The dashboard is available at
`http://localhost:20128` once the process is running.

## Usage

1. Open the dashboard and connect a provider (e.g. a free-tier provider such as Kiro AI or
   OpenCode Free).
2. Point your IDE or tool (Claude Code, Cursor, Cline, etc.) at `http://localhost:20128/v1`
   with an API key generated from the dashboard.
3. Set the model to `auto` to let OmniRoute route requests across providers with intelligent
   fallback and cost optimization.

## Alternatives

- **Global CLI**: `npm install -g omniroute && omniroute`
- **Docker**: `docker run -d -p 127.0.0.1:20128:20128 diegosouzapw/omniroute:latest`

See the [upstream repository](https://github.com/diegosouzapw/OmniRoute) for full
documentation.

## Ruflo

This project also installs [Ruflo](https://github.com/ruvnet/ruflo) (npm package
`ruflo`), an AI agent orchestration platform / meta-harness for Claude Code. It adds
multi-agent swarms, persistent memory, self-learning hooks and an MCP server.

`npm install` (above) pulls it in, so no extra step is needed. Verify it with:

```bash
npm run ruflo -- --version
```

### Already initialized

`ruflo init` has been run and its configuration is committed:

| Path | What it is |
| --- | --- |
| `CLAUDE.md` | Swarm guidance loaded by Claude Code |
| `.claude/` | 30 skills, 16 commands, 17 agents, hook helpers + `settings.json` |
| `.claude-flow/config.yaml` | V3 runtime config (hierarchical-mesh, 15 agents, hybrid memory) |
| `.mcp.json` | Registers the `claude-flow` MCP server (`npx ruflo@latest mcp start`) |
| `.agents/skills/ruflo/SKILL.md` | Core skill for cross-agent discovery |

Runtime state (`.swarm/`, `ruvector.db`, `.claude-flow/data|logs|sessions|metrics`)
is gitignored and regenerates locally.

Note: `.claude/settings.json` enables 7 Claude Code hook types for this project, so
Claude Code sessions here run Ruflo's hook handler.

### Use it

```bash
npm run ruflo:status            # show system status
npm run ruflo -- swarm --help
npm run ruflo -- daemon start   # background workers (stop with: daemon stop)
npm run ruflo:init -- --force   # re-scaffold config
```

`npm run ruflo -- <command>` forwards any Ruflo command (`agent`, `swarm`, `memory`,
`task`, `hive-mind`, `mcp`, `doctor`, ...). Run `npm run ruflo -- --help` for the full
list.

### Wire it into Claude Code

```bash
claude mcp add claude-flow -- npx ruflo@latest mcp start
```

### Alternatives (Ruflo)

- **Global CLI**: `npm install -g ruflo@latest && ruflo init wizard`
- **One-off**: `npx ruflo@latest init wizard`
- **Install script**: `curl -fsSL https://cdn.jsdelivr.net/gh/ruvnet/ruflo@main/scripts/install.sh | bash`

See the [Ruflo repository](https://github.com/ruvnet/ruflo) for full documentation.

## Agent Reach

[Agent Reach](https://github.com/Panniantong/Agent-Reach) gives an AI agent read access
to the internet — web pages, RSS, YouTube, GitHub, Reddit, Twitter/X, Bilibili,
Xiaohongshu and more — behind one CLI. It is a *machine-level* tool, not a dependency of
this project: by design it keeps all of its files outside the workspace, so nothing here
imports it and `npm install` does not fetch it.

Install it per machine (Python 3.10+):

```bash
pipx install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto            # read-only check, no changes
agent-reach install --env=auto --system   # install/configure the base channels
```

If your Python is externally managed (PEP 668) and `pipx` is unavailable, use a venv:

```bash
python3 -m venv ~/.agent-reach-venv
~/.agent-reach-venv/bin/pip install https://github.com/Panniantong/agent-reach/archive/main.zip
```

Where it puts things:

| Path | What |
| --- | --- |
| `~/.agent-reach/` | Config and tokens (mode 600) |
| `~/.claude/skills/agent-reach/` | The skill Claude Code loads |
| `~/.config/yt-dlp/config` | `--js-runtimes node` for YouTube |

`agent-reach doctor` reports which of the 15 channels are live. The base install covers
web/RSS/YouTube/GitHub/Exa search; the rest need per-channel logins or cookies:

```bash
agent-reach install --system --channels=twitter,reddit,bilibili   # pick channels
agent-reach uninstall                                             # remove everything
```
