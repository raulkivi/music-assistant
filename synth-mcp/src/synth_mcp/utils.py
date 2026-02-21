import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

SYNTH_OUTPUT_DIR = "/tmp/synth-mcp"


def validate_musicxml(musicxml_str: str) -> tuple[bool, str]:
    """Validate a MusicXML string.

    Returns:
        (True, "") if valid, (False, error_message) if invalid.
    """
    if not musicxml_str or not musicxml_str.strip():
        return False, "MusicXML string is empty"

    try:
        root = ET.fromstring(musicxml_str)
    except ET.ParseError as e:
        return False, f"Invalid XML: {e}"

    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if tag not in ("score-partwise", "score-timewise"):
        return False, (
            f"Not a MusicXML score: root element is <{tag}>, "
            "expected <score-partwise> or <score-timewise>"
        )

    return True, ""


def validate_tempo_factor(tempo_factor: float) -> tuple[bool, str]:
    """Validate a tempo factor value (must be in range 0.25–4.0).

    Returns:
        (True, "") if valid, (False, error_message) if invalid.
    """
    if not isinstance(tempo_factor, (int, float)):
        return False, f"tempo_factor must be a number, got {type(tempo_factor).__name__}"

    if tempo_factor < 0.25 or tempo_factor > 4.0:
        return False, (
            f"tempo_factor must be between 0.25 and 4.0, got {tempo_factor}. "
            "Values below 1.0 slow the tempo; values above 1.0 speed it up."
        )

    return True, ""


def generate_output_path(output_path: str | None) -> str:
    """Return output_path if provided, otherwise generate one in SYNTH_OUTPUT_DIR."""
    if output_path:
        return output_path

    output_dir = Path(SYNTH_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(output_dir / f"output_{timestamp}.wav")
