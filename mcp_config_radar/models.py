"""Small data models shared by discovery, parsing, and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ConfigSource:
    client: str
    path: Path
    root: Path

    @property
    def display_path(self) -> str:
        try:
            return self.path.resolve().relative_to(self.root.resolve()).as_posix()
        except (OSError, ValueError):
            try:
                return "~/" + self.path.resolve().relative_to(Path.home().resolve()).as_posix()
            except (OSError, ValueError):
                return self.path.as_posix()


@dataclass
class ConfigDocument:
    source: ConfigSource
    servers: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    paths: tuple[str, ...] = ()
    server: str | None = None
    fields: tuple[str, ...] = ()


@dataclass
class ScanResult:
    root: Path
    documents: list[ConfigDocument] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    errors: list[Finding] = field(default_factory=list)
