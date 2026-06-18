"""The normal MCP surface must expose one canonical deterministic entrypoint."""

from aocs_mcp.server import mcp


def test_only_one_public_mcp_tool_is_registered():
    assert set(mcp._tool_manager._tools) == {"aocs_run_full"}
