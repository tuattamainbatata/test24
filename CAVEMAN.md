# Caveman

Local setup for [caveman](https://github.com/JuliusBrussee/caveman), a token-optimization
layer for AI coding agents. Two halves are set up here:

1. **The CLI** (`@caveman-ai/cli`) — an npm dependency of this project.
2. **The Claude Code skills** — vendored into `.claude/skills/`, so `/caveman` works in
   this repo without a global install.

## CLI

Installed with the rest of the project:

```bash
npm install
```

The `caveman` binary requires **Node.js >= 22.13** (this repo was set up on v22.22.2).

```bash
npm run caveman            # top-level help
npm run caveman:setup      # download the companion Go binaries (compression + metering)
npm run caveman:learn      # token-usage report and suggested moves
```

Anything past the script name needs `--` so npm forwards it:

```bash
npm run caveman -- status
npm run caveman -- claude          # run Claude Code on the compression layer
npm run caveman -- run -- <cmd>    # run any other command on the layer
```

`caveman setup --install` fetches the Go binaries that do the actual compression and
metering; until it runs, the CLI works but the compression layer is not active. It is a
network install of prebuilt binaries, so it is left as an explicit step rather than a
postinstall hook.

Global install is the upstream-recommended alternative and does not need this repo:

```bash
npm install -g @caveman-ai/cli && caveman setup --install
```

## Skills

`.claude/skills/` carries the four skills from the upstream Claude Code plugin, plus the
three `cavecrew` subagents in `.claude/agents/`:

| Skill | Use |
|---|---|
| `caveman` | `/caveman lite\|full\|ultra\|off` — terse replies, technical substance intact. |
| `cavecrew` | Decides when to delegate to `cavecrew-investigator` / `-builder` / `-reviewer`. |
| `caveman-compress` | Compress a memory file (`CLAUDE.md`, notes) in place, with a backup. |
| `caveman-stats` | Session token stats — **needs the full plugin install**, see below. |

Compress a file directly, without going through an agent:

```bash
cd .claude/skills/caveman-compress
python3 -m scripts /path/to/NOTES.md
```

It writes the compressed text back over the original and keeps the untouched copy under
`~/.local/share/caveman-compress/backups/`.

### What a skills-only install does not give you

Upstream ships these as a plugin that also registers `SessionStart` and
`UserPromptSubmit` hooks. Those are not vendored, so caveman mode does not auto-activate
and `caveman-stats` has nothing feeding it numbers. See `.claude/skills/NOTICE.md`. For
the full behaviour:

```bash
claude plugin marketplace add JuliusBrussee/caveman
claude plugin install caveman@caveman
```

Other agents (Codex, Cursor, Gemini CLI, Cline, and ~30 more) have their own one-line
install — see the upstream [INSTALL.md](https://github.com/JuliusBrussee/caveman/blob/main/INSTALL.md).

## License

The vendored skills are MIT. The upstream engine, proxy, and cacheengine are BSL-1.1 and
are not vendored here — the CLI dependency only launches them. See upstream
[LICENSING.md](https://github.com/JuliusBrussee/caveman/blob/main/LICENSING.md).
