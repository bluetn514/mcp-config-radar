# Contributing

Issues and pull requests are welcome. Before proposing a new client adapter, include a sanitized example of that client's MCP config format and a link to its official documentation.

## Development

- Python 3.11 or newer is required.
- The runtime uses only the Python standard library.
- Keep reports value-free: never print server arguments, environment values, URL credentials, or HTTP header values.
- Keep discovery read-only and avoid launching configured commands or making network requests.

Install the local package in editable mode with `python -m pip install -e .`, then run `mcp-parity --help`.

## Pull requests

Please describe the client/config shape being added, the user-visible behavior, and any compatibility limits. Avoid including real credentials or personal config files in examples.
