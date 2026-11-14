"""Local utility and read-only build evidence tools."""

import json
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("local-tools")
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "home-assistant-run.json"


@mcp.tool
def current_time() -> str:
    """Return the current local date and time with its UTC offset."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


@mcp.tool
def word_count(text: str) -> int:
    """Count whitespace-separated words in the supplied text."""
    return len(text.split())


@mcp.tool
def get_build_evidence(run_id: str) -> dict:
    """Look up a saved Home Assistant GitHub Actions run by its exact run ID."""
    evidence = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if run_id == evidence["run_id"]:
        return {"status": "found", **evidence}
    return {"status": "missing", "run_id": run_id}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
