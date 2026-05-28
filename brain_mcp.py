import os
import sys
import base64
import httpx
from mcp.server.fastmcp import FastMCP

# Config from Env
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
BRAIN_REPO = os.environ.get("BRAIN_REPO", "pmxt-dev/company-brain")

mcp = FastMCP(
    "Company Brain",
    instructions=(
        "Knowledge base for PMXT. When writing architecture, decision, or project "
        "docs via write_to_brain, include an ASCII diagram for any flow, system, or "
        "sequence with more than ~3 moving parts: boxes for components, arrows for "
        "data/fund flow, numbered steps, and a 'START HERE' marker on build plans. "
        "Keep diagrams in fenced code blocks. Never leave a multi-actor flow in prose only."
    ),
)

def get_headers():
    if not GITHUB_TOKEN:
        raise Exception("GITHUB_TOKEN not found in environment.")
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

@mcp.tool()
def list_knowledge(path: str = "docs") -> str:
    """List all knowledge files in the company brain via GitHub API."""
    url = f"https://api.github.com/repos/{BRAIN_REPO}/contents/{path}"
    with httpx.Client() as client:
        resp = client.get(url, headers=get_headers())
        resp.raise_for_status()
        items = resp.json()
        return "\n".join([item["path"] for item in items if item["type"] == "file" or item["type"] == "dir"])

@mcp.tool()
def read_knowledge(file_path: str) -> str:
    """Read a specific knowledge file from the company brain via GitHub."""
    url = f"https://api.github.com/repos/{BRAIN_REPO}/contents/{file_path}"
    with httpx.Client() as client:
        resp = client.get(url, headers=get_headers())
        resp.raise_for_status()
        data = resp.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content

@mcp.tool()
def write_to_brain(file_path: str, content: str, commit_message: str) -> str:
    """Update or create a file in the company brain using the GitHub API."""
    url = f"https://api.github.com/repos/{BRAIN_REPO}/contents/{file_path}"
    headers = get_headers()
    
    with httpx.Client() as client:
        # 1. Get current file (for SHA if it exists)
        resp = client.get(url, headers=headers)
        sha = None
        if resp.status_code == 200:
            sha = resp.json()["sha"]
        
        # 2. Push update
        payload = {
            "message": commit_message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8")
        }
        if sha:
            payload["sha"] = sha
            
        put_resp = client.put(url, headers=headers, json=payload)
        put_resp.raise_for_status()
        
    return f"Successfully pushed {file_path} to GitHub."

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
