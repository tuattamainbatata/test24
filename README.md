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
    "ecc": {
      "source": {
        "source": "github",
        "repo": "affaan-m/ECC"
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
    "ecc@ecc": true,
    "ui-ux-pro-max@ui-ux-pro-max-skill": true
  }
}
```

Equivalent manual install from inside Claude Code:

```
/plugin marketplace add https://github.com/affaan-m/ECC
/plugin install ecc@ecc

/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
/plugin install ui-ux-pro-max@ui-ux-pro-max-skill
```

### ecc

[Repo](https://github.com/affaan-m/ECC) — the ECC operator layer for general development
work. Successor to (and superset of) `everything-claude-code`, which this repo used
previously; do not enable both, since their agents, commands, and hooks collide.

| Type | Items |
|------|-------|
| **Agents** | 71, including planner, architect, code-architect, code-reviewer, security-reviewer, tdd-guide, build-error-resolver, e2e-runner, doc-updater, plus per-language reviewers and build resolvers |
| **Skills** | 311, spanning backend/frontend patterns, TDD, security review, accessibility, agent harness construction, benchmarking, and per-stack guides |
| **Commands** | 97, including `/code-review`, `/plan`, `/checkpoint`, `/build-fix`, `/feature-dev`, `/refactor-clean`, `/test-coverage`, `/update-docs`, the `epic-*` set, and per-language `*-build` / `*-review` / `*-test` commands |
| **Hooks** | Lifecycle, quality, and safety automation (memory persistence among them), loaded from the plugin's own `hooks/hooks.json` |

Two notes from ECC's docs:

- **Don't layer installs.** The marketplace install above is complete on its own — don't
  also run ECC's `install.sh`, and don't copy its hooks into `settings.json`. Claude Code
  auto-loads a plugin's `hooks/hooks.json`, so duplicating them fires every hook twice.
- **Rules aren't distributable via plugins.** ECC's rule packs (`common` plus per-language
  packs for typescript, python, rust, go, react, and ~17 others) have to be copied by hand
  if you want them:

  ```bash
  git clone https://github.com/affaan-m/ECC.git
  mkdir -p ~/.claude/rules/ecc
  cp -R ECC/rules/common ~/.claude/rules/ecc/
  ```

The plugin exposes `hooks_enabled` (default on) and `hook_profile` (`minimal` / `standard`
/ `strict`, default `standard`) as user config, adjustable via `/plugin`.

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
