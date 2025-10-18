import asyncio
import json
import aiofiles

from pathlib import Path
from mcp.server.fastmcp import FastMCP

from source.entity import LinearInput
from source.smithery_tools import linear_tools

mcp = FastMCP(
    name="Save Code Tool MCP",
    host="0.0.0.0",
    port=8050,
)


@mcp.tool(
    name="auto_linear",
    description="Call linear and slack tools to get issues and slack messages, then ",
)
async def auto_linear(
    input_args: LinearInput
):
    # Get the linear session
    try:
        linear_client = await linear_tools()

        if not linear_client:
            return "Error getting linear client"

        # print(f"Linear client initialized")

        # Use the context manager properly
        async with linear_client as (read, write, _):
            from mcp import ClientSession

            async with ClientSession(read, write) as linear_session:
                # Initialize the connection
                await linear_session.initialize()

                linear_tools_list = await linear_session.list_tools()
                if not linear_tools_list:
                    return "Error getting linear tools list"
                # print(f"Got Linear tools list")
                args = {
                    "team": input_args.team,
                    "after": input_args.after,
                    "cycle": input_args.cycle,
                    "label": input_args.label,
                    "limit": input_args.limit,
                    "query": input_args.query,
                    "state": input_args.state,
                    "before": input_args.before,
                    "orderBy": input_args.orderBy,
                    "project": input_args.project,
                    "assignee": input_args.assignee,
                    "parentId": input_args.parentId,
                    "createdAt": input_args.createdAt,
                    "updatedAt": input_args.updatedAt,
                    "includeArchived": input_args.includeArchived,
                }

                args = {k: v for k, v in args.items() if v is not None}
                issue_results = (
                    (await linear_session.call_tool("list_issues", arguments=args))
                    .content[0]
                    .text
                )

                issue_results = json.loads(issue_results)  # dict
                # print(f"Tool result: {issue_results}, length: {len(issue_results)}")

                # Validate we have issues
                if not issue_results or len(issue_results) == 0:
                    return "No issues found in Linear"

                # Sort by priority (lower value = higher priority, so we want ascending order)
                sorted_issues = sorted(
                    issue_results,
                    key=lambda x: x.get("priority", {}).get("value", float("inf")),
                )

                issue_id, issue_description = None, None

                # If project is specified, try to find that specific issue
                if input_args.project:
                    for issue in sorted_issues:
                        if issue.get("identifier") == input_args.project:
                            issue_id = issue["id"]
                            issue_description = issue.get(
                                "description", "No description available"
                            )
                            # print(
                            #     f"Found specific issue: {issue['id']}, identifier: {issue['identifier']}"
                            # )
                            break

                # If no specific project found or project not specified, get the highest priority issue
                if not issue_id:
                    # Get the first issue (highest priority after sorting)
                    first_issue = sorted_issues[0]
                    issue_id = first_issue["id"]
                    issue_description = first_issue.get(
                        "description", "No description available"
                    )
                    # print(
                    #     f"Using highest priority issue: {issue_id}, identifier: {first_issue.get('identifier', 'N/A')}"
                    # )

                if not issue_id:
                    return "Could not determine issue to process"

                # Get issue comments
                issue_comments = await linear_session.call_tool(
                    "list_comments", arguments={"issueId": issue_id}
                )
                issue_comments = json.loads(issue_comments.content[0].text)

                # for comment in issue_comments:
                #     print(
                #         f"Comment: {comment['id']}, content: {comment.get('body', comment.get('content', 'No content'))}"
                #     )
                # print(f"Issue comments: {issue_comments}")

                # Make a data structure to save the issue description and comments and feed it to a agent
                data_structure = {
                    "issue_description": issue_description,
                    "issue_comments": issue_comments,
                }
                # print(f"Data structure: {data_structure}")
                return data_structure
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        # print(f"Full error traceback: {error_details}")
        return f"Error in auto_linear tool: {e}\nDetails: {error_details}"


@mcp.tool(
    name="save_file",
    description="Save a file to the local directory",
)
async def save_file(
    file_name: str,
    file_content: str ,
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
    return (
        f"Call auto_linear tool to receive relevant issues and comments to process. After you have finished processing the issues, call save_file tool to save the file to the local directory."
    )

async def test_auto_linear():
    """Test function to run auto_linear directly"""
    # print("Testing auto_linear function...")
    result = await auto_linear()
    # print(f"Result: {result}")
    save_file(file_name="issues.json", file_content=result)    


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run in test mode
        asyncio.run(test_auto_linear())
    else:
        # Run as MCP server
        # print("Starting MCP server on port 8050...")
        # print("To test the function directly, run: python main.py test")
        mcp.run()
