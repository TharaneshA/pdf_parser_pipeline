# src/main.py

import argparse
import logging
from pathlib import Path
import time

from src.parser import parse_pdf_to_markdown
from src.extractor import extract_esg_data
# --- IMPORT THE NEW FUNCTION ---
from src.utils.file_utils import find_pdfs_in_directory, save_json_output, save_markdown_output

# Configure logging for clear, informative console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def process_single_file(pdf_path: Path, final_output_dir: Path):
    """Orchestrates the full parsing and extraction pipeline for a single PDF file."""
    logger.info(f"--- Starting pipeline for: {pdf_path.name} ---")
    
    # Stage 1: Parse PDF to Markdown
    markdown_content = parse_pdf_to_markdown(pdf_path)
    if not markdown_content:
        logger.error(f"Stopping pipeline for {pdf_path.name} due to parsing failure.")
        return

    # --- NEW INTERMEDIATE STEP ADDED HERE ---
    # Define the hardcoded path as requested for the intermediate output.
    # Using pathlib.Path is robust for handling Windows paths.
    intermediate_output_dir = Path("C:/project/pdf_parser_pipeline/output")
    logger.info(f"Saving intermediate parsed markdown to specified directory: '{intermediate_output_dir}'")
    save_markdown_output(markdown_content, intermediate_output_dir, pdf_path.name)
    
    # Stage 2: Extract structured data using Gemini
    logger.info("Content saved. Proceeding to send content to Gemini for extraction...")
    extracted_data = extract_esg_data(markdown_content)
    if not extracted_data:
        logger.error(f"Stopping pipeline for {pdf_path.name} due to extraction failure.")
        return

    # Stage 3: Save the final JSON output to the directory specified by the --output argument
    save_json_output(extracted_data, final_output_dir, pdf_path.name)
    logger.info(f"--- Successfully completed pipeline for: {pdf_path.name} ---")


def main():
    """Main function to handle command-line arguments and run the pipeline."""
    parser = argparse.ArgumentParser(description="ESG Report Parsing Pipeline")
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to a single PDF file or a directory containing PDF files."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("./final_json_output"), # Changed default to be more descriptive
        help="The directory where FINAL JSON output files will be saved. Defaults to './final_json_output'."
    )
    parser.add_argument(
        "--batch",
        "-b",
        action="store_true",
        help="Enable batch processing mode. The --input path should be a directory."
    )
    args = parser.parse_args()

    start_time = time.time()
    
    if args.batch:
        logger.info(f"Batch mode enabled. Processing all PDFs in directory: {args.input}")
        pdf_files = find_pdfs_in_directory(args.input)
        if not pdf_files:
            logger.warning("No PDF files found in the specified directory.")
            return
        
        total_files = len(pdf_files)
        for i, pdf_path in enumerate(pdf_files):
            logger.info(f"Processing file {i+1} of {total_files}...")
            process_single_file(pdf_path, args.output)
            
    else:
        if not args.input.is_file() or args.input.suffix.lower() != '.pdf':
            logger.error(f"Single file mode: --input path must be a valid PDF file. Got: {args.input}")
            return
        process_single_file(args.input, args.output)

    end_time = time.time()
    logger.info(f"Total execution time: {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    main()