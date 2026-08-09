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

## NVIDIA API streaming example

`scripts/nvidia_streaming.py` shows how to stream a chat completion from
NVIDIA's OpenAI-compatible endpoint (`https://integrate.api.nvidia.com/v1`)
using the `openai` Python client.

```bash
pip install -r scripts/requirements.txt
export NVIDIA_API_KEY="nvapi-..."   # get one from https://build.nvidia.com
python scripts/nvidia_streaming.py "your prompt here"
```

## OpenRouter streaming example

`scripts/openrouter_streaming.mjs` streams a chat completion via the
OpenRouter SDK, printing content as it arrives and reporting reasoning
token usage from the final chunk.

```bash
npm install
export OPENROUTER_API_KEY="sk-or-..."   # get one from https://openrouter.ai/keys
node scripts/openrouter_streaming.mjs "your prompt here"
```

## Alternatives

- **Global CLI**: `npm install -g omniroute && omniroute`
- **Docker**: `docker run -d -p 127.0.0.1:20128:20128 diegosouzapw/omniroute:latest`

See the [upstream repository](https://github.com/diegosouzapw/OmniRoute) for full
documentation.
