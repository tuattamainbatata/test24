# Third-party skills

Skills in this directory are vendored from external, separately maintained repositories:

- `banner-design/`, `brand/`, `design/`, `design-system/`, `slides/`, `ui-styling/`, `ui-ux-pro-max/`
  from [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (MIT License)
- `babysit/`, `cloud-sync/`, `design-is/`, `do/`, `how-it-works/`, `knowledge-agent/`, `learn-codebase/`,
  `make-plan/`, `mem-search/`, `mode-creator/`, `oh-my-issues/`, `pathfinder/`, `smart-explore/`, `standup/`,
  `timeline-report/`, `version-bump/`, `weekly-digests/`, `what-the/`, `wowerpoint/`
  from [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) (Apache License 2.0)
- `karpathy-guidelines/` from [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) (MIT License)

The `claude-mem`-sourced skills assume the claude-mem plugin runtime (a local worker service on
`localhost`, MCP server, and hooks) is installed and running — several of them (`cloud-sync`,
`timeline-report`, `weekly-digests`, `mem-search`, `knowledge-agent`) shell out to
`http://localhost:$WORKER_PORT/...`. They will not function until claude-mem itself is installed
separately (see the upstream repo). All other skills are self-contained.
