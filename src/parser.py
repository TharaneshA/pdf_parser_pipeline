from pathlib import Path
from unstructured.partition.pdf import partition_pdf
import logging

logger = logging.getLogger(__name__)

def parse_pdf_to_markdown(file_path: Path) -> str | None:
    """
    Parses a PDF file using the Unstructured library with its high-resolution
    strategy to produce a clean Markdown output suitable for an LLM.

    Args:
        file_path: The path to the PDF file.

    Returns:
        The extracted content formatted as a single Markdown string, or None on failure.
    """
    logger.info(f"Starting PDF parsing for: '{file_path.name}' using 'hi_res' strategy...")
    
    try:
        # Use partition_pdf for intelligent, layout-aware extraction.
        # - strategy="hi_res": Uses advanced models for layout detection.
        # - infer_table_structure=True: Crucial for correctly interpreting tables.
        # - languages=["eng"]: Helps with OCR accuracy if needed.
        elements = partition_pdf(
            filename=str(file_path),
            strategy="hi_res",
            infer_table_structure=True,
            languages=["eng"]
        )

        # Combine the extracted elements into a single markdown string.
        # This simple join is highly effective and preserves document flow.
        markdown_content = "\n\n".join([str(el) for el in elements])
        
        logger.info(f"Successfully parsed '{file_path.name}'. Content length: {len(markdown_content)} characters.")
        return markdown_content
        
    except Exception as e:
        logger.error(f"Fatal error during PDF parsing for '{file_path.name}'. Error: {e}", exc_info=True)
        return None