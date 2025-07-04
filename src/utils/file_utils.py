
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def find_pdfs_in_directory(directory_path: Path) -> list[Path]:
    """
    Recursively finds all PDF files within a given directory.

    Args:
        directory_path: The path to the directory to search.

    Returns:
        A list of Path objects for each found PDF file.
    """
    if not directory_path.is_dir():
        logger.error(f"Provided path is not a directory: {directory_path}")
        return []
    
    logger.info(f"Searching for PDF files in '{directory_path}'...")
    pdf_files = list(directory_path.rglob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF file(s).")
    return pdf_files

def save_json_output(data: dict, output_dir: Path, original_filename: str):
    """
    Saves the extracted data dictionary as a JSON file.

    Args:
        data: The dictionary containing the extracted data.
        output_dir: The directory where the JSON file will be saved.
        original_filename: The name of the original PDF file, used for the output filename.
    """
    try:
        # Ensure the output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a clean filename for the output
        output_filename = Path(original_filename).stem + ".json"
        output_path = output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Successfully saved extracted data to '{output_path}'")
    except Exception as e:
        logger.error(f"Failed to save JSON output for {original_filename}. Error: {e}", exc_info=True)