"""
inbox_calendar_notion_azure.py
Convert the "Inbox & Calendar Assistant" runner to use Azure OpenAI.
Now includes Notion integration.
"""

import asyncio
import json
import os
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from api.cloudgpt_aoai import get_openai_token_provider
from openai import AsyncAzureOpenAI

from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio

# ──────────────────────────────────────────────────────────────────────
# 1 | Environment – load your Azure settings from .env
#       Expected .env vars:
#         AZURE_OPENAI_ENDPOINT   = https://<your-resource>.openai.azure.com
#         AZURE_OPENAI_DEPLOYMENT = o1-20241217        (deployment ID)
#         AZURE_OPENAI_API_VERSION= 2024-09-01-preview (or later)
#   (If you prefer key auth, also set AZURE_OPENAI_API_KEY and
#    skip the token-provider lines below.)
# ──────────────────────────────────────────────────────────────────────
load_dotenv()

AZURE_ENDPOINT     = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_VERSION  = os.getenv("AZURE_OPENAI_API_VERSION", "2024-09-01-preview")
# DEPLOYMENT_NAME    = "gpt-4o-20241120"
DEPLOYMENT_NAME    = "o3-20250416"

# AAD-based auth  (comment this block out if you're using an API key)
token_provider = get_openai_token_provider()

print(token_provider)

azure_client = AsyncAzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_version=AZURE_API_VERSION,
    azure_ad_token_provider=token_provider,   # omit if using key auth
    # api_key=os.getenv("AZURE_OPENAI_API_KEY"),   # ← use this line for key auth
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
        # Notion MCP server
        notion_srv = await stack.enter_async_context(
            MCPServerStdio(
                params={"command": "python", "args": ["mcp_servers/notion_mcp_server.py"]}
            )
        )

        # ——— Agent that talks to Azure OpenAI ———
        agent = Agent(
            name="Inbox, Calendar & Notion Assistant",
            instructions=(
                "You are a helpful assistant that can interact with Gmail, Google Calendar, and Notion.\n\n"
                
                "For email-related queries, use Gmail tools:\n"
                "- `gmail_search_messages`: Search emails with Gmail's query syntax\n"
                "- `gmail_get_message`: Get full email content\n"
                "- `gmail_send_message`: Send new emails\n\n"
                
                "For calendar-related queries, use Calendar tools:\n"
                "- `calendar_search_events`: Find calendar events\n"
                "- `calendar_get_event`: Get event details\n"
                "- `calendar_create_event`: Create new calendar events\n\n"
                
                "For Notion-related queries, use Notion tools:\n"
                "- `NotionManagerSearchContent`: Search for pages and databases in Notion\n"
                "- `NotionManagerReadPage`: Read the full content of a Notion page\n\n"
                
                "When answering questions, use the appropriate tool based on the user's request. "
                "You can combine information from multiple sources when needed."
            ),
            model=OpenAIChatCompletionsModel(
                model=DEPLOYMENT_NAME,      # deployment ID, e.g. o1-20241217
                openai_client=azure_client, # Azure client created above
            ),
            mcp_servers=[gmail_srv, cal_srv, notion_srv],
        )

        # Example query – replace with whatever you need
        result = await Runner.run(
            agent,
            input=input("Ask about your email, calendar, or Notion: ")
        )
        print(result.final_output)
        
        # Save responses to a file in a more readable format
        with open("data/result.json", "w") as f:
            # Format new_items for better readability
            formatted_items = []
            
            for item in result.new_items:
                item_type = item.type
                
                if item_type == 'tool_call_item':
                    formatted_item = {
                        "type": item_type,
                        "tool_name": item.raw_item.name,
                        "arguments": item.raw_item.arguments
                    }
                elif item_type == 'tool_call_output_item':
                    formatted_item = {
                        "type": item_type,
                        "output": item.output
                    }
                elif item_type == 'message_output_item':
                    formatted_item = {
                        "type": item_type,
                        "content": item.raw_item.content[0].text if item.raw_item.content else ""
                    }
                else:
                    formatted_item = {"type": item_type}
                
                formatted_items.append(formatted_item)
            
            # Create the final JSON structure
            json_data = {
                "formatted_items": formatted_items,
                "final_output": result.final_output
            }
            
            json.dump(json_data, f, indent=2)

# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(main())