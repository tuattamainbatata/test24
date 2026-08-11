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

## OpenRouter Reasoning Tokens

This project includes support for tracking reasoning tokens when using OpenRouter models.

### Setup

1. Copy `.env.example` to `.env` and add your OpenRouter API key:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your API key:
   ```
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

### Usage

Use the provided utilities to stream or fetch responses with reasoning token tracking:

```typescript
import { streamWithReasoningTokens } from './src/reasoning-tokens.js';

const result = await streamWithReasoningTokens("Your question here");
console.log(`Reasoning tokens: ${result.usage.reasoningTokens}`);
```

### Examples

Run the example demonstrations:

```bash
npm run example:reasoning-tokens
```

This will show:
- Streaming example with token tracking
- Non-streaming example with token tracking
- Token usage breakdown (prompt, completion, reasoning, total)

## Alternatives

- **Global CLI**: `npm install -g omniroute && omniroute`
- **Docker**: `docker run -d -p 127.0.0.1:20128:20128 diegosouzapw/omniroute:latest`

See the [upstream repository](https://github.com/diegosouzapw/OmniRoute) for full
documentation.
