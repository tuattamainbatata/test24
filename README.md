# test24

This repository previously contained a local setup for
[OmniRoute](https://github.com/diegosouzapw/OmniRoute), a third-party npm package
marketed as an "AI gateway" that aggregates AI providers behind a single
OpenAI-compatible endpoint. That setup has been removed after review of the
upstream project's own documentation surfaced concerns:

- Its "zero-config" default behavior routes traffic through a free-tier
  provider (OpenCode Free) whose terms of service explicitly restrict use to
  "your own internal use... not on behalf of or for the benefit of any third
  party" — i.e. the tool's out-of-the-box behavior conflicts with that
  provider's ToS.
- The codebase includes opt-in features (`src/mitm/`, `open-sse/config/cliFingerprints.ts`,
  `open-sse/services/claudeCode*.ts`) that reimplement other vendors' internal
  client-integrity/billing tokens and spoof TLS/header fingerprints of
  official CLI tools (Claude Code, Codex, Copilot, Antigravity, Cursor) so
  that proxied traffic is indistinguishable from the official client. The
  project's own docs record real account bans resulting from this.
- The project's `SECURITY.md` documents responding to supply-chain scanner
  (Socket.dev/Snyk) malware findings with an attestation that the flagged
  behavior is intentional, rather than disputing the classification.

None of this is a statement about the maintainer's intent, but the combination
of default behavior and available features carries real ToS and
account-suspension risk for anyone pointing real credentials at it. This repo
no longer installs or runs it.
