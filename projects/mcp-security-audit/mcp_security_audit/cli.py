"""
MCP Security Audit CLI
======================

Command-line interface for scanning MCP servers.
"""

import argparse
import json
import sys
from pathlib import Path

from .scanner import (
    scan_config_file,
    scan_mcp_server,
    generate_report,
    AuditResult,
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Security Audit Tool - Scan MCP servers for security issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan a configuration file
  mcp-audit config.json
  
  # Output as markdown
  mcp-audit config.json --format markdown
  
  # Output as JSON
  mcp-audit config.json --format json
  
  # Scan inline JSON config
  mcp-audit --json '{"name": "my-server", "permissions": ["filesystem:read:*"]}'
"""
    )
    
    parser.add_argument(
        "config",
        nargs="?",
        help="Path to MCP configuration file (JSON)"
    )
    
    parser.add_argument(
        "--json", "-j",
        help="Inline JSON configuration to scan"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)"
    )
    
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="Exit with error code if HIGH or CRITICAL findings found"
    )
    
    args = parser.parse_args()
    
    # Get configuration
    if args.json:
        try:
            config = json.loads(args.json)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)
        result = scan_mcp_server(config)
    elif args.config:
        try:
            result = scan_config_file(args.config)
        except FileNotFoundError:
            print(f"Error: File not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {args.config}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Generate report
    report = generate_report(result, format=args.format)
    
    # Output
    if args.output:
        Path(args.output).write_text(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)
    
    # Exit code
    if args.fail_on_high and (result.critical_count > 0 or result.high_count > 0):
        sys.exit(1)


if __name__ == "__main__":
    main()
