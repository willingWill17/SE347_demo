from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from urllib.parse import urlencode
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def linear_tools():
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        raise ValueError("LINEAR_API_KEY environment variable is not set. Please check your .env file.")
    
    base_url = "https://server.smithery.ai/linear/mcp"
    params = {
        "profile": "prominent-fox-34SjSm",
        "api_key": api_key,
    }
    url = f"{base_url}?{urlencode(params)}"
    
    try:
        # Return the context manager tuple instead of the session
        return streamablehttp_client(url)
    except Exception as e:
        raise Exception(f"Failed to connect to Linear API: {e}")

if __name__ == "__main__":
    linear_session = asyncio.run(linear_tools())