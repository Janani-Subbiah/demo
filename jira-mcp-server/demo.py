#!/usr/bin/env python3
"""
Demo script showing how to use the JIRA MCP Server tools
"""

import json

def show_demo():
    """Show example usage of the JIRA MCP Server"""
    
    print("🎯 JIRA MCP Server - Demo Usage")
    print("=" * 50)
    print()
    
    print("🔧 1. FETCH USER STORIES FROM PROJECT")
    print("-" * 30)
    print("Tool: fetch_user_stories")
    print("Description: Get all user stories from a specific project")
    print()
    
    example1 = {
        "project_key": "MYPROJ",
        "max_results": 20,
        "include_subtasks": False
    }
    print("Example request:")
    print(json.dumps(example1, indent=2))
    print()
    
    print("Expected response:")
    print("""Found 15 user stories:

**MYPROJ-101** - User login functionality
  Status: In Progress
  Type: Story
  Assignee: john.doe@company.com
  Story Points: 5.0
  Epic: MYPROJ-100
  Description: As a user, I want to log in securely...

**MYPROJ-102** - Password reset feature
  Status: To Do
  Type: Story
  Assignee: jane.smith@company.com
  Story Points: 3.0
...""")
    print()
    
    print("🔍 2. SEARCH ISSUES WITH JQL")
    print("-" * 30)
    print("Tool: search_jira_issues")
    print("Description: Search issues using JIRA Query Language")
    print()
    
    example2 = {
        "jql": "assignee = currentUser() AND status = 'In Progress'",
        "max_results": 10
    }
    print("Example request:")
    print(json.dumps(example2, indent=2))
    print()
    
    print("🎯 3. GET PROJECT USER STORIES WITH FILTERS")
    print("-" * 30)
    print("Tool: get_project_user_stories")
    print("Description: Get user stories with advanced filtering")
    print()
    
    example3 = {
        "project_key": "MYPROJ",
        "status": "In Progress",
        "assignee": "john.doe@company.com",
        "max_results": 15
    }
    print("Example request:")
    print(json.dumps(example3, indent=2))
    print()
    
    print("📋 4. GET SPECIFIC ISSUE DETAILS")
    print("-" * 30)
    print("Tool: get_jira_issue")
    print("Description: Get detailed information about a specific issue")
    print()
    
    example4 = {
        "issue_key": "MYPROJ-101"
    }
    print("Example request:")
    print(json.dumps(example4, indent=2))
    print()
    
    print("💡 USEFUL JQL EXAMPLES")
    print("-" * 30)
    
    jql_examples = [
        {
            "description": "All user stories in a project",
            "jql": 'project = "MYPROJ" AND issuetype = "Story"'
        },
        {
            "description": "High priority bugs",
            "jql": 'project = "MYPROJ" AND issuetype = "Bug" AND priority = "High"'
        },
        {
            "description": "Stories in current sprint",
            "jql": 'project = "MYPROJ" AND sprint in openSprints() AND issuetype = "Story"'
        },
        {
            "description": "Recently updated issues",
            "jql": 'project = "MYPROJ" AND updated >= -7d'
        },
        {
            "description": "Issues in specific epic",
            "jql": '"Epic Link" = "MYPROJ-100"'
        },
        {
            "description": "Unassigned user stories",
            "jql": 'project = "MYPROJ" AND issuetype = "Story" AND assignee is EMPTY'
        }
    ]
    
    for i, example in enumerate(jql_examples, 1):
        print(f"{i}. {example['description']}")
        print(f"   JQL: {example['jql']}")
        print()
    
    print("🚀 GETTING STARTED")
    print("-" * 30)
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Configure .env file with your JIRA credentials")
    print("3. Test connection: python test_server.py")
    print("4. Add to MCP config and start using!")
    print()
    
    print("📖 For more information, see README.md")

if __name__ == "__main__":
    show_demo()

