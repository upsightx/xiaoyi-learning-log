# MCP Security Audit Tool 🔒

A security scanner for MCP (Model Context Protocol) servers.

## Why This Matters

MCP is the "USB-C for AI" - a unified protocol for connecting AI agents to tools and data. But with standardization comes risk:

- **CVE-2025-6514** (CVSS 10.0) - Remote code execution in mcp-remote
- **78%** of MCP implementations lack proper authorization
- **Tool Poisoning** - Hidden instructions in tool descriptions can hijack AI behavior

This tool helps you find and fix these issues before attackers do.

## Features

✅ **Vulnerability Detection**
- CVE-2025-6514 (mcp-remote RCE)
- Known vulnerable dependencies

✅ **Tool Poisoning Detection**
- Hidden instruction blocks
- System prompt override attempts
- Suspicious keywords (API keys, secrets)

✅ **Authorization Checks**
- Missing authorization config
- Disabled authorization
- Over-privileged permissions

✅ **Multiple Output Formats**
- Text (default)
- Markdown
- JSON

## Installation

```bash
pip install mcp-security-audit
```

Or clone and install locally:

```bash
git clone https://github.com/upsightx/mcp-security-audit.git
cd mcp-security-audit
pip install -e .
```

## Usage

### Scan a configuration file

```bash
mcp-audit mcp-config.json
```

### Output as Markdown

```bash
mcp-audit mcp-config.json --format markdown > security-report.md
```

### Output as JSON

```bash
mcp-audit mcp-config.json --format json
```

### Scan inline JSON

```bash
mcp-audit --json '{"name": "my-server", "permissions": ["filesystem:read:*"]}'
```

### Fail on high/critical findings (CI/CD)

```bash
mcp-audit mcp-config.json --fail-on-high
```

## Example Output

```
MCP Security Audit Report
==================================================
Server: my-mcp-server
Status: VULNERABLE

Summary: 1 critical, 1 high, 1 medium, 0 low

[CRITICAL] CVE-2025-6514: mcp-remote Remote Code Execution
  mcp-remote npm package before v0.2.1 allows remote code execution...
  → Upgrade mcp-remote to v0.2.1 or later.

[HIGH] Missing Authorization Configuration
  No authorization configuration found...
  → Implement authorization controls. Use OAuth 2.0, API keys, or mTLS.

[MEDIUM] Over-privileged Permission: filesystem:read:*
  Permission 'filesystem:read:*' grants broad access...
  → Use specific, limited permissions instead of wildcards.
```

## Configuration Format

The tool expects MCP configuration in JSON format:

```json
{
  "name": "my-mcp-server",
  "authorization": {
    "enabled": true
  },
  "permissions": [
    "filesystem:read:/data",
    "network:connect:api.example.com"
  ],
  "tools": [
    {
      "name": "read_file",
      "description": "Read a file from the filesystem"
    }
  ],
  "dependencies": {
    "mcp-remote": "0.2.1"
  }
}
```

## Security Checks

| Check | Severity | Description |
|-------|----------|-------------|
| CVE-2025-6514 | CRITICAL | mcp-remote RCE vulnerability |
| Tool Poisoning | HIGH | Hidden instructions in tool descriptions |
| Missing Auth | HIGH | No authorization configuration |
| Over-privileged | MEDIUM | Wildcard permissions |

## Contributing

Issues and PRs welcome at [GitHub](https://github.com/upsightx/mcp-security-audit).

## License

MIT

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [CVE-2025-6514](https://nvd.nist.gov/vuln/detail/CVE-2025-6514)
- [Microsoft MCP Security Guide](https://learn.microsoft.com/en-us/azure/ai-services/)
