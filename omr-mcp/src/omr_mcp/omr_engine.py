import time
import re
import shutil
import xml.etree.ElementTree as ET
from defusedxml.ElementTree import fromstring as _fromstring  # type: ignore[import-untyped]
from pathlib import Path
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Candidate directories where oemer stores downloaded model checkpoints.
_OEMER_CACHE_CANDIDATES = [
    Path.home() / ".oemer",
    Path.home() / ".cache" / "oemer",
]


def health_check() -> dict[str, Any]:
    """Check runtime dependencies and return a human-readable status summary.

    Returns a dict with top-level ``status`` ("ok" or "degraded") and a
    ``checks`` mapping with per-dependency results.  Does not import oemer
    beyond a simple availability probe so it stays fast.
    """
    checks: dict[str, dict[str, Any]] = {}

    # --- oemer availability ---
    try:
        import oemer  # noqa: F401  # type: ignore[import-untyped]
        from importlib.metadata import version as pkg_version
        try:
            oemer_version = pkg_version("oemer")
        except Exception:
            oemer_version = "unknown"
        checks["oemer"] = {"status": "ok", "version": oemer_version}
    except ImportError as exc:
        checks["oemer"] = {
            "status": "missing",
            "error": str(exc),
            "hint": "Run 'uv sync' inside omr-mcp/ to install dependencies.",
        }

    # --- oemer model cache ---
    model_cache_path: Optional[str] = None
    for candidate in _OEMER_CACHE_CANDIDATES:
        if candidate.exists():
            model_cache_path = str(candidate)
            break

    if model_cache_path:
        checks["model_cache"] = {
            "status": "ok",
            "path": model_cache_path,
            "note": "Model cache found — ready to recognise sheet music.",
        }
    else:
        checks["model_cache"] = {
            "status": "missing",
            "path": None,
            "note": (
                "Model cache not found. On first use oemer will download ~100 MB of "
                "model checkpoints (this may take 5–10 minutes). Subsequent runs are fast."
            ),
        }

    overall = "ok" if all(v["status"] == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}


def _extract_musicxml_metadata(musicxml_content: str) -> dict[str, Any]:
    """Extract metadata from MusicXML content."""
    metadata = {}
    
    # Count staves (parts)
    staves_matches = re.findall(r'<part\s+id=', musicxml_content)
    metadata["staves_detected"] = len(staves_matches) if staves_matches else 0
    
    # Count measures (in first part to avoid duplicates)
    measure_matches = re.findall(r'<measure\s+number="(\d+)"', musicxml_content)
    if measure_matches:
        # Get unique measure numbers
        unique_measures = set(int(m) for m in measure_matches)
        metadata["measures"] = max(unique_measures) if unique_measures else 0
    else:
        metadata["measures"] = 0
    
    return metadata


def _run_oemer(image_path: str) -> str:
    """Run oemer on an image and return the output path."""
    from oemer import generate  # type: ignore[import-untyped]
    return generate(image_path)


def recognize_image(image_path: str) -> dict[str, Any]:
    """Process sheet music image and return MusicXML."""
    path = Path(image_path)
    
    # Validate input file
    if not path.exists():
        return {"error": f"File not found: {image_path}"}
    
    if path.suffix.lower() not in [".png", ".jpg", ".jpeg"]:
        return {"error": f"Unsupported format: {path.suffix}. Supported formats: PNG, JPEG"}
    
    start_time = time.time()
    
    try:
        logger.info(f"Starting OMR processing for: {path}")
        
        # Process the image
        logger.info("Running oemer recognition...")
        result_path = _run_oemer(str(path))
        
        # Read the generated MusicXML
        if not Path(result_path).exists():
            return {"error": f"OMR processing completed but output file not found: {result_path}"}
        
        with open(result_path, "r", encoding="utf-8") as f:
            musicxml_content = f.read()
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Extract metadata from MusicXML
        xml_metadata = _extract_musicxml_metadata(musicxml_content)
        
        logger.info(f"OMR processing completed successfully in {processing_time_ms}ms")
        
        return {
            "musicxml": musicxml_content,
            "metadata": {
                "source": str(path),
                "staves_detected": xml_metadata["staves_detected"],
                "measures": xml_metadata["measures"],
                "processing_time_ms": processing_time_ms,
                "engine": "oemer"
            }
        }
        
    except ImportError as e:
        return {
            "error": f"oemer library not available: {str(e)}. Please install with: pip install oemer"
        }
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"OMR processing failed after {processing_time_ms}ms: {str(e)}")
        return {
            "error": f"OMR processing failed: {str(e)}",
            "metadata": {
                "source": str(path),
                "processing_time_ms": processing_time_ms,
                "engine": "oemer"
            }
        }


