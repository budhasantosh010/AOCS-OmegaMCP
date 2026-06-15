"""AOCS-Omega package."""


def main() -> None:
    """Console-script entrypoint for the MCP server."""
    from aocs_mcp.server import main as server_main

    server_main()


__all__ = ["main"]
