import asyncio
import json
import logging
import os

import mcp.server.stdio
from mcp.server import Server
from mcp.types import TextContent, Tool

from .engine import ProcessingError, extract_midi, parse_parts, synthesize_midi
from .utils import generate_output_path, validate_musicxml, validate_tempo_factor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Server("synth-mcp")


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_parts",
            description="List all voice parts available in a MusicXML score",
            inputSchema={
                "type": "object",
                "properties": {
                    "musicxml": {
                        "type": "string",
                        "description": "MusicXML document as a string",
                    }
                },
                "required": ["musicxml"],
            },
        ),
        Tool(
            name="synthesize",
            description=(
                "Synthesize audio from a MusicXML score. "
                "Optionally select specific voice parts and adjust the tempo."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "musicxml": {
                        "type": "string",
                        "description": "MusicXML document as a string",
                    },
                    "part_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Part IDs to include (default: all parts)",
                    },
                    "tempo_factor": {
                        "type": "number",
                        "description": (
                            "Tempo multiplier: 1.0 = score tempo, 0.75 = 75% speed. "
                            "Valid range: 0.25–4.0. Default: 1.0"
                        ),
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to write WAV file (auto-generated if omitted)",
                    },
                },
                "required": ["musicxml"],
            },
        ),
        Tool(
            name="list_capabilities",
            description="List supported formats and available tools for this synthesis server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


def _error(message: str, code: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"error": message, "error_code": code}))]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_parts":
        musicxml = arguments.get("musicxml", "")

        ok, err = validate_musicxml(musicxml)
        if not ok:
            return _error(err, "INVALID_INPUT")

        try:
            parts = parse_parts(musicxml)
            return [TextContent(type="text", text=json.dumps({"parts": parts}, indent=2))]
        except ProcessingError as e:
            return _error(str(e), e.error_code)
        except Exception as e:
            logger.error("get_parts unexpected error: %s", e)
            return _error(f"Unexpected error: {e}", "PROCESSING_FAILED")

    elif name == "synthesize":
        musicxml = arguments.get("musicxml", "")
        part_ids = arguments.get("part_ids")  # None → all parts
        tempo_factor = arguments.get("tempo_factor", 1.0)
        output_path = arguments.get("output_path")

        ok, err = validate_musicxml(musicxml)
        if not ok:
            return _error(err, "INVALID_INPUT")

        ok, err = validate_tempo_factor(tempo_factor)
        if not ok:
            return _error(err, "INVALID_PARAMETER")

        if part_ids is not None and not isinstance(part_ids, list):
            return _error("part_ids must be a list of strings", "INVALID_PARAMETER")

        resolved_output = generate_output_path(output_path)

        try:
            midi_bytes = extract_midi(musicxml, part_ids, tempo_factor)
        except ProcessingError as e:
            return _error(str(e), e.error_code)
        except Exception as e:
            logger.error("extract_midi unexpected error: %s", e)
            return _error(f"MIDI extraction failed: {e}", "PROCESSING_FAILED")

        try:
            duration = synthesize_midi(midi_bytes, resolved_output)
        except ProcessingError as e:
            return _error(str(e), e.error_code)
        except Exception as e:
            logger.error("synthesize_midi unexpected error: %s", e)
            return _error(f"Synthesis failed: {e}", "PROCESSING_FAILED")

        # Resolve the list of included part IDs for the response
        if part_ids is not None:
            parts_included = part_ids
        else:
            try:
                parts_included = [p["id"] for p in parse_parts(musicxml)]
            except Exception:
                parts_included = []

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "audio_path": resolved_output,
                        "format": "wav",
                        "duration_seconds": round(duration, 2),
                        "parts_included": parts_included,
                        "tempo_factor": tempo_factor,
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "list_capabilities":
        soundfont_path = os.environ.get("SYNTH_SOUNDFONT_PATH", "")
        soundfont_loaded = bool(soundfont_path) and os.path.exists(soundfont_path)

        fluidsynth_available = True
        try:
            import fluidsynth  # noqa: F401
        except (ImportError, OSError):
            fluidsynth_available = False

        backend_version = "unknown"
        try:
            import subprocess
            r = subprocess.run(
                ["fluidsynth", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # FluidSynth prints e.g. "FluidSynth version 2.3.4\n..."
            first_line = (r.stdout + r.stderr).strip().split("\n")[0]
            backend_version = first_line.replace("FluidSynth version ", "").strip() or "unknown"
        except Exception:
            pass

        result = {
            "server": "synth-mcp",
            "version": "0.1.0",
            "input_formats": ["musicxml"],
            "output_formats": ["wav"],
            "tools": ["get_parts", "synthesize", "list_capabilities"],
            "backend": "fluidsynth",
            "backend_version": backend_version,
            "soundfont_loaded": soundfont_loaded,
            "soundfont_path": soundfont_path if soundfont_loaded else None,
            "fluidsynth_available": fluidsynth_available,
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    raise ValueError(f"Unknown tool: {name}")


def main():
    """Entry point for synth-mcp."""
    soundfont_path = os.environ.get("SYNTH_SOUNDFONT_PATH", "")
    if not soundfont_path:
        logger.warning(
            "SYNTH_SOUNDFONT_PATH is not set — synthesis will fail. "
            "Download an SF2 soundfont and set the variable before calling synthesize."
        )
    elif not os.path.exists(soundfont_path):
        logger.warning("Soundfont not found at %r — synthesis will fail.", soundfont_path)
    else:
        logger.info("Soundfont: %s", soundfont_path)

    try:
        import fluidsynth  # noqa: F401
        logger.info("FluidSynth library available")
    except (ImportError, OSError) as e:
        logger.warning("FluidSynth library not available: %s", e)

    logger.info("Starting synth-mcp server…")

    async def _run():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
