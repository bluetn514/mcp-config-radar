# MCP Parity

**Catch MCP server config drift across AI coding tools before it breaks a workflow.**

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![Zero runtime dependencies](https://img.shields.io/badge/runtime-zero%20dependencies-2E8B57)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)

When the same MCP server is configured in Claude Code, Cursor, VS Code, or Gemini CLI, a small difference can make one agent fail while another works. `mcp-parity` finds those differences locally and produces a CI-friendly report.

![MCP Parity compares client config files and reports field names without exposing values](docs/overview.svg)

## Quick start

Requires Python 3.11 or newer.

```bash
python -m pip install .
mcp-parity .
```

Or run directly from a checkout:

```bash
git clone https://github.com/bluetn514/mcp-config-parity.git
cd mcp-config-parity
python -m pip install .
```

You can also run it without installing the command entry point:

```bash
python -m mcp_parity .
```

Example output:

```text
mcp-parity 0.1.0

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
mcp-parity examples/project
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
mcp-parity . --user
```

### Require the same servers in selected clients

```bash
mcp-parity . --expect cursor,vscode,codex
```

The expected-client check is opt-in because not every repository uses every editor.

### JSON report

```bash
mcp-parity . --format json > mcp-parity.json
```

### SARIF report

```bash
mcp-parity . --format sarif > mcp-parity.sarif
```

See [the GitHub Actions example](examples/ci/mcp-parity.yml) for uploading SARIF and failing the job when drift is present.

### Inspect a non-standard path

```bash
mcp-parity . --config ./config/team-mcp.json
```

## Privacy and safety

- The tool is read-only. It does not rewrite config files, execute server commands, or contact remote MCP endpoints.
- Config values stay local and are compared in memory.
- Reports never include command args, environment values, URL credentials, or HTTP header values. For these fields, a report names only the field that differs.
- Use `--user` only when you want personal config locations included in the scan.

## Scope

MCP Parity checks whether config entries match; it does not test whether a server launches, whether a URL is reachable, or whether an API credential is valid. It compares server entries with the same name across different client types. If two clients intentionally need different configs, the report makes that difference visible so you can decide whether it is expected.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Adapter contributions should include official documentation for the config format and sanitized examples.

## License

MIT. See [LICENSE](LICENSE).
