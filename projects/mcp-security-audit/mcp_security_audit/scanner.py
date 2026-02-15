"""
MCP Security Scanner
====================

Core scanning logic for detecting MCP security issues.
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from pathlib import Path


class Severity(Enum):
    """Security finding severity levels."""
    CRITICAL = "CRITICAL"  # CVSS 9.0-10.0
    HIGH = "HIGH"          # CVSS 7.0-8.9
    MEDIUM = "MEDIUM"      # CVSS 4.0-6.9
    LOW = "LOW"            # CVSS 0.1-3.9
    INFO = "INFO"          # Informational


@dataclass
class Finding:
    """A security finding from the audit."""
    id: str
    title: str
    severity: Severity
    description: str
    recommendation: str
    cve: str | None = None
    cvss: float | None = None
    references: list[str] = field(default_factory=list)


@dataclass
class AuditResult:
    """Result of an MCP security audit."""
    server_name: str
    findings: list[Finding] = field(default_factory=list)
    
    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)
    
    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)
    
    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)
    
    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.LOW)
    
    @property
    def is_secure(self) -> bool:
        return self.critical_count == 0 and self.high_count == 0


# Known vulnerability database
KNOWN_VULNERABILITIES = {
    "CVE-2025-6514": Finding(
        id="CVE-2025-6514",
        title="mcp-remote Remote Code Execution",
        severity=Severity.CRITICAL,
        description="mcp-remote npm package before v0.2.1 allows remote code execution through malicious MCP servers. Attackers can execute arbitrary code by disguising malicious tools as legitimate ones.",
        recommendation="Upgrade mcp-remote to v0.2.1 or later. Validate all MCP server sources before connecting.",
        cve="CVE-2025-6514",
        cvss=10.0,
        references=[
            "https://nvd.nist.gov/vuln/detail/CVE-2025-6514",
        ]
    ),
}


# Security check patterns
TOOL_POISONING_PATTERNS = [
    # Hidden instructions in tool descriptions
    (r'<HIDDEN>.*?</HIDDEN>', "Hidden instruction block detected"),
    (r'<!--.*?-->', "HTML comment in tool description"),
    (r'(?i)system:\s*(you are|ignore|override)', "System prompt override attempt"),
    (r'(?i)execute|eval|exec\(', "Code execution keywords in description"),
    (r'(?i)api[_-]?key|secret|password|token', "Sensitive credential keywords"),
]

SUSPICIOUS_PERMISSIONS = [
    "filesystem:read:*",
    "filesystem:write:*",
    "network:*",
    "process:exec",
    "env:read",
]


def check_tool_poisoning(tool_description: str) -> list[Finding]:
    """Check for tool poisoning patterns in a tool description."""
    findings = []
    
    for pattern, message in TOOL_POISONING_PATTERNS:
        if re.search(pattern, tool_description, re.DOTALL | re.IGNORECASE):
            findings.append(Finding(
                id=f"MCP-TOOL-POISON-{len(findings)+1}",
                title=f"Tool Poisoning: {message}",
                severity=Severity.HIGH,
                description=f"Pattern '{pattern}' found in tool description. This could indicate a tool poisoning attack.",
                recommendation="Review tool description for hidden instructions. Validate tool source.",
            ))
    
    return findings


def check_permissions(permissions: list[str]) -> list[Finding]:
    """Check for over-privileged configurations."""
    findings = []
    
    for perm in permissions:
        if perm in SUSPICIOUS_PERMISSIONS:
            findings.append(Finding(
                id=f"MCP-PERM-{len(findings)+1}",
                title=f"Over-privileged Permission: {perm}",
                severity=Severity.MEDIUM,
                description=f"Permission '{perm}' grants broad access. This violates least privilege principle.",
                recommendation="Use specific, limited permissions instead of wildcards. Define exact resources needed.",
            ))
    
    return findings


def check_authorization(config: dict[str, Any]) -> list[Finding]:
    """Check for authorization configuration issues."""
    findings = []
    
    # Check if authorization is configured
    if "authorization" not in config:
        findings.append(Finding(
            id="MCP-AUTH-001",
            title="Missing Authorization Configuration",
            severity=Severity.HIGH,
            description="No authorization configuration found. 78% of MCP implementations lack proper authorization management.",
            recommendation="Implement authorization controls. Use OAuth 2.0, API keys, or mTLS for authentication.",
        ))
    elif not config.get("authorization", {}).get("enabled", False):
        findings.append(Finding(
            id="MCP-AUTH-002",
            title="Authorization Disabled",
            severity=Severity.HIGH,
            description="Authorization is explicitly disabled.",
            recommendation="Enable authorization for all production MCP servers.",
        ))
    
    return findings


def check_dependencies(dependencies: dict[str, str]) -> list[Finding]:
    """Check for known vulnerable dependencies."""
    findings = []
    
    for dep, version in dependencies.items():
        # Check mcp-remote for CVE-2025-6514
        if dep == "mcp-remote" or dep == "@anthropic-ai/mcp-remote":
            # Parse version (simplified)
            if version.startswith("0.1.") or version == "0.2.0":
                findings.append(KNOWN_VULNERABILITIES["CVE-2025-6514"])
    
    return findings


def scan_mcp_server(config: dict[str, Any]) -> AuditResult:
    """
    Scan an MCP server configuration for security issues.
    
    Args:
        config: MCP server configuration dictionary
        
    Returns:
        AuditResult containing all findings
    """
    server_name = config.get("name", "unknown")
    result = AuditResult(server_name=server_name)
    
    # Check authorization
    result.findings.extend(check_authorization(config))
    
    # Check permissions
    permissions = config.get("permissions", [])
    result.findings.extend(check_permissions(permissions))
    
    # Check tools for poisoning
    tools = config.get("tools", [])
    for tool in tools:
        description = tool.get("description", "")
        result.findings.extend(check_tool_poisoning(description))
    
    # Check dependencies
    dependencies = config.get("dependencies", {})
    result.findings.extend(check_dependencies(dependencies))
    
    return result


def scan_config_file(config_path: str | Path) -> AuditResult:
    """
    Scan an MCP configuration file.
    
    Args:
        config_path: Path to the configuration file (JSON)
        
    Returns:
        AuditResult containing all findings
    """
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, "r") as f:
        config = json.load(f)
    
    return scan_mcp_server(config)


def generate_report(result: AuditResult, format: str = "text") -> str:
    """
    Generate a security audit report.
    
    Args:
        result: AuditResult from scan
        format: Output format ("text", "json", "markdown")
        
    Returns:
        Formatted report string
    """
    if format == "json":
        return json.dumps({
            "server": result.server_name,
            "is_secure": result.is_secure,
            "summary": {
                "critical": result.critical_count,
                "high": result.high_count,
                "medium": result.medium_count,
                "low": result.low_count,
                "total": len(result.findings),
            },
            "findings": [
                {
                    "id": f.id,
                    "title": f.title,
                    "severity": f.severity.value,
                    "description": f.description,
                    "recommendation": f.recommendation,
                    "cve": f.cve,
                    "cvss": f.cvss,
                }
                for f in result.findings
            ]
        }, indent=2)
    
    elif format == "markdown":
        lines = [
            f"# MCP Security Audit Report",
            f"",
            f"**Server**: {result.server_name}",
            f"**Status**: {'✅ SECURE' if result.is_secure else '❌ VULNERABLE'}",
            f"",
            f"## Summary",
            f"",
            f"| Severity | Count |",
            f"|----------|-------|",
            f"| 🔴 CRITICAL | {result.critical_count} |",
            f"| 🟠 HIGH | {result.high_count} |",
            f"| 🟡 MEDIUM | {result.medium_count} |",
            f"| 🟢 LOW | {result.low_count} |",
            f"",
        ]
        
        if result.findings:
            lines.append("## Findings")
            lines.append("")
            
            for f in result.findings:
                severity_emoji = {
                    Severity.CRITICAL: "🔴",
                    Severity.HIGH: "🟠",
                    Severity.MEDIUM: "🟡",
                    Severity.LOW: "🟢",
                    Severity.INFO: "ℹ️",
                }.get(f.severity, "❓")
                
                lines.append(f"### {severity_emoji} [{f.severity.value}] {f.title}")
                lines.append("")
                if f.cve:
                    lines.append(f"**CVE**: {f.cve} (CVSS {f.cvss})")
                    lines.append("")
                lines.append(f"**Description**: {f.description}")
                lines.append("")
                lines.append(f"**Recommendation**: {f.recommendation}")
                lines.append("")
        
        return "\n".join(lines)
    
    else:  # text format
        lines = [
            f"MCP Security Audit Report",
            f"=" * 50,
            f"Server: {result.server_name}",
            f"Status: {'SECURE' if result.is_secure else 'VULNERABLE'}",
            f"",
            f"Summary: {result.critical_count} critical, {result.high_count} high, {result.medium_count} medium, {result.low_count} low",
            f"",
        ]
        
        for f in result.findings:
            lines.append(f"[{f.severity.value}] {f.title}")
            lines.append(f"  {f.description}")
            lines.append(f"  → {f.recommendation}")
            lines.append("")
        
        return "\n".join(lines)
