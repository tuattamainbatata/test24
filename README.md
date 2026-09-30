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

This repo enables two Claude Code plugins. Both marketplaces and both plugins are declared
in `.claude/settings.json`, so anyone who opens the project in Claude Code and trusts the
folder gets them automatically:

```json
{
  "extraKnownMarketplaces": {
    "everything-claude-code": {
      "source": {
        "source": "github",
        "repo": "worldflowai/everything-claude-code"
      }
    },
    "ui-ux-pro-max-skill": {
      "source": {
        "source": "github",
        "repo": "nextlevelbuilder/ui-ux-pro-max-skill"
      }
    }
  },
  "enabledPlugins": {
    "everything-claude-code@everything-claude-code": true,
    "ui-ux-pro-max@ui-ux-pro-max-skill": true
  }
}
```

Equivalent manual install from inside Claude Code:

```
/plugin marketplace add worldflowai/everything-claude-code
/plugin install everything-claude-code@everything-claude-code

/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
/plugin install ui-ux-pro-max@ui-ux-pro-max-skill
```

### everything-claude-code

[Repo](https://github.com/worldflowai/everything-claude-code) — general development
workflow: agents, skills, commands, rules, and hooks.

| Type | Items |
|------|-------|
| **Commands** | `/plan`, `/tdd`, `/verify`, `/code-review`, `/e2e`, `/eval`, `/learn`, `/orchestrate`, `/build-fix`, `/checkpoint`, `/refactor-clean`, `/test-coverage`, `/update-docs`, `/update-codemaps`, `/setup-pm` |
| **Agents** | planner, architect, tdd-guide, code-reviewer, security-reviewer, build-error-resolver, e2e-runner, refactor-cleaner, doc-updater |
| **Skills** | coding-standards, backend-patterns, frontend-patterns, tdd-workflow, security-review, verification-loop, eval-harness, continuous-learning, strategic-compact, clickhouse-io |
| **Rules** | coding-style, git-workflow, security, testing, performance, patterns, agents, hooks |
| **Hooks** | SessionStart / SessionEnd / PreCompact / PreToolUse / PostToolUse / Stop automation (memory persistence, strategic compaction, continuous learning) |

The plugin's hooks and scripts are Node.js based and detect the package manager from the
project — this repo's `package-lock.json` resolves that to npm with no extra configuration.

### ui-ux-pro-max

[Repo](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) — UI/UX design
intelligence, backed by a local searchable database of design styles, palettes, font
pairings, chart recipes, and per-stack guidelines.

| Skill | What it covers |
|-------|----------------|
| **ui-ux-pro-max** | Core design intelligence for pages, components, design systems, accessibility, and interaction |
| **ui-styling** | shadcn/ui, Radix, and Tailwind styling; canvas-based visual designs |
| **design** | Brand identity, design tokens, logo generation, corporate identity deliverables |
| **design-system** | Three-layer token architecture (primitive → semantic → component) and component specs |
| **brand** | Brand voice, messaging frameworks, asset management, style guides |
| **slides** | Strategic HTML presentations with Chart.js and design tokens |
| **banner-design** | Social, ad, hero, and print banners with multiple art directions |

The skills activate on their own for UI/UX work; they can also be driven directly, e.g.

```bash
python3 <skill-path>/ui-ux-pro-max/scripts/search.py "fintech banking" --design-system
```

**Requires Python 3** for that search script (standard library only — it makes no network
calls and installs nothing).
