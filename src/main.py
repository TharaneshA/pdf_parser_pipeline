# src/main.py

import argparse
import logging
from pathlib import Path
import time

from src.parser import parse_pdf_to_markdown
from src.extractor import extract_esg_data
from src.utils.file_utils import find_pdfs_in_directory, save_json_output

# Configure logging for clear, informative console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def process_single_file(pdf_path: Path, output_dir: Path):
    """Orchestrates the full parsing and extraction pipeline for a single PDF file."""
    logger.info(f"--- Starting pipeline for: {pdf_path.name} ---")
    
    # Stage 1: Parse PDF to Markdown
    markdown_content = parse_pdf_to_markdown(pdf_path)
    if not markdown_content:
        logger.error(f"Stopping pipeline for {pdf_path.name} due to parsing failure.")
        return

    # Stage 2: Extract structured data using Gemini
    extracted_data = extract_esg_data(markdown_content)
    if not extracted_data:
        logger.error(f"Stopping pipeline for {pdf_path.name} due to extraction failure.")
        return

    # Stage 3: Save the output
    save_json_output(extracted_data, output_dir, pdf_path.name)
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
        default=Path("./output"),
        help="The directory where JSON output files will be saved. Defaults to './output'."
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