"""Normalize server entries and report field-level configuration drift."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import ConfigDocument, Finding


def _transport(server: dict[str, Any]) -> str:
    value = server.get("type", server.get("transport", server.get("transportType")))
    if isinstance(value, str) and value.strip():
        normalized = value.casefold().replace("streamable-http", "http")
        return "http" if normalized == "streamable http" else normalized
    if isinstance(server.get("command"), str):
        return "stdio"
    if isinstance(server.get("url"), str):
        return "http"
    return "unknown"


def _enabled(server: dict[str, Any]) -> bool:
    if server.get("disabled") is True:
        return False
    if server.get("enabled") is False:
        return False
    return True


def _canonical(server: dict[str, Any]) -> dict[str, Any]:
    """Return comparison values in memory; reporters must never render values."""
    args = server.get("args", [])
    if not isinstance(args, list):
        args = [args]
    env = server.get("env", {})
    if not isinstance(env, dict):
        env = {"<invalid-env-shape>": type(env).__name__}
    headers = server.get("headers", {})
    if not isinstance(headers, dict):
        headers = {"<invalid-headers-shape>": type(headers).__name__}
    return {
        "transport": _transport(server),
        "command": server.get("command"),
        "args": args,
        "cwd": server.get("cwd"),
        "url": server.get("url"),
        "enabled": _enabled(server),
        "env": env,
        "headers": headers,
    }


def compare_documents(documents: list[ConfigDocument], expected_clients: set[str] | None = None) -> list[Finding]:
    """Find named server differences across discovered config documents."""
    by_name: dict[str, list[tuple[ConfigDocument, dict[str, Any]]]] = defaultdict(list)
    for document in documents:
        for name, definition in document.servers.items():
            by_name[name].append((document, definition))

    findings: list[Finding] = []
    for name in sorted(by_name, key=str.casefold):
        entries = by_name[name]
        by_client: dict[str, list[ConfigDocument]] = defaultdict(list)
        for document, _definition in entries:
            by_client[document.source.client].append(document)

        if expected_clients:
            present_clients = set(by_client)
            absent = sorted(expected_clients - present_clients)
            if absent:
                paths = tuple(sorted({document.source.display_path for document, _ in entries}))
                findings.append(Finding(
                    code="MCP301",
                    severity="warning",
                    message=f"server {name!r} is missing from expected client(s): {', '.join(absent)}",
                    paths=paths,
                    server=name,
                    fields=tuple(absent),
                ))

        if len(entries) < 2:
            continue
        for index, (baseline_doc, baseline_server) in enumerate(entries):
            baseline = _canonical(baseline_server)
            for other_doc, other_server in entries[index + 1:]:
                # Two separate projects may intentionally configure the same
                # client differently. Parity only compares unlike clients.
                if baseline_doc.source.client == other_doc.source.client:
                    continue
                current = _canonical(other_server)
                differing = tuple(key for key in baseline if baseline[key] != current[key])
                if differing:
                    paths = (baseline_doc.source.display_path, other_doc.source.display_path)
                    findings.append(Finding(
                        code="MCP201",
                        severity="warning",
                        message=f"server {name!r} differs between {paths[0]} and {paths[1]}",
                        paths=paths,
                        server=name,
                        fields=differing,
                    ))
    return findings
