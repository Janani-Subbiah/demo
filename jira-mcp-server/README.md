# JIRA MCP Server

An MCP (Model Context Protocol) server for fetching JIRA user stories and issues using the JIRA REST API.

## Features

- 🎯 **Fetch User Stories**: Get user stories from specific projects or using custom JQL
- 🔍 **Search Issues**: Search JIRA issues with powerful JQL queries
- 📋 **Issue Details**: Get detailed information about specific issues
- 🎨 **Filtering**: Filter user stories by status, assignee, epic, and more
- 🚀 **Fast & Efficient**: Async HTTP client with proper error handling

## Installation

1. **Clone or download the server files**
   ```bash
   cd jira-mcp-server
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your JIRA credentials
   ```

## Configuration

Set the following environment variables (or create a `.env` file):

- `JIRA_URL`: Your JIRA instance URL (e.g., `https://yourcompany.atlassian.net`)
- `JIRA_EMAIL`: Your JIRA account email
- `JIRA_API_TOKEN`: Your JIRA API token (create one at Account Settings > Security > API tokens)
- `JIRA_SSL_VERIFY`: SSL verification (default: `true`)

### Getting a JIRA API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label and copy the token
4. Use your email and this token for authentication

## MCP Integration

Add to your MCP configuration file (e.g., `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "jira-user-stories": {
      "command": "python",
      "args": ["/path/to/jira-mcp-server/server.py"],
      "env": {
        "JIRA_URL": "https://yourcompany.atlassian.net",
        "JIRA_EMAIL": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token",
        "JIRA_SSL_VERIFY": "true"
      }
    }
  }
}
```

## Available Tools

### 1. `fetch_user_stories`
Fetch user stories from a project or using custom JQL.

**Parameters:**
- `project_key` (string): JIRA project key (e.g., "PROJ")
- `jql` (string): Custom JQL query (alternative to project_key)
- `max_results` (integer): Maximum results (default: 50, max: 100)
- `include_subtasks` (boolean): Include subtasks (default: false)

**Example Usage:**
```
Fetch user stories from project "MYPROJ"
```

### 2. `get_jira_issue`
Get detailed information about a specific JIRA issue.

**Parameters:**
- `issue_key` (string): JIRA issue key (e.g., "PROJ-123")

**Example Usage:**
```
Get details for issue PROJ-123
```

### 3. `search_jira_issues`
Search JIRA issues using JQL (JIRA Query Language).

**Parameters:**
- `jql` (string): JQL query
- `max_results` (integer): Maximum results (default: 50)
- `start_at` (integer): Starting index for pagination

**Example Usage:**
```
Search for issues: assignee = currentUser() AND status = "In Progress"
```

### 4. `get_project_user_stories`
Get user stories from a project with advanced filtering.

**Parameters:**
- `project_key` (string): JIRA project key
- `status` (string): Filter by status (optional)
- `assignee` (string): Filter by assignee (optional)
- `epic` (string): Filter by epic key (optional)
- `max_results` (integer): Maximum results

**Example Usage:**
```
Get user stories from MYPROJ assigned to john.doe@company.com with status "In Progress"
```

## JQL Examples

Here are some useful JQL queries you can use with the search tools:

```sql
-- All user stories in a project
project = "MYPROJ" AND issuetype = "Story"

-- User stories assigned to you
project = "MYPROJ" AND issuetype = "Story" AND assignee = currentUser()

-- Stories in specific sprint
project = "MYPROJ" AND sprint = "Sprint 1" AND issuetype = "Story"

-- High priority bugs
project = "MYPROJ" AND issuetype = "Bug" AND priority = "High"

-- Recently updated issues
project = "MYPROJ" AND updated >= -7d

-- Stories with specific labels
project = "MYPROJ" AND issuetype = "Story" AND labels in ("frontend", "api")

-- Issues in epic
"Epic Link" = "MYPROJ-100"
```

## Testing

You can test the server by running it directly:

```bash
python server.py
```

The server will start and wait for MCP protocol messages on stdin/stdout.

## Troubleshooting

### Common Issues

1. **Authentication Error**: Verify your JIRA_EMAIL and JIRA_API_TOKEN are correct
2. **Connection Error**: Check your JIRA_URL and network connectivity
3. **Permission Error**: Ensure your JIRA account has access to the projects you're querying
4. **SSL Error**: Try setting JIRA_SSL_VERIFY=false if you have SSL issues (not recommended for production)

### Debug Mode

Set logging level to DEBUG for more verbose output:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Example Interactions

### Fetch User Stories from a Project
```
User: "Fetch user stories from project ABC"
Server: Found 15 user stories:

**ABC-101** - User login functionality
  Status: In Progress
  Type: Story
  Assignee: john.doe@company.com
  Story Points: 5.0
  ...
```

### Get Issue Details
```
User: "Get details for issue ABC-101"
Server: **ABC-101** - User login functionality

**Type:** Story
**Status:** In Progress
**Priority:** High
**Assignee:** john.doe@company.com
**Reporter:** jane.smith@company.com
...
```

## API Reference

The server implements the MCP (Model Context Protocol) and provides the following capabilities:

- **Tools**: 4 tools for various JIRA operations
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Authentication**: Secure API token-based authentication
- **Pagination**: Support for paginated results
- **Filtering**: Advanced filtering options for better results

## Security

- API tokens are more secure than passwords
- SSL verification is enabled by default
- Credentials are passed via environment variables
- No sensitive data is logged

## License

This project is open source. Feel free to modify and distribute according to your needs.

