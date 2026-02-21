import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

RENDER_OUTPUT_DIR = "/tmp/render-mcp"

VALID_IMAGE_FORMATS = ("png", "svg")
DPI_MIN = 72
DPI_MAX = 600
DPI_DEFAULT = 150
PAGE_DEFAULT = 1


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


def validate_image_format(fmt: str) -> tuple[bool, str]:
    """Validate an image format string.

    Returns:
        (True, "") if valid, (False, error_message) if invalid.
    """
    if fmt not in VALID_IMAGE_FORMATS:
        return False, (
            f"Unsupported image format {fmt!r}. "
            f"Valid formats: {', '.join(VALID_IMAGE_FORMATS)}"
        )
    return True, ""


def validate_dpi(dpi: int) -> tuple[bool, str]:
    """Validate DPI value (must be in range DPI_MIN–DPI_MAX).

    Returns:
        (True, "") if valid, (False, error_message) if invalid.
    """
    if not isinstance(dpi, int):
        return False, f"dpi must be an integer, got {type(dpi).__name__}"
    if dpi < DPI_MIN or dpi > DPI_MAX:
        return False, (
            f"dpi must be between {DPI_MIN} and {DPI_MAX}, got {dpi}"
        )
    return True, ""


def validate_page(page: int) -> tuple[bool, str]:
    """Validate a page number (must be a positive integer).

    Returns:
        (True, "") if valid, (False, error_message) if invalid.
    """
    if not isinstance(page, int):
        return False, f"page must be an integer, got {type(page).__name__}"
    if page < 1:
        return False, f"page must be at least 1, got {page}"
    return True, ""


def generate_pdf_path(output_path: str | None) -> str:
    """Return output_path if provided, otherwise generate one in RENDER_OUTPUT_DIR."""
    if output_path:
        return output_path
    output_dir = Path(RENDER_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(output_dir / f"score_{timestamp}.pdf")


def generate_image_path(output_path: str | None, fmt: str) -> str:
    """Return output_path if provided, otherwise generate one in RENDER_OUTPUT_DIR."""
    if output_path:
        return output_path
    output_dir = Path(RENDER_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(output_dir / f"score_{timestamp}.{fmt}")
