"""Secret-safe text, JSON, and SARIF reports."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from . import __version__
from .models import Finding, ScanResult


def _finding_data(finding: Finding) -> dict[str, Any]:
    return {
        "code": finding.code,
        "severity": finding.severity,
        "message": finding.message,
        "paths": list(finding.paths),
        "server": finding.server,
        "fields": list(finding.fields),
    }


def json_report(result: ScanResult, findings: list[Finding]) -> str:
    payload = {
        "schemaVersion": 1,
        "version": __version__,
        "configs": [
            {
                "client": document.source.client,
                "path": document.source.display_path,
                "serverCount": len(document.servers),
            }
            for document in result.documents
        ],
        "summary": {
            "configs": len(result.documents),
            "servers": sum(len(document.servers) for document in result.documents),
            "findings": len(findings),
            "errors": len(result.errors),
        },
        "findings": [_finding_data(item) for item in findings],
        "errors": [_finding_data(item) for item in result.errors],
        "privacy": "Configuration values are never included in reports.",
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def text_report(result: ScanResult, findings: list[Finding]) -> str:
    lines = [f"mcp-config-radar {__version__}", ""]
    config_count = len(result.documents)
    server_count = sum(len(document.servers) for document in result.documents)
    lines.append(f"Scanned {config_count} config(s) and {server_count} server definition(s).")

    for document in result.documents:
        lines.append(f"  {document.source.client:<16} {document.source.display_path} ({len(document.servers)} server(s))")

    if not result.documents:
        lines.append("No supported MCP config files found. Use --config PATH to inspect a specific file.")

    if result.errors:
        lines.extend(["", "CONFIG ERRORS"])
        for finding in result.errors:
            lines.append(f"  ERROR  {finding.message}")

    if findings:
        lines.extend(["", "CONFIGURATION DRIFT"])
        for finding in findings:
            if finding.code == "MCP301":
                lines.append(f"  MISSING  {finding.message}")
            else:
                field_names = ", ".join(finding.fields)
                lines.append(f"  DRIFT    {finding.message}; fields: {field_names}")
        lines.append("  Values for command args, environment variables, and HTTP headers are never printed.")
    else:
        lines.extend(["", "No cross-client drift found."])

    counts = Counter(item.code for item in findings)
    summary = f"Summary: {counts['MCP201']} drift, {counts['MCP301']} missing expected server(s), {len(result.errors)} config error(s)."
    lines.extend(["", summary])
    return "\n".join(lines)


def sarif_report(result: ScanResult, findings: list[Finding]) -> str:
    all_findings = [*findings, *result.errors]
    rules: dict[str, dict[str, str]] = {}
    results = []
    for finding in all_findings:
        rules.setdefault(finding.code, {
            "id": finding.code,
            "name": {
                "MCP001": "InvalidMcpConfig",
                "MCP201": "McpConfigDrift",
                "MCP301": "MissingExpectedServer",
            }.get(finding.code, finding.code),
            "shortDescription": {"text": finding.code},
        })
        location = finding.paths[0] if finding.paths else "."
        result_item: dict[str, Any] = {
            "ruleId": finding.code,
            "level": "error" if finding.severity == "error" else "warning",
            "message": {"text": finding.message},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": location.replace("\\", "/")},
                "region": {"startLine": 1},
            }}],
        }
        if finding.server:
            result_item["properties"] = {"server": finding.server, "fields": list(finding.fields)}
        results.append(result_item)

    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "mcp-config-radar",
                    "semanticVersion": __version__,
                    "rules": list(rules.values()),
                },
            },
            "results": results,
            "properties": {"privacy": "Configuration values are never included in reports."},
        }],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
