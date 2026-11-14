"""Local utility and read-only build evidence tools."""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("local-tools")
NOTES_DIR = Path(__file__).resolve().parent / "notes"
MAX_NOTE_BYTES = 16_384
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


@mcp.tool
def read_note(name: str) -> dict:
    """Read a UTF-8 Markdown note by its lowercase name, without the extension."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", name):
        return {"status": "invalid_name", "name": name}

    path = (NOTES_DIR / f"{name}.md").resolve()
    if path.parent != NOTES_DIR.resolve():
        return {"status": "invalid_name", "name": name}

    try:
        with path.open("rb") as note:
            data = note.read(MAX_NOTE_BYTES + 1)
    except FileNotFoundError:
        return {"status": "missing", "name": name}
    except OSError:
        return {"status": "unreadable", "name": name}

    if len(data) > MAX_NOTE_BYTES:
        return {"status": "too_large", "name": name}
    try:
        return {"status": "found", "name": name, "text": data.decode("utf-8")}
    except UnicodeDecodeError:
        return {"status": "unreadable", "name": name}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http", action="store_true", help="Serve MCP over loopback HTTP")
    parser.add_argument("--port", type=int, default=8000, help="Loopback HTTP port")
    args = parser.parse_args()
    if args.http:
        mcp.run(transport="http", host="127.0.0.1", port=args.port, show_banner=False)
    else:
        mcp.run(transport="stdio", show_banner=False)
