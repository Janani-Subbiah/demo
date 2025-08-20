#!/usr/bin/env python3
"""
JIRA MCP Server - Fetch user stories and issues using JIRA REST API
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
import base64

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    GetPromptResult,
    ListPromptsResult,
    ListToolsResult,
    PromptMessage,
    TextContent,
    Tool,
)
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JiraConfig:
    def __init__(self):
        self.base_url = os.getenv("JIRA_URL", "").rstrip('/')
        self.email = os.getenv("JIRA_EMAIL", "")
        self.api_token = os.getenv("JIRA_API_TOKEN", "")
        self.ssl_verify = os.getenv("JIRA_SSL_VERIFY", "true").lower() == "true"
        
        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError("JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN environment variables are required")
    
    def get_auth_header(self) -> str:
        """Generate Basic Auth header for JIRA API"""
        credentials = f"{self.email}:{self.api_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"

class JiraIssue(BaseModel):
    """Model for JIRA issue/user story"""
    key: str
    id: str
    summary: str
    description: Optional[str]
    status: str
    issue_type: str
    assignee: Optional[str]
    reporter: Optional[str]
    priority: Optional[str]
    created: str
    updated: str
    story_points: Optional[float]
    epic_link: Optional[str]
    labels: List[str]

class JiraClient:
    def __init__(self, config: JiraConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=30.0,
            verify=config.ssl_verify,
            headers={
                "Authorization": config.get_auth_header(),
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL for JIRA API endpoint"""
        return urljoin(f"{self.config.base_url}/rest/api/3/", endpoint.lstrip('/'))
    
    def _parse_issue(self, issue_data: Dict[str, Any]) -> JiraIssue:
        """Parse JIRA issue data into JiraIssue model"""
        fields = issue_data.get("fields", {})
        
        # Extract assignee and reporter
        assignee = None
        if fields.get("assignee"):
            assignee = fields["assignee"].get("displayName") or fields["assignee"].get("emailAddress")
        
        reporter = None
        if fields.get("reporter"):
            reporter = fields["reporter"].get("displayName") or fields["reporter"].get("emailAddress")
        
        # Extract story points (could be in customfield_10016 or similar)
        story_points = None
        for key, value in fields.items():
            if "story" in key.lower() and "point" in key.lower() and isinstance(value, (int, float)):
                story_points = float(value)
                break
        
        # Extract epic link
        epic_link = None
        epic_field = fields.get("customfield_10014")  # Common epic link field
        if epic_field:
            epic_link = epic_field
        
        return JiraIssue(
            key=issue_data["key"],
            id=issue_data["id"],
            summary=fields.get("summary", ""),
            description=fields.get("description", {}).get("content", [{}])[0].get("content", [{}])[0].get("text", "") if fields.get("description") else None,
            status=fields.get("status", {}).get("name", ""),
            issue_type=fields.get("issuetype", {}).get("name", ""),
            assignee=assignee,
            reporter=reporter,
            priority=fields.get("priority", {}).get("name"),
            created=fields.get("created", ""),
            updated=fields.get("updated", ""),
            story_points=story_points,
            epic_link=epic_link,
            labels=fields.get("labels", [])
        )
    
    async def search_issues(self, jql: str, max_results: int = 50, start_at: int = 0) -> List[JiraIssue]:
        """Search for issues using JQL"""
        url = self._build_url("search")
        
        params = {
            "jql": jql,
            "maxResults": max_results,
            "startAt": start_at,
            "fields": "summary,description,status,issuetype,assignee,reporter,priority,created,updated,labels,customfield_*"
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            issues = []
            for issue_data in data.get("issues", []):
                try:
                    issue = self._parse_issue(issue_data)
                    issues.append(issue)
                except Exception as e:
                    logger.warning(f"Failed to parse issue {issue_data.get('key', 'unknown')}: {e}")
            
            return issues
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while searching issues: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching issues: {e}")
            raise
    
    async def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """Get a specific issue by key"""
        url = self._build_url(f"issue/{issue_key}")
        
        params = {
            "fields": "summary,description,status,issuetype,assignee,reporter,priority,created,updated,labels,customfield_*"
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            issue_data = response.json()
            return self._parse_issue(issue_data)
        except httpx.HTTPError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error while fetching issue {issue_key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching issue {issue_key}: {e}")
            raise

# Initialize server
server = Server("jira-mcp-server")

@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools for JIRA operations"""
    return ListToolsResult(
        tools=[
            Tool(
                name="fetch_user_stories",
                description="Fetch JIRA user stories from a specific project or using JQL",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "JIRA project key (e.g., 'PROJ'). Either project_key or jql is required."
                        },
                        "jql": {
                            "type": "string",
                            "description": "Custom JQL query. Either project_key or jql is required."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 50, max: 100)",
                            "minimum": 1,
                            "maximum": 100
                        },
                        "include_subtasks": {
                            "type": "boolean",
                            "description": "Include subtasks in results (default: false)"
                        }
                    },
                    "anyOf": [
                        {"required": ["project_key"]},
                        {"required": ["jql"]}
                    ]
                }
            ),
            Tool(
                name="get_jira_issue",
                description="Get details of a specific JIRA issue by key",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "JIRA issue key (e.g., 'PROJ-123')"
                        }
                    },
                    "required": ["issue_key"]
                }
            ),
            Tool(
                name="search_jira_issues",
                description="Search JIRA issues using custom JQL query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "jql": {
                            "type": "string",
                            "description": "JQL (JIRA Query Language) query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 50, max: 100)",
                            "minimum": 1,
                            "maximum": 100
                        },
                        "start_at": {
                            "type": "integer",
                            "description": "Starting index for pagination (default: 0)",
                            "minimum": 0
                        }
                    },
                    "required": ["jql"]
                }
            ),
            Tool(
                name="get_project_user_stories",
                description="Get all user stories from a specific project with filtering options",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "JIRA project key (e.g., 'PROJ')"
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status (e.g., 'To Do', 'In Progress', 'Done')"
                        },
                        "assignee": {
                            "type": "string",
                            "description": "Filter by assignee email or username"
                        },
                        "epic": {
                            "type": "string",
                            "description": "Filter by epic key (e.g., 'PROJ-100')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 50)",
                            "minimum": 1,
                            "maximum": 100
                        }
                    },
                    "required": ["project_key"]
                }
            )
        ]
    )

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls for JIRA operations"""
    try:
        config = JiraConfig()
        
        async with JiraClient(config) as client:
            if name == "fetch_user_stories":
                return await handle_fetch_user_stories(client, arguments)
            elif name == "get_jira_issue":
                return await handle_get_jira_issue(client, arguments)
            elif name == "search_jira_issues":
                return await handle_search_jira_issues(client, arguments)
            elif name == "get_project_user_stories":
                return await handle_get_project_user_stories(client, arguments)
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                )
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

async def handle_fetch_user_stories(client: JiraClient, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle fetch_user_stories tool call"""
    project_key = arguments.get("project_key")
    jql = arguments.get("jql")
    max_results = arguments.get("max_results", 50)
    include_subtasks = arguments.get("include_subtasks", False)
    
    if not project_key and not jql:
        return CallToolResult(
            content=[TextContent(type="text", text="Either 'project_key' or 'jql' parameter is required")]
        )
    
    if jql:
        search_jql = jql
    else:
        # Build JQL for user stories in the project
        if include_subtasks:
            search_jql = f'project = "{project_key}" AND issuetype in ("Story", "User Story", "Sub-task")'
        else:
            search_jql = f'project = "{project_key}" AND issuetype in ("Story", "User Story")'
    
    try:
        issues = await client.search_issues(search_jql, max_results)
        
        if not issues:
            return CallToolResult(
                content=[TextContent(type="text", text="No user stories found matching the criteria")]
            )
        
        # Format the results
        result_text = f"Found {len(issues)} user stories:\n\n"
        for issue in issues:
            result_text += f"**{issue.key}** - {issue.summary}\n"
            result_text += f"  Status: {issue.status}\n"
            result_text += f"  Type: {issue.issue_type}\n"
            if issue.assignee:
                result_text += f"  Assignee: {issue.assignee}\n"
            if issue.story_points:
                result_text += f"  Story Points: {issue.story_points}\n"
            if issue.epic_link:
                result_text += f"  Epic: {issue.epic_link}\n"
            if issue.description:
                desc_preview = issue.description[:100] + "..." if len(issue.description) > 100 else issue.description
                result_text += f"  Description: {desc_preview}\n"
            result_text += "\n"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
    
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error fetching user stories: {str(e)}")]
        )

async def handle_get_jira_issue(client: JiraClient, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle get_jira_issue tool call"""
    issue_key = arguments.get("issue_key")
    
    if not issue_key:
        return CallToolResult(
            content=[TextContent(type="text", text="'issue_key' parameter is required")]
        )
    
    try:
        issue = await client.get_issue(issue_key)
        
        if not issue:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Issue {issue_key} not found")]
            )
        
        # Format the detailed issue information
        result_text = f"**{issue.key}** - {issue.summary}\n\n"
        result_text += f"**Type:** {issue.issue_type}\n"
        result_text += f"**Status:** {issue.status}\n"
        result_text += f"**Priority:** {issue.priority or 'Not set'}\n"
        result_text += f"**Assignee:** {issue.assignee or 'Unassigned'}\n"
        result_text += f"**Reporter:** {issue.reporter or 'Unknown'}\n"
        result_text += f"**Created:** {issue.created}\n"
        result_text += f"**Updated:** {issue.updated}\n"
        
        if issue.story_points:
            result_text += f"**Story Points:** {issue.story_points}\n"
        
        if issue.epic_link:
            result_text += f"**Epic:** {issue.epic_link}\n"
        
        if issue.labels:
            result_text += f"**Labels:** {', '.join(issue.labels)}\n"
        
        if issue.description:
            result_text += f"\n**Description:**\n{issue.description}\n"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
    
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error fetching issue {issue_key}: {str(e)}")]
        )

async def handle_search_jira_issues(client: JiraClient, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle search_jira_issues tool call"""
    jql = arguments.get("jql")
    max_results = arguments.get("max_results", 50)
    start_at = arguments.get("start_at", 0)
    
    if not jql:
        return CallToolResult(
            content=[TextContent(type="text", text="'jql' parameter is required")]
        )
    
    try:
        issues = await client.search_issues(jql, max_results, start_at)
        
        if not issues:
            return CallToolResult(
                content=[TextContent(type="text", text="No issues found matching the JQL query")]
            )
        
        # Format the results
        result_text = f"Found {len(issues)} issues matching the query:\n\n"
        for issue in issues:
            result_text += f"**{issue.key}** - {issue.summary}\n"
            result_text += f"  Status: {issue.status} | Type: {issue.issue_type}\n"
            if issue.assignee:
                result_text += f"  Assignee: {issue.assignee}\n"
            result_text += "\n"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
    
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error searching issues: {str(e)}")]
        )

async def handle_get_project_user_stories(client: JiraClient, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle get_project_user_stories tool call"""
    project_key = arguments.get("project_key")
    status = arguments.get("status")
    assignee = arguments.get("assignee")
    epic = arguments.get("epic")
    max_results = arguments.get("max_results", 50)
    
    if not project_key:
        return CallToolResult(
            content=[TextContent(type="text", text="'project_key' parameter is required")]
        )
    
    # Build JQL query with filters
    jql_parts = [f'project = "{project_key}"', 'issuetype in ("Story", "User Story")']
    
    if status:
        jql_parts.append(f'status = "{status}"')
    
    if assignee:
        jql_parts.append(f'assignee = "{assignee}"')
    
    if epic:
        jql_parts.append(f'"Epic Link" = "{epic}"')
    
    jql = " AND ".join(jql_parts)
    
    try:
        issues = await client.search_issues(jql, max_results)
        
        if not issues:
            return CallToolResult(
                content=[TextContent(type="text", text="No user stories found matching the criteria")]
            )
        
        # Format the results with more details
        result_text = f"Found {len(issues)} user stories in project {project_key}:\n\n"
        
        for issue in issues:
            result_text += f"**{issue.key}** - {issue.summary}\n"
            result_text += f"  📊 Status: {issue.status}\n"
            
            if issue.assignee:
                result_text += f"  👤 Assignee: {issue.assignee}\n"
            else:
                result_text += f"  👤 Assignee: Unassigned\n"
            
            if issue.story_points:
                result_text += f"  🎯 Story Points: {issue.story_points}\n"
            
            if issue.epic_link:
                result_text += f"  📋 Epic: {issue.epic_link}\n"
            
            if issue.labels:
                result_text += f"  🏷️ Labels: {', '.join(issue.labels)}\n"
            
            result_text += f"  📅 Updated: {issue.updated}\n"
            result_text += "\n"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )
    
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error fetching project user stories: {str(e)}")]
        )

async def main():
    """Run the JIRA MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jira-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())

