#!/usr/bin/env python3
"""
Setup script for JIRA MCP Server
"""

from setuptools import setup, find_packages

setup(
    name="jira-mcp-server",
    version="1.0.0",
    description="MCP server for fetching JIRA user stories using REST API",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.0.0",
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "jira-mcp-server=server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

