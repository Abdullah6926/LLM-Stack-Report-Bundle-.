"""MCP SDK v2 server: 2 tools, 1 resource, 1 prompt. Run with `python mcp_server_sdk.py`."""
from mcp.server import MCPServer
mcp = MCPServer("LLM Stack Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers; safe, deterministic demonstration tool."""
    return a + b

@mcp.tool()
def public_status(component: str) -> dict:
    """Return harmless public demo status for an allowlisted component."""
    allowed = {"api", "retrieval", "worker"}
    if component not in allowed:
        raise ValueError("component is not allowlisted")
    return {"component": component, "status": "ok"}

@mcp.resource("stack://overview")
def overview() -> str:
    """A static, non-sensitive overview resource."""
    return "The stack has models, tools, retrieval, policy, and tracing."

@mcp.prompt()
def explain_stack(topic: str) -> str:
    """Create a short teaching prompt for a named LLM stack topic."""
    return f"Explain {topic!r} using intuition, mechanism, and one limitation."

if __name__ == "__main__":
    mcp.run()
