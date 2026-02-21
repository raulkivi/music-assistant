"""
Input validation and shared utilities for musicxml-abc-mcp.

No MCP SDK imports and no business logic here.
"""


def validate_musicxml(musicxml: str) -> tuple[bool, str]:
    """Return (True, '') if the string looks like MusicXML, else (False, reason)."""
    if not musicxml or not musicxml.strip():
        return False, "MusicXML string is empty."
    if "<score-partwise" not in musicxml and "<score-timewise" not in musicxml:
        return False, (
            "Input does not appear to be MusicXML: "
            "no <score-partwise> or <score-timewise> root element found."
        )
    return True, ""


def validate_abc_str(abc: str) -> tuple[bool, str]:
    """Return (True, '') if the string is non-empty, else (False, reason)."""
    if not abc or not abc.strip():
        return False, "ABC string is empty."
    return True, ""
