import asyncio
import json
import aiofiles

from pathlib import Path
from mcp import ClientSession
from mcp.server.fastmcp import FastMCP

# from source.entity import LinearInput
from source.smithery_tools import linear_tools

mcp = FastMCP(
    name="Save Code Tool MCP",
    port=8001,
)


@mcp.tool(
    name="auto_linear",
    description="Call linear and slack tools to get issues and slack messages, then ",
)
async def auto_linear(
    after: str | None = None,
    limit: int | None = None,
    before: str | None = None,
    orderBy: str | None = None,
    project: str | None = None,
):
    # Get the linear session
    try:
        linear_client = await linear_tools()

        if not linear_client:
            return "Error getting linear client"


        # Use the context manager properly
        async with linear_client as (read, write, _):

            async with ClientSession(read, write) as linear_session:
                # Initialize the connection
                await linear_session.initialize()

                linear_tools_list = await linear_session.list_tools()
                if not linear_tools_list:
                    return "Error getting linear tools list"
                args = {
                    "assignee": "me",
                    "after": after,
                    "limit": limit,
                    "before": before,
                    "orderBy": orderBy,
                }

                args = {k: v for k, v in args.items() if v is not None}
                issue_results = (
                    (await linear_session.call_tool("list_issues", arguments=args))
                    .content[0]
                    .text
                )

                issue_results = json.loads(issue_results)  # dict

                # Validate we have issues
                if not issue_results or len(issue_results) == 0:
                    return "No issues found in Linear"


                issue_id, issue_description = None, None

                # If project is specified, try to find that specific issue
                if project:
                    for issue in issue_results:
                        if issue.get("identifier") == project:
                            issue_id = issue["id"]
                            issue_description = issue.get(
                                "description", "No description available"
                            )
                            break

                # # Sort by priority (lower value = higher priority, so we want ascending order)
                sorted_issues = sorted(
                    issue_results,
                    key=lambda x: x.get("priority", {}).get("value", float("inf")),
                )
                # If no specific project found or project not specified, get the highest priority issue
                if not issue_id:
                    # Get the first issue (highest priority after sorting)
                    first_issue = sorted_issues[0]
                    issue_id = first_issue["id"]
                    issue_description = first_issue.get(
                        "description", "No description available"
                    )

                if not issue_id:
                    return "Could not determine issue to process"

                # Get issue comments
                issue_comments = await linear_session.call_tool(
                    "list_comments", arguments={"issueId": issue_id}
                )
                issue_comments = json.loads(issue_comments.content[0].text)

                # Make a data structure to save the issue description and comments and feed it to a agent
                data_structure = {
                    "issue_description": issue_description,
                    "issue_comments": issue_comments,
                }
                return data_structure
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        return f"Error in auto_linear tool: {e}\nDetails: {error_details}"


@mcp.tool(
    name="save_file",
    description="Save a file to the local directory",
)
async def save_file(
    file_name: str,
    file_content: str,
):
    try:
        if not file_name:
            return "File name is required"
        if not file_content:
            return "File content is required"

        path = Path(file_name)
        file_name = path.with_suffix(".md")

        async with aiofiles.open(file_name, "w", encoding="utf-8") as f:
            await f.write(file_content or "")

        return "File saved successfully"
    except Exception as e:
        return f"Error saving file: {e}"

@mcp.prompt()
def prompt():
    return f"Call auto_linear tool to receive relevant issues and comments to process. After you have finished processing the issues, call save_file tool to save the file to the local directory."


async def test_auto_linear():
    """Test function to run auto_linear directly"""
    result = await auto_linear(limit=1)
    await save_file(file_name="issues.json", file_content=json.dumps(result, indent=2))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run in test mode
        asyncio.run(test_auto_linear())
    else:
        # Run as MCP server
        mcp.run(transport="streamable-http")
