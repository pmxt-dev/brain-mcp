import os
import git
import sys
from mcp.server.fastmcp import FastMCP

# Path to the brain repo
BRAIN_REPO_PATH = os.environ.get("BRAIN_REPO_PATH", "/opt/data/repos/company-brain")

mcp = FastMCP("Company Brain")

def get_repo():
    if not os.path.exists(BRAIN_REPO_PATH):
        raise Exception(f"Brain repo not found at {BRAIN_REPO_PATH}. Set BRAIN_REPO_PATH env var.")
    return git.Repo(BRAIN_REPO_PATH)

@mcp.tool()
def list_knowledge(directory: str = "docs") -> str:
    """List knowledge files in the company brain."""
    results = []
    full_path = os.path.join(BRAIN_REPO_PATH, directory)
    if not os.path.exists(full_path):
        return f"Error: Directory {directory} not found."
    for root, _, files in os.walk(full_path):
        for file in files:
            if file.endswith(".md"):
                results.append(os.path.relpath(os.path.join(root, file), BRAIN_REPO_PATH))
    return "\n".join(results)

@mcp.tool()
def read_knowledge(file_path: str) -> str:
    """Read a specific knowledge file from the brain."""
    full_path = os.path.join(BRAIN_REPO_PATH, file_path)
    with open(full_path, "r") as f:
        return f.read()

@mcp.tool()
def search_knowledge(query: str) -> str:
    """Search for a keyword across the brain docs."""
    repo = get_repo()
    try:
        results = repo.git.grep("-l", query, "--", "docs")
        return results
    except:
        return "No matches found."

@mcp.tool()
def write_to_brain(file_path: str, content: str, commit_message: str) -> str:
    """Pull, write, commit, and push an update to the brain."""
    repo = get_repo()
    repo.remotes.origin.pull()
    full_path = os.path.join(BRAIN_REPO_PATH, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)
    repo.index.add([file_path])
    repo.index.commit(commit_message)
    repo.remote().push()
    return f"Pushed update to {file_path}"

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
