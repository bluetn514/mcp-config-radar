# MCP Config Radar

**Compare MCP server configs across AI coding tools with secret-safe diffs and CI reports.**

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![Zero runtime dependencies](https://img.shields.io/badge/runtime-zero%20dependencies-2E8B57)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)

When the same MCP server is configured in Claude Code, Cursor, VS Code, or Gemini CLI, differences can make one tool behave differently from another. `mcp-config-radar` compares those entries locally and produces a CI-friendly report without printing sensitive values.

![MCP Config Radar compares client config files and reports field names without exposing values](docs/overview.svg)

## Quick start

Requires Python 3.11 or newer.

```bash
python -m pip install .
mcp-config-radar .
```

Or run directly from a checkout:

```bash
git clone https://github.com/bluetn514/mcp-config-radar.git
cd mcp-config-radar
python -m pip install .
```

You can also run it without installing the command entry point:

```bash
python -m mcp_config_radar .
```

Example output:

```text
mcp-config-radar 0.1.0

Scanned 3 config(s) and 3 server definition(s).
  claude-code      .mcp.json (1 server(s))
  cursor           .cursor/mcp.json (1 server(s))
  vscode           .vscode/mcp.json (1 server(s))

CONFIGURATION DRIFT
  DRIFT    server 'github' differs between .mcp.json and .cursor/mcp.json; fields: env
  DRIFT    server 'github' differs between .mcp.json and .vscode/mcp.json; fields: args, env
  Values for command args, environment variables, and HTTP headers are never printed.

Summary: 2 drift, 0 missing expected server(s), 0 config error(s).
```

Try it on the bundled example:

```bash
mcp-config-radar examples/project
```

## What it checks

- Finds same-named MCP servers in supported config files and compares their transport, command, arguments, working directory, URL, enabled state, environment, and HTTP headers.
- Can check that every server appears in a set of clients you name with `--expect`.
- Reports invalid JSON/TOML, duplicate JSON keys, and malformed server maps.
- Emits readable text, machine-readable JSON, or SARIF for code scanning.
- Returns `1` on drift and `2` on unreadable or invalid config, making it suitable for CI.

## Supported config locations

Project discovery searches the project tree and skips dependency/build folders such as `.git`, `node_modules`, `.venv`, `vendor`, and `dist`.

| Client | Project config | `--user` config |
| --- | --- | --- |
| Claude Code | `.mcp.json` | `~/.claude.json` |
| Cursor | `.cursor/mcp.json` | `~/.cursor/mcp.json` |
| VS Code | `.vscode/mcp.json` | — |
| Gemini CLI | `.gemini/settings.json` | `~/.gemini/settings.json` |
| Codex | — | `~/.codex/config.toml` |
| Claude Desktop | — | OS-specific `claude_desktop_config.json` |
| Windsurf | — | `~/.codeium/windsurf/mcp_config.json` |

User-level files are only inspected when you pass `--user`. Pass any other file explicitly with `--config PATH`.

## Examples

### Include user-level config

```bash
mcp-config-radar . --user
```

### Require the same servers in selected clients

```bash
mcp-config-radar . --expect cursor,vscode,codex
```

The expected-client check is opt-in because not every repository uses every editor.

### JSON report

```bash
mcp-config-radar . --format json > mcp-config-radar.json
```

### SARIF report

```bash
mcp-config-radar . --format sarif > mcp-config-radar.sarif
```

See [the GitHub Actions example](examples/ci/mcp-config-radar.yml) for uploading SARIF and failing the job when drift is present.

### Inspect a non-standard path

```bash
mcp-config-radar . --config ./config/team-mcp.json
```

## Privacy and safety

- The tool is read-only. It does not rewrite config files, execute server commands, or contact remote MCP endpoints.
- Config values stay local and are compared in memory.
- Reports never include command args, environment values, URL credentials, or HTTP header values. For these fields, a report names only the field that differs.
- Use `--user` only when you want personal config locations included in the scan.

## Scope

MCP Config Radar compares same-named server entries across client config files. It does not launch configured processes, probe endpoints, benchmark servers, or decide whether a difference is intentional. If two clients need different settings, the report shows which fields differ so you can review them.

## Related projects

This project focuses on cross-client configuration comparison and value-free drift reports. It does not diagnose server health or audit server behavior. For adjacent workflows, see [`mcp-doctor`](https://github.com/realwigu/mcp-doctor) for broader server diagnosis, security checks, and benchmarks, and [`mcp-config-doctor`](https://github.com/aolingge/mcp-config-doctor) for validating individual config files and setup. [`egao1980/mcp-parity`](https://github.com/egao1980/mcp-parity) tests MCP protocol interoperability across SDKs; it is a different kind of parity check.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Adapter contributions should include official documentation for the config format and sanitized examples.

## License

MIT. See [LICENSE](LICENSE).
