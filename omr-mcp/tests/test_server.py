"""Tests for OMR MCP server module."""

import asyncio
import json
import pytest

from omr_mcp.server import _detect_input_format


class TestDetectInputFormat:
    """Tests for input format detection."""

    def test_explicit_path_hint(self):
        assert _detect_input_format("/some/path/image.png", "path") == "path"

    def test_explicit_base64_hint(self):
        assert _detect_input_format("/some/path/image.png", "base64") == "base64"

    def test_auto_detect_path(self):
        assert _detect_input_format("/home/user/image.png", None) == "path"
        assert _detect_input_format("./relative/path.jpg", None) == "path"
        assert _detect_input_format("C:\\Windows\\path.png", None) == "path"

    def test_auto_detect_base64_data_url(self):
        base64_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        assert _detect_input_format(base64_data, None) == "base64"

    def test_auto_detect_long_base64(self):
        # Long string without path separators should be detected as base64
        long_base64 = "A" * 600
        assert _detect_input_format(long_base64, None) == "base64"


class TestServerToolSchemas:
    """Tests for MCP server tool definitions."""

    def test_list_tools_returns_all_tools(self):
        from omr_mcp.server import list_tools

        tools = asyncio.get_event_loop().run_until_complete(list_tools())
        tool_names = [t.name for t in tools]

        assert "recognize_sheet" in tool_names
        assert "recognize_sheet_to_file" in tool_names
        assert "recognize_sheets" in tool_names
        assert "list_capabilities" in tool_names
        assert "list_supported_formats" in tool_names  # kept as deprecated alias

    def test_recognize_sheet_schema(self):
        from omr_mcp.server import list_tools
        
        tools = asyncio.get_event_loop().run_until_complete(list_tools())
        recognize_sheet = next(t for t in tools if t.name == "recognize_sheet")
        
        schema = recognize_sheet.inputSchema
        assert "image" in schema["properties"]
        assert "format" in schema["properties"]
        assert schema["required"] == ["image"]

    def test_recognize_sheet_to_file_schema(self):
        from omr_mcp.server import list_tools
        
        tools = asyncio.get_event_loop().run_until_complete(list_tools())
        tool = next(t for t in tools if t.name == "recognize_sheet_to_file")
        
        schema = tool.inputSchema
        assert "input_path" in schema["properties"]
        assert "output_path" in schema["properties"]
        assert schema["required"] == ["input_path"]

    def test_recognize_sheets_schema(self):
        from omr_mcp.server import list_tools

        tools = asyncio.get_event_loop().run_until_complete(list_tools())
        tool = next(t for t in tools if t.name == "recognize_sheets")

        schema = tool.inputSchema
        assert "images" in schema["properties"]
        assert schema["properties"]["images"]["type"] == "array"
        assert schema["required"] == ["images"]

    def test_list_capabilities_tool(self):
        from omr_mcp.server import call_tool

        result = asyncio.get_event_loop().run_until_complete(
            call_tool("list_capabilities", {})
        )
        assert len(result) == 1

        data = json.loads(result[0].text)
        assert data["server"] == "omr-mcp"
        assert "input_formats" in data
        assert "output_formats" in data
        assert "tools" in data
        assert "backend" in data
        assert "png" in data["input_formats"]
        assert "musicxml" in data["output_formats"]
        assert "list_capabilities" in data["tools"]

    def test_list_supported_formats_tool(self):
        """Deprecated alias — should return the same payload as list_capabilities."""
        from omr_mcp.server import call_tool

        result = asyncio.get_event_loop().run_until_complete(
            call_tool("list_supported_formats", {})
        )
        assert len(result) == 1

        data = json.loads(result[0].text)
        assert "input_formats" in data
        assert "output_formats" in data
        assert "png" in data["input_formats"]
        assert "musicxml" in data["output_formats"]

    def test_recognize_sheets_empty_list_returns_error(self):
        from omr_mcp.server import call_tool

        result = asyncio.get_event_loop().run_until_complete(
            call_tool("recognize_sheets", {"images": []})
        )
        data = json.loads(result[0].text)
        assert "error" in data

    def test_recognize_sheets_invalid_images_param_returns_error(self):
        from omr_mcp.server import call_tool

        result = asyncio.get_event_loop().run_until_complete(
            call_tool("recognize_sheets", {"images": "not-a-list"})
        )
        data = json.loads(result[0].text)
        assert "error" in data
