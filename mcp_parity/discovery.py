"""Discover known MCP config files without traversing dependency folders."""

from __future__ import annotations

import os
from pathlib import Path

from .models import ConfigSource

_PRUNED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules",
    "vendor", "dist", "build", ".next", ".tox", "__pycache__",
}

_PROJECT_FILES = {".mcp.json": "claude-code"}
_PROJECT_SUBPATHS = {
    (".cursor", "mcp.json"): "cursor",
    (".vscode", "mcp.json"): "vscode",
    (".gemini", "settings.json"): "gemini",
}


def _source(path: Path, root: Path, client: str) -> ConfigSource:
    return ConfigSource(client=client, path=path, root=root)


def _user_sources(root: Path) -> list[ConfigSource]:
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser()
    candidates: list[tuple[Path, str]] = [
        (codex_home / "config.toml", "codex"),
        (home / ".gemini" / "settings.json", "gemini"),
        (home / ".cursor" / "mcp.json", "cursor"),
        (home / ".codeium" / "windsurf" / "mcp_config.json", "windsurf"),
        (home / ".claude.json", "claude-code-user"),
        (home / ".config" / "Claude" / "claude_desktop_config.json", "claude-desktop"),
        (home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json", "claude-desktop"),
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append((Path(appdata) / "Claude" / "claude_desktop_config.json", "claude-desktop"))

    sources = []
    for path, client in candidates:
        if path.is_file():
            sources.append(_source(path, root, client))
    return sources


def discover_sources(root: Path, include_user: bool = False, explicit: list[Path] | None = None) -> list[ConfigSource]:
    """Find project and optional user config files, plus explicitly named files."""
    root = root.resolve()
    found: dict[Path, ConfigSource] = {}

    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(
            name for name in dirs
            if name not in _PRUNED_DIRS and not (Path(current) / name).is_symlink()
        )
        directory = Path(current)

        for filename, client in _PROJECT_FILES.items():
            if filename in files:
                path = directory / filename
                if not path.is_symlink():
                    found[path.resolve()] = _source(path, root, client)

        for parts, client in _PROJECT_SUBPATHS.items():
            path = directory.joinpath(*parts)
            if path.is_file() and not path.is_symlink():
                found[path.resolve()] = _source(path, root, client)

    if include_user:
        for source in _user_sources(root):
            found[source.path.resolve()] = source

    for path in explicit or []:
        expanded = path.expanduser()
        resolved = (expanded if expanded.is_absolute() else root / expanded).resolve()
        client = infer_client(resolved)
        found[resolved] = _source(resolved, root, client)

    return sorted(found.values(), key=lambda item: (item.client, item.display_path.casefold()))


def infer_client(path: Path) -> str:
    """Infer a client label from a conventional config file path."""
    parts = {part.casefold() for part in path.parts}
    name = path.name.casefold()
    if path.suffix.casefold() == ".toml" and ".codex" in parts:
        return "codex"
    if ".cursor" in parts:
        return "cursor"
    if ".vscode" in parts:
        return "vscode"
    if ".gemini" in parts:
        return "gemini"
    if ".codeium" in parts or name == "mcp_config.json":
        return "windsurf"
    if name == "claude_desktop_config.json" or "claude" in str(path).casefold():
        return "claude-desktop"
    if name == ".mcp.json" or ".claude.json" == name:
        return "claude-code"
    if name == "mcp.json":
        return "mcp"
    return "custom"
