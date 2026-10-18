"""Official MCP Python SDK v2 client. Requires the server on localhost:8000."""
import anyio
from mcp.client import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool("add", {"a": 19, "b": 23})
        print(result.structured_content)

if __name__ == "__main__": anyio.run(main)
