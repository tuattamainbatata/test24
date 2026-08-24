# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is not an application with its own source code — it's a thin local-setup wrapper around
[OmniRoute](https://github.com/diegosouzapw/OmniRoute), an external AI gateway package installed
as the single dependency `omniroute` (see `package.json`). All gateway/routing/dashboard logic
lives inside that npm package, not in this repo. There is no `src/` to build, lint, or test here.

## Commands

- `npm install` — installs the `omniroute` dependency.
- `npm start` — runs the `omniroute` CLI (defined as the `start` script in `package.json`). This
  launches the gateway; the dashboard becomes available at `http://localhost:20128`.

There are no build, lint, or test scripts in this repo.

## Usage

1. Run `npm start`, open the dashboard, and connect a provider (e.g. a free-tier provider such as
   Kiro AI or OpenCode Free).
2. Point an IDE or tool (Claude Code, Cursor, Cline, etc.) at `http://localhost:20128/v1` using an
   API key generated from the dashboard.
3. Set the model to `auto` to let OmniRoute route requests across providers with fallback and cost
   optimization.

Alternative install/run paths (not used by this repo's `package.json`, but available upstream):
global CLI (`npm install -g omniroute && omniroute`) or Docker
(`docker run -d -p 127.0.0.1:20128:20128 diegosouzapw/omniroute:latest`).
