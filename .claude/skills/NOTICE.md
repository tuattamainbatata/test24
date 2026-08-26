# Vendored skills

## caveman

Source: [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) — `plugins/caveman/`
at commit `81536f57b3303b7de7f5bc5b564cc344f9112d68` (installer version 2.3.1).

License: MIT (`skills/` and the adoption surfaces are MIT; the Go engine, proxy, and
cacheengine directories of the upstream repo are BSL-1.1 and are **not** vendored here).
See upstream `LICENSE` and `LICENSING.md`.

Vendored:

| Path | What |
|---|---|
| `caveman/` | Ultra-compressed reply mode. `/caveman lite\|full\|ultra\|off`. |
| `cavecrew/` | When to delegate to the compressed subagents below. |
| `caveman-compress/` | Compress a natural-language memory file in place (`scripts/`, Python 3). |
| `caveman-stats/` | Session token stats. |
| `../agents/cavecrew-{investigator,builder,reviewer}.md` | Subagents the `cavecrew` skill dispatches to. |

### Limitations of a skills-only install

Upstream ships these as a Claude Code *plugin*, whose `plugin.json` also registers
`SessionStart` and `UserPromptSubmit` hooks. Those hook scripts are not vendored, so:

- **`caveman-stats` does not produce numbers here.** Its output is injected by the
  `caveman-mode-tracker` hook, not computed by the model. The skill file is kept for
  parity but needs the full plugin install to work.
- Caveman mode does not auto-activate at session start — invoke `/caveman` (or say
  "caveman mode") once per session.

For hooks, the statusline badge, and the compression proxy, install the plugin instead:

```
claude plugin marketplace add JuliusBrussee/caveman
claude plugin install caveman@caveman
```
