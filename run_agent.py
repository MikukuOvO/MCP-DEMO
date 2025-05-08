import asyncio
import os
from contextlib import AsyncExitStack

from dotenv import load_dotenv

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

# ──────────────────────────────────────────────────────────────────────
# 1 | Environment ─ load your Azure-/OpenAI settings from .env
# ──────────────────────────────────────────────────────────────────────
load_dotenv()                             # pulls AZURE_OPENAI_* (or OPENAI_API_KEY)

DEPLOYMENT_NAME = os.getenv(
    "AZURE_OPENAI_DEPLOYMENT_NAME",       # Azure: gpt-4o, gpt-35-turbo, …
    "gpt-4o"                              # fallback for public OpenAI
)

# ──────────────────────────────────────────────────────────────────────
# 2 | Main runner
# ──────────────────────────────────────────────────────────────────────
async def main() -> None:
    async with AsyncExitStack() as stack:
        # Gmail MCP server
        gmail_srv = await stack.enter_async_context(
            MCPServerStdio(
                params={"command": "python", "args": ["mcp_servers/gmail_mcp_server.py"]}
            )
        )
        # Google Calendar MCP server
        cal_srv = await stack.enter_async_context(
            MCPServerStdio(
                params={"command": "python", "args": ["mcp_servers/calendar_mcp_server.py"]}
            )
        )

        # Create the agent with both servers attached
        agent = Agent(
            name="Inbox & Calendar Assistant",
            instructions=(
                "Use Gmail tools (`gmail_search_messages`, `gmail_get_message`) "
                "for email questions and Calendar tools "
                "(`calendar_search_events`, `calendar_get_event`) for agenda questions."
            ),
            model=DEPLOYMENT_NAME,         # Azure treats this as *deployment-id*
            mcp_servers=[gmail_srv, cal_srv],
        )

        # Example query – replace with whatever you need
        result = await Runner.run(
            agent,
            # Input by user in terminal
            input=input("Ask about your email or calendar: ")
        )
        print(result.final_output)

# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(main())
