"""Command-line interface for MCP Parity."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .compare import compare_documents
from .discovery import discover_sources
from .loader import load_sources
from .report import json_report, sarif_report, text_report

_CLIENTS = (
    "claude-code", "claude-code-user", "claude-desktop", "codex",
    "cursor", "vscode", "gemini", "windsurf", "custom",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcp-parity",
        description="Find MCP server configuration drift across AI coding tools.",
        epilog="Reports never print command args, environment variable values, or HTTP header values.",
    )
    parser.add_argument("path", nargs="?", default=".", help="project directory to scan (default: current directory)")
    parser.add_argument("--config", action="append", default=[], metavar="FILE", help="also inspect a specific config file; repeatable")
    parser.add_argument("--user", action="store_true", help="also inspect known MCP config files in your user profile")
    parser.add_argument("--expect", metavar="CLIENTS", help="comma-separated clients expected to contain every server (for example: cursor,vscode,codex)")
    parser.add_argument("--format", choices=("text", "json", "sarif"), default="text", help="report format (default: text)")
    parser.add_argument("--fail-on", choices=("drift", "never"), default="drift", help="exit 1 when drift is found (default: drift)")
    parser.add_argument("--version", action="version", version=f"mcp-parity {__version__}")
    return parser


def _expected_clients(value: str | None, parser: argparse.ArgumentParser) -> set[str] | None:
    if value is None:
        return None
    clients = {item.strip().casefold() for item in value.split(",") if item.strip()}
    unknown = sorted(clients - set(_CLIENTS))
    if not clients or unknown:
        parser.error("--expect requires known client names; supported: " + ", ".join(_CLIENTS))
    return clients


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    root = Path(args.path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"scan path is not a directory: {args.path}")

    expected = _expected_clients(args.expect, parser)
    explicit = [Path(value) for value in args.config]
    sources = discover_sources(root, include_user=args.user, explicit=explicit)
    result = load_sources(sources, root)
    findings = compare_documents(result.documents, expected_clients=expected)

    if args.format == "json":
        output = json_report(result, findings)
    elif args.format == "sarif":
        output = sarif_report(result, findings)
    else:
        output = text_report(result, findings)
    print(output)

    if result.errors:
        return 2
    if args.fail_on == "drift" and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
