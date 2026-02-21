import mcp.server.stdio
from mcp.server import Server
from mcp.types import Tool, TextContent
import json
import logging

from .omr_engine import recognize_image, recognize_image_to_file, recognize_images
from .utils import decode_base64_image, SUPPORTED_IMAGE_FORMATS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Server("omr-mcp")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="recognize_sheet",
            description="Recognize music notation from an image and return MusicXML",
            inputSchema={
                "type": "object",
                "properties": {
                    "image": {
                        "type": "string",
                        "description": "File path or base64-encoded image data"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["path", "base64"],
                        "description": "Input format hint: 'path' or 'base64' (auto-detected if omitted)"
                    }
                },
                "required": ["image"]
            }
        ),
        Tool(
            name="recognize_sheet_to_file",
            description="Process sheet music image and save MusicXML result to filesystem",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to input image"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path for output MusicXML file (auto-generated if omitted)"
                    }
                },
                "required": ["input_path"]
            }
        ),
        Tool(
            name="recognize_sheets",
            description="Process multiple pages of sheet music in order and return a single merged MusicXML",
            inputSchema={
                "type": "object",
                "properties": {
                    "images": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ordered list of image file paths or base64-encoded images (one per page)"
                    }
                },
                "required": ["images"]
            }
        ),
        Tool(
            name="list_capabilities",
            description="List supported formats and available tools for this OMR server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_supported_formats",
            description="(Deprecated — use list_capabilities) List supported input and output formats",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]

def _detect_input_format(image: str, format_hint: str | None) -> str:
    """Detect if input is a file path or base64 data."""
    if format_hint:
        return format_hint
    # Base64 data typically starts with data: or is very long without path separators
    if image.startswith("data:") or (len(image) > 500 and "/" not in image and "\\" not in image):
        return "base64"
    return "path"

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "recognize_sheet":
        image = arguments["image"]
        format_hint = arguments.get("format")
        input_format = _detect_input_format(image, format_hint)
        
        logger.info(f"Processing sheet music recognition (format: {input_format})")
        
        try:
            if input_format == "base64":
                # Decode base64 to temporary file
                success, path_or_error = decode_base64_image(image)
                if not success:
                    return [TextContent(type="text", text=json.dumps({"error": path_or_error}))]
                image_path = path_or_error
            else:
                image_path = image
            
            result = recognize_image(image_path)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            error_result = {"error": f"Failed to process image: {str(e)}"}
            return [TextContent(type="text", text=json.dumps(error_result))]
    
    elif name == "recognize_sheet_to_file":
        input_path = arguments["input_path"]
        output_path = arguments.get("output_path")
        
        logger.info(f"Processing sheet music to file: {input_path}")
        
        try:
            result = recognize_image_to_file(input_path, output_path)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            error_result = {"error": f"Failed to process image: {str(e)}"}
            return [TextContent(type="text", text=json.dumps(error_result))]
    
    elif name == "recognize_sheets":
        images = arguments.get("images", [])
        if not isinstance(images, list):
            error_result = {"error": "'images' must be a list", "error_code": "INVALID_PARAMETER"}
            return [TextContent(type="text", text=json.dumps(error_result))]

        logger.info(f"Processing {len(images)} sheet music page(s)")

        # Resolve any base64 inputs to temp files
        resolved_paths = []
        resolution_error = None
        for img in images:
            input_format = _detect_input_format(img, None)
            if input_format == "base64":
                success, path_or_error = decode_base64_image(img)
                if not success:
                    resolution_error = path_or_error
                    break
                resolved_paths.append(path_or_error)
            else:
                resolved_paths.append(img)

        if resolution_error:
            return [TextContent(type="text", text=json.dumps({"error": resolution_error}))]

        try:
            result = recognize_images(resolved_paths)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.error(f"Error processing images: {str(e)}")
            error_result = {"error": f"Failed to process images: {str(e)}", "error_code": "PROCESSING_FAILED"}
            return [TextContent(type="text", text=json.dumps(error_result))]

    elif name in ("list_capabilities", "list_supported_formats"):
        try:
            from importlib.metadata import version as pkg_version
            backend_version = pkg_version("oemer")
        except Exception:
            backend_version = "unknown"

        result = {
            "server": "omr-mcp",
            "version": "0.1.0",
            "input_formats": list(ext.lstrip(".") for ext in SUPPORTED_IMAGE_FORMATS),
            "output_formats": ["musicxml"],
            "tools": [
                "recognize_sheet",
                "recognize_sheet_to_file",
                "recognize_sheets",
                "list_capabilities",
            ],
            "backend": "oemer",
            "backend_version": backend_version,
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    raise ValueError(f"Unknown tool: {name}")

def main():
    """Main entry point for the OMR MCP server."""
    logger.info("Starting OMR MCP Server...")
    import asyncio
    asyncio.run(mcp.server.stdio.run_server(app))

if __name__ == "__main__":
    main()