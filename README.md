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

## Configuration

The dashboard generates a gateway API key that your IDE/tools use to authenticate to the
local OmniRoute endpoint. Keep it out of source control:

1. Copy `.env.example` to `.env` and paste the generated key into `OMNIROUTE_API_KEY`.
   `.env` is gitignored, so the real key never gets committed.
2. Point your tool at OmniRoute using the values from `.env`:
   - **Base URL**: `OMNIROUTE_BASE_URL` (`http://localhost:20128/v1`)
   - **API key**: `OMNIROUTE_API_KEY`

   For example, with Claude Code, set `ANTHROPIC_BASE_URL` and `ANTHROPIC_API_KEY` (or your
   tool's equivalent env vars) to these values before launching it.
3. If a key is ever exposed (e.g. pasted somewhere public), regenerate it from the OmniRoute
   dashboard and update your local `.env`.

## Alternatives

- **Global CLI**: `npm install -g omniroute && omniroute`
- **Docker**: `docker run -d -p 127.0.0.1:20128:20128 diegosouzapw/omniroute:latest`

See the [upstream repository](https://github.com/diegosouzapw/OmniRoute) for full
documentation.
