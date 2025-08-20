#!/usr/bin/env python3
"""
Test script for JIRA MCP Server
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to Python path so we can import server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import JiraConfig, JiraClient

async def test_jira_connection():
    """Test basic JIRA connection and authentication"""
    try:
        print("🔧 Testing JIRA MCP Server...")
        print("-" * 50)
        
        # Initialize configuration
        config = JiraConfig()
        print(f"✅ Configuration loaded")
        print(f"   JIRA URL: {config.base_url}")
        print(f"   Email: {config.email}")
        print(f"   SSL Verify: {config.ssl_verify}")
        print()
        
        # Test connection
        async with JiraClient(config) as client:
            print("🔗 Testing JIRA connection...")
            
            # Test with a simple search
            test_jql = "ORDER BY created DESC"
            issues = await client.search_issues(test_jql, max_results=1)
            
            print(f"✅ Connection successful!")
            print(f"   Found {len(issues)} test issue(s)")
            
            if issues:
                issue = issues[0]
                print(f"   Latest issue: {issue.key} - {issue.summary}")
                print(f"   Status: {issue.status}")
                print(f"   Type: {issue.issue_type}")
            
            print()
            print("🎯 Testing user story search...")
            
            # Test user story search
            story_jql = 'issuetype in ("Story", "User Story") ORDER BY created DESC'
            stories = await client.search_issues(story_jql, max_results=5)
            
            print(f"✅ Found {len(stories)} user stories")
            
            for i, story in enumerate(stories[:3], 1):
                print(f"   {i}. {story.key} - {story.summary}")
                print(f"      Status: {story.status} | Assignee: {story.assignee or 'Unassigned'}")
            
            if len(stories) > 3:
                print(f"   ... and {len(stories) - 3} more")
            
        print()
        print("🎉 All tests passed! The JIRA MCP Server is ready to use.")
        print()
        print("📝 Next steps:")
        print("1. Add the server to your MCP configuration")
        print("2. Start using it with your MCP client")
        print("3. Try commands like 'fetch user stories from project XYZ'")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print()
        print("🔧 Troubleshooting:")
        print("1. Check your .env file has correct JIRA credentials")
        print("2. Verify your JIRA URL is accessible")
        print("3. Ensure your API token has proper permissions")
        print("4. Check network connectivity")
        return False
    
    return True

async def test_specific_project(project_key: str):
    """Test fetching user stories from a specific project"""
    try:
        config = JiraConfig()
        
        async with JiraClient(config) as client:
            print(f"🎯 Testing project '{project_key}'...")
            
            jql = f'project = "{project_key}" AND issuetype in ("Story", "User Story") ORDER BY created DESC'
            stories = await client.search_issues(jql, max_results=10)
            
            print(f"✅ Found {len(stories)} user stories in project {project_key}")
            
            for story in stories[:5]:
                print(f"   • {story.key} - {story.summary}")
            
            if len(stories) > 5:
                print(f"   ... and {len(stories) - 5} more")
                
    except Exception as e:
        print(f"❌ Project test failed: {str(e)}")

if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠️  No .env file found. Please copy env.example to .env and configure your credentials.")
        sys.exit(1)
    
    # Run basic tests
    success = asyncio.run(test_jira_connection())
    
    if success and len(sys.argv) > 1:
        # Test specific project if provided
        project_key = sys.argv[1]
        print("\n" + "="*50)
        asyncio.run(test_specific_project(project_key))
    
    print("\n📖 For more information, see README.md")

