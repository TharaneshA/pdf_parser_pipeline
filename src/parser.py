from pathlib import Path
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Table
import logging
from pathlib import Path
import html2text

logger = logging.getLogger(__name__)

def parse_pdf_to_markdown(file_path: Path) -> str | None:
    """
    Parses a PDF file using the Unstructured library with a text-based strategy
    to produce a clean Markdown output suitable for an LLM, focusing on text and tables.

    Args:
        file_path: The path to the PDF file.

    Returns:
        The extracted content formatted as a single Markdown string, or None on failure.
    """
    logger.info(f"Starting PDF parsing for: '{file_path.name}' using 'fast' strategy for table formatting...")
    
    try:
        # Use partition_pdf for intelligent, layout-aware extraction.
        # - strategy="hi_res": Uses advanced models for layout detection, including tables.
        # - infer_table_structure=True: Crucial for correctly interpreting tables.
        elements = partition_pdf(
            filename=str(file_path),
            strategy="fast",
            infer_table_structure=True
        )

        # Combine the extracted elements into a single markdown string, formatting tables.
        h = html2text.HTML2Text()
        h.body_width = 0  # Disable line wrapping
        
        markdown_parts = []
        for el in elements:
            if isinstance(el, Table):
                # For tables, use the HTML representation and convert it to Markdown
                if el.metadata.text_as_html:
                    markdown_parts.append(h.handle(el.metadata.text_as_html))
                else:
                    markdown_parts.append(el.text) # Fallback to text if HTML is not available
            else:
                markdown_parts.append(el.text)
        
        markdown_content = "\n\n".join(markdown_parts)
        
        logger.info(f"Successfully parsed '{file_path.name}'. Content length: {len(markdown_content)} characters.")
        return markdown_content
        
    except Exception as e:
        logger.error(f"Fatal error during PDF parsing for '{file_path.name}'. Error: {e}", exc_info=True)
        return None