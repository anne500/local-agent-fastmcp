"""Exercise tool discovery and execution through a real stdio subprocess."""

import sys
import unittest
from datetime import datetime
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from langchain_mcp_adapters.client import MultiServerMCPClient

SERVER = Path(__file__).resolve().parents[1] / "mcp_server.py"


class StdioTests(unittest.IsolatedAsyncioTestCase):
    async def test_fastmcp_tool_contract(self) -> None:
        transport = StdioTransport(command=sys.executable, args=[str(SERVER)])
        async with Client(transport, timeout=15) as client:
            tools = await client.list_tools()
            self.assertEqual(
                {tool.name for tool in tools},
                {"current_time", "word_count", "get_build_evidence", "read_note"},
            )

            count = await client.call_tool("word_count", {"text": "Cedar needs a smoke test."})
            self.assertEqual(count.data, 5)

            result = await client.call_tool("current_time", {})
            self.assertIsNotNone(datetime.fromisoformat(result.data).utcoffset())

            found = await client.call_tool("get_build_evidence", {"run_id": "21890541227"})
            self.assertEqual(found.data["status"], "found")
            self.assertEqual(found.data["conclusion"], "failure")
            self.assertTrue(found.data["source_url"].endswith("/21890541227"))

            missing = await client.call_tool("get_build_evidence", {"run_id": "99999999999"})
            self.assertEqual(missing.data, {"status": "missing", "run_id": "99999999999"})

    async def test_note_lookup_and_path_validation(self) -> None:
        transport = StdioTransport(command=sys.executable, args=[str(SERVER)])
        async with Client(transport, timeout=15) as client:
            found = await client.call_tool("read_note", {"name": "cedar"})
            self.assertEqual(found.data["status"], "found")
            self.assertIn("Cedar needs a CI smoke test.", found.data["text"])
            missing = await client.call_tool("read_note", {"name": "missing-smoke-test-note"})
            self.assertEqual(missing.data["status"], "missing")
            traversal = await client.call_tool("read_note", {"name": "../README"})
            self.assertEqual(traversal.data["status"], "invalid_name")

    async def test_langchain_adapter_discovers_and_calls_tools(self) -> None:
        client = MultiServerMCPClient(
            {"local": {"command": sys.executable, "args": [str(SERVER)], "transport": "stdio"}}
        )
        tools = {tool.name: tool for tool in await client.get_tools()}
        result = await tools["word_count"].ainvoke({"text": "Cedar needs a smoke test."})
        self.assertEqual(result[0]["text"], "5")