def _merge_musicxml_pages(musicxml_pages: list[str]) -> str:
    """Merge per-page MusicXML documents into a single score.

    Appends the measures from each successive page into the matching parts of
    the first page's document (matched by index). Measure numbers are
    renumbered to continue sequentially across pages.
    """
    if len(musicxml_pages) == 1:
        return musicxml_pages[0]

    trees = [_fromstring(page) for page in musicxml_pages]
    base = trees[0]
    base_parts = list(base.findall("part"))

    for page_tree in trees[1:]:
        page_parts = list(page_tree.findall("part"))
        for i, page_part in enumerate(page_parts):
            if i >= len(base_parts):
                break  # extra parts on this page — skip
            base_part = base_parts[i]
            existing = base_part.findall("measure")
            last_num = max((int(m.get("number", 0)) for m in existing), default=0)
            for measure in page_part.findall("measure"):
                old_num = int(measure.get("number", 0))
                measure.set("number", str(last_num + old_num))
                base_part.append(measure)

    return ET.tostring(base, encoding="unicode")


def recognize_images(image_paths: list[str]) -> dict[str, Any]:
    """Process multiple sheet music images in page order and return merged MusicXML.

    Args:
        image_paths: Ordered list of image file paths (or base64 strings).

    Returns:
        dict with 'musicxml' and 'metadata' (including 'page_count'), or 'error'.
    """
    if not image_paths:
        return {"error": "No images provided", "error_code": "INVALID_PARAMETER"}

    page_results = []
    errors = []

    for i, path in enumerate(image_paths):
        result = recognize_image(path)
        if "error" in result:
            errors.append(f"Page {i + 1} ({path}): {result['error']}")
        else:
            page_results.append(result)

    if errors:
        return {
            "error": f"Failed to process {len(errors)} page(s): {'; '.join(errors)}",
            "error_code": "PROCESSING_FAILED",
        }

    if len(page_results) == 1:
        result = page_results[0]
        result["metadata"]["page_count"] = 1
        return result

    merged_xml = _merge_musicxml_pages([r["musicxml"] for r in page_results])
    xml_meta = _extract_musicxml_metadata(merged_xml)
    total_time = sum(r["metadata"]["processing_time_ms"] for r in page_results)

    return {
        "musicxml": merged_xml,
        "metadata": {
            "page_count": len(page_results),
            "staves_detected": xml_meta["staves_detected"],
            "measures": xml_meta["measures"],
            "processing_time_ms": total_time,
            "engine": "oemer",
        },
    }


def recognize_image_to_file(input_path: str, output_path: Optional[str] = None) -> dict[str, Any]:
    """Process sheet music image and save MusicXML to file."""
    path = Path(input_path)
    
    # Validate input file
    if not path.exists():
        return {"error": f"File not found: {input_path}"}
    
    if path.suffix.lower() not in [".png", ".jpg", ".jpeg"]:
        return {"error": f"Unsupported format: {path.suffix}. Supported formats: PNG, JPEG"}
    
    # Determine output path
    if output_path is None:
        output_path = str(path.with_suffix(".musicxml"))
    
    start_time = time.time()
    
    try:
        logger.info(f"Starting OMR processing for: {path}")
        
        # Process the image
        logger.info("Running oemer recognition...")
        result_path = _run_oemer(str(path))
        
        # Read and copy/move to desired output path
        if not Path(result_path).exists():
            return {"error": f"OMR processing completed but output file not found: {result_path}"}
        
        # Copy to output path if different
        if str(Path(result_path).resolve()) != str(Path(output_path).resolve()):
            shutil.copy2(result_path, output_path)
        
        # Read content for metadata extraction
        with open(output_path, "r", encoding="utf-8") as f:
            musicxml_content = f.read()
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Extract metadata from MusicXML
        xml_metadata = _extract_musicxml_metadata(musicxml_content)
        
        logger.info(f"OMR processing completed successfully in {processing_time_ms}ms")
        
        return {
            "output_path": output_path,
            "metadata": {
                "source": str(path),
                "staves_detected": xml_metadata["staves_detected"],
                "measures": xml_metadata["measures"],
                "processing_time_ms": processing_time_ms,
                "engine": "oemer"
            }
        }
        
    except ImportError as e:
        return {
            "error": f"oemer library not available: {str(e)}. Please install with: pip install oemer"
        }
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"OMR processing failed after {processing_time_ms}ms: {str(e)}")
        return {
            "error": f"OMR processing failed: {str(e)}",
            "metadata": {
                "source": str(path),
                "processing_time_ms": processing_time_ms,
                "engine": "oemer"
            }
        }