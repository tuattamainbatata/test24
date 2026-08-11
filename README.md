# test24

Minimal setup for calling AI models through [OpenRouter](https://openrouter.ai), a
hosted API that routes requests to many model providers through official
partnerships, exposed via an OpenAI-compatible endpoint.

## Setup

1. Create an account and API key at https://openrouter.ai/keys.
2. Install dependencies:

   ```bash
   npm install
   ```

3. Export your key:

   ```bash
   export OPENROUTER_API_KEY=sk-or-...
   ```

## Run

```bash
npm start
```

This sends a single test chat completion through OpenRouter (default model
`openai/gpt-4o-mini`; override with `OPENROUTER_MODEL`).

## Usage

Point any OpenAI-compatible tool at `https://openrouter.ai/api/v1` with your
OpenRouter API key. See https://openrouter.ai/docs for the full model catalog,
pricing, and rate limits.

---

**Note:** an earlier version of this repo set up
[OmniRoute](https://github.com/diegosouzapw/OmniRoute) instead. That was
removed after its own documentation showed its default configuration routes
traffic through a provider whose ToS forbids third-party proxy use, and that
it ships opt-in features designed to spoof official CLI fingerprints to
evade providers' bot/abuse detection. OpenRouter is used here instead because
it operates through official provider agreements rather than detection
evasion.
