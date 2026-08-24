# OmniRoute — working notes

Thin wrapper repo: `package.json` + `README.md` only. All code lives in the
`omniroute` npm package. There is no source to explore here.

## Token discipline

These cost a lot of context for near-zero value. Don't repeat them:

- **Never `Read` `node_modules/omniroute/package.json`** — ~430 lines, mostly
  test/CI scripts. To get a field: `node -p "require('./node_modules/omniroute/package.json').version"`.
- **Don't `ls` or glob inside `node_modules/omniroute/`** — it vendors its own
  `node_modules` and matches thousands of paths.
- **Don't poll background install logs.** Redirect to a file, check exit code,
  and only `tail` on failure.

## State check (one command, cheap)

```bash
npm run verify
```

Prints `BIN`, `VER`, `symlink`. Use this instead of re-deriving install state.

## Install

`npm install` takes **longer than the 120s Bash timeout** and will be pushed to
the background. Run it detached and check the exit code rather than watching it:

```bash
npm install > /tmp/omni-install.log 2>&1; echo "exit=$?"
```

Known flake: `npm error code ECONNRESET` partway through. It leaves a **partial**
install — `npm ls omniroute` still reports `3.8.49` because that reflects the
recorded dependency tree, not what's on disk. `npm run verify` is the honest
check. Fix is simply to re-run `npm install`; the retry resumed and completed.

Peer-dep `ERESOLVE` and `deprecated` warnings during install are expected and
harmless.

## Run

```bash
npm start          # -> node_modules/.bin/omniroute
```

Dashboard: `http://localhost:20128`, API: `http://localhost:20128/v1`.

Node engine required: `>=22.22.2 <23 || >=24.0.0 <27`. This environment is on
22.22.2 — the exact floor, so it satisfies the range with no headroom.

## Unverified claims

- `README.md` says "290+ providers"; the package's own description says "160+".
  Neither number has been checked against the code. Don't repeat either as fact.
- The package pulls in Playwright, ONNX runtime, TensorFlow, `keytar`
  (OS credential store), an ngrok binding, and a `src/mitm/` native TLS-proxy
  component. Plausible for a gateway that terminates provider TLS, but it is a
  broad surface for a process designed to hold API keys. Not audited.

## Not done

The server has never been started in this repo, and no provider credentials
have been configured. Starting it opens a listening service and is a
credential-handling step — confirm with the user before doing either.
