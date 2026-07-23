"""
Lab 5 - MCP client (provided complete).

A real FastMCP client. It mints a scoped JWT for each registered client, then
calls all three tools against the secure server. Watch how the token's scopes
control access: full-client succeeds on everything; limited-client is denied
multiply/divide. A call with no token is rejected outright.
"""
import asyncio
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
import auth

SERVER = "http://127.0.0.1:8000/mcp/"


async def call_all(label, token):
    print(f"\n=== {label} ===")
    client = Client(SERVER, auth=BearerAuth(token)) if token else Client(SERVER)
    try:
        async with client as c:
            for name in ("add", "multiply", "divide"):
                try:
                    res = await c.call_tool(name, {"a": 6, "b": 3})
                    print(f"  {name}(6, 3) -> {res.data}   [OK]")
                except Exception as e:
                    print(f"  {name}(6, 3) -> DENIED: {str(e)[:70]}")
    except Exception as e:
        print(f"  connection failed: {str(e)[:70]}")


async def main():
    # No token at all -> rejected.
    await call_all("no-auth (expect 401)", token=None)
    # full-client: all three tools succeed.
    await call_all("full-client", auth.mint_token("full-client"))
    # limited-client: only 'add' is in scope.
    await call_all("limited-client", auth.mint_token("limited-client"))


if __name__ == "__main__":
    asyncio.run(main())
