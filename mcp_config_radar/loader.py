"""Load MCP server maps from JSON and Codex TOML config files."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

from .models import ConfigDocument, ConfigSource, Finding, ScanResult


class DuplicateKeyError(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _server_map(data: Any, client: str) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict):
        raise ValueError("the config root must be an object")

    candidate_keys = ["mcp_servers"] if client == "codex" else []
    if client == "vscode":
        candidate_keys.extend(["servers", "mcpServers", "mcp_servers"])
    else:
        candidate_keys.extend(["mcpServers", "mcp_servers", "servers"])

    raw_servers = next((data[key] for key in candidate_keys if key in data), None)
    if raw_servers is None:
        expected = " or ".join(f"{key!r}" for key in candidate_keys)
        raise ValueError(f"no MCP server map found (expected {expected})")
    if not isinstance(raw_servers, dict):
        raise ValueError("the MCP server map must be an object/table")

    servers: dict[str, dict[str, Any]] = {}
    for name, definition in raw_servers.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("server names must be non-empty strings")
        if not isinstance(definition, dict):
            raise ValueError(f"server {name!r} must be an object/table")
        servers[name] = definition
    return servers


def load_sources(sources: list[ConfigSource], root: Path) -> ScanResult:
    result = ScanResult(root=root)
    for source in sources:
        try:
            raw = source.path.read_bytes()
            if source.path.suffix.casefold() == ".toml":
                data = tomllib.loads(raw.decode("utf-8-sig"))
            else:
                data = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_unique_object)
            servers = _server_map(data, source.client)
            result.documents.append(ConfigDocument(source=source, servers=servers))
        except (OSError, UnicodeError, json.JSONDecodeError, tomllib.TOMLDecodeError, DuplicateKeyError, ValueError) as exc:
            result.errors.append(Finding(
                code="MCP001",
                severity="error",
                message=f"{source.display_path}: {type(exc).__name__}: {exc}",
                paths=(source.display_path,),
            ))
    return result
