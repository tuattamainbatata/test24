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

## Claude Code setup

This repo is configured to use the
[everything-claude-code](https://github.com/worldflowai/everything-claude-code) plugin — a
collection of Claude Code agents, skills, commands, rules, and hooks. The marketplace and
plugin are declared in `.claude/settings.json`, so anyone who opens this project in Claude
Code and trusts the folder gets them automatically:

```json
{
  "extraKnownMarketplaces": {
    "everything-claude-code": {
      "source": {
        "source": "github",
        "repo": "worldflowai/everything-claude-code"
      }
    }
  },
  "enabledPlugins": {
    "everything-claude-code@everything-claude-code": true
  }
}
```

Equivalent manual install from inside Claude Code:

```
/plugin marketplace add worldflowai/everything-claude-code
/plugin install everything-claude-code@everything-claude-code
```

### What it adds

| Type | Items |
|------|-------|
| **Commands** | `/plan`, `/tdd`, `/verify`, `/code-review`, `/e2e`, `/eval`, `/learn`, `/orchestrate`, `/build-fix`, `/checkpoint`, `/refactor-clean`, `/test-coverage`, `/update-docs`, `/update-codemaps`, `/setup-pm` |
| **Agents** | planner, architect, tdd-guide, code-reviewer, security-reviewer, build-error-resolver, e2e-runner, refactor-cleaner, doc-updater |
| **Skills** | coding-standards, backend-patterns, frontend-patterns, tdd-workflow, security-review, verification-loop, eval-harness, continuous-learning, strategic-compact, clickhouse-io |
| **Rules** | coding-style, git-workflow, security, testing, performance, patterns, agents, hooks |
| **Hooks** | SessionStart / SessionEnd / PreCompact / PreToolUse / PostToolUse / Stop automation (memory persistence, strategic compaction, continuous learning) |

The plugin's hooks and scripts are Node.js based and detect the package manager from the
project — this repo's `package-lock.json` resolves that to npm with no extra configuration.
