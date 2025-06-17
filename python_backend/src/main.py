import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the parent directory to sys.path to allow imports from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pdf_parser import process_pdf_report
from src.gemini_summarizer import GeminiSummarizer
from src.utils import (
    find_pdf_files, 
    ensure_directory_exists, 
    generate_output_filename,
    print_processing_stats,
    ProgressTracker
)

# Define paths
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DIR = BASE_DIR / "data" / "input_pdfs"
OUTPUT_DIR = BASE_DIR / "data" / "output_summaries"

def process_single_pdf(pdf_path: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Process a single PDF file and generate a summary.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str): Directory to save the summary
        
    Returns:
        Dict[str, Any]: Processing result
    """
    if output_dir is None:
        output_dir = str(OUTPUT_DIR)
    
    ensure_directory_exists(output_dir)
    
    try:
        # Extract text and structure from PDF
        print(f"\nProcessing PDF: {pdf_path}")
        report_data = process_pdf_report(pdf_path)
        
        if "error" in report_data:
            print(f"Error processing PDF: {report_data['error']}")
            return {"success": False, "error": report_data["error"]}
        
        # Generate summary using Gemini
        print("Generating summary using Gemini...")
        summarizer = GeminiSummarizer()
        summary = summarizer.summarize_report(report_data)
        
        # Save summary to file
        output_filename = generate_output_filename(os.path.basename(pdf_path))
        output_path = os.path.join(output_dir, output_filename)
        
        summarizer.save_summary(summary, output_path)
        
        return {
            "success": True,
            "source_file": os.path.basename(pdf_path),
            "output_file": output_filename,
            "output_path": output_path,
            "sections_found": list(report_data.get("sections", {}).keys()),
            "numerical_data_points": len(report_data.get("numerical_data", [])),
            "tokens_used": summary.get("metadata", {}).get("response_tokens", 0)
        }
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return {"success": False, "error": str(e)}

def batch_process_directory(input_dir: str = None, output_dir: str = None) -> Dict[str, Any]:
    """
    Process all PDF files in a directory.
    
    Args:
        input_dir (str): Directory containing PDF files
        output_dir (str): Directory to save summaries
        
    Returns:
        Dict[str, Any]: Processing statistics
    """
    if input_dir is None:
        input_dir = str(INPUT_DIR)
    
    if output_dir is None:
        output_dir = str(OUTPUT_DIR)
    
    ensure_directory_exists(input_dir)
    ensure_directory_exists(output_dir)
    
    # Find all PDF files
    pdf_files = find_pdf_files(input_dir)
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return {"success": False, "error": "No PDF files found"}
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF
    results = []
    success_count = 0
    error_count = 0
    total_tokens = 0
    
    progress = ProgressTracker(len(pdf_files), "Processing PDFs")
    
    for pdf_file in pdf_files:
        result = process_single_pdf(pdf_file, output_dir)
        results.append(result)
        
        if result.get("success", False):
            success_count += 1
            total_tokens += result.get("tokens_used", 0)
        else:
            error_count += 1
        
        progress.update()
    
    # Compile statistics
    stats = {
        "total_files": len(pdf_files),
        "success_count": success_count,
        "error_count": error_count,
        "success_rate": f"{(success_count / len(pdf_files) * 100):.1f}%" if pdf_files else "N/A",
        "total_tokens_used": total_tokens,
        "output_directory": output_dir
    }
    
    print_processing_stats(stats)
    return {"success": True, "stats": stats, "results": results}

def main():
    """
    Main entry point for the application.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Satori XR Report Summarizer")
    parser.add_argument("--input", "-i", help="Input PDF file or directory")
    parser.add_argument("--output", "-o", help="Output directory for summaries")
    parser.add_argument("--batch", "-b", action="store_true", help="Process all PDFs in input directory")
    
    args = parser.parse_args()
    
    if args.batch or (args.input and os.path.isdir(args.input)):
        # Batch processing mode
        input_dir = args.input if args.input else str(INPUT_DIR)
        output_dir = args.output if args.output else str(OUTPUT_DIR)
        
        print(f"Batch processing PDFs from {input_dir}")
        batch_process_directory(input_dir, output_dir)
        
    elif args.input and os.path.isfile(args.input):
        # Single file processing mode
        output_dir = args.output if args.output else str(OUTPUT_DIR)
        
        print(f"Processing single PDF: {args.input}")
        result = process_single_pdf(args.input, output_dir)
        
        if result.get("success", False):
            print(f"\nSummary saved to: {result['output_path']}")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
    
    else:
        # No valid input provided
        print("No input specified. Use --input to specify a PDF file or directory.")
        print("Use --batch to process all PDFs in the input directory.")
        print("\nExample usage:")
        print("  python main.py --input report.pdf")
        print("  python main.py --batch --input ./pdf_reports")

if __name__ == "__main__":
    main()