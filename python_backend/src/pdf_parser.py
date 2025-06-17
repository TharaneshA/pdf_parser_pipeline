import fitz  # PyMuPDF
import re
import os
import datetime
import logging
import pdfplumber
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('pdf_parser')

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts raw text content from all pages of a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content from all pages
    """
    logger.info(f"Extracting text from PDF: {os.path.basename(pdf_path)}")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at {pdf_path}")
        return ""
    
    try:
        doc = fitz.open(pdf_path)
        text = ""
        page_count = len(doc)
        logger.info(f"PDF has {page_count} pages")
        
        for page_num in range(page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            logger.debug(f"Extracted {len(page_text)} characters from page {page_num + 1}")
        
        doc.close()
        logger.info(f"Completed text extraction: {len(text)} total characters")
        return text
        
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        return ""

def extract_tables_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts tables from a PDF file using pdfplumber with position information.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        List[Dict[str, Any]]: List of extracted tables with page number, position and formatted content
    """
    logger.info(f"Extracting tables from PDF: {os.path.basename(pdf_path)}")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at {pdf_path}")
        return []
    
    tables_with_position = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"Scanning {total_pages} pages for tables")
            
            for page_num, page in enumerate(pdf.pages):
                logger.debug(f"Extracting tables from page {page_num + 1}/{total_pages}")
                page_tables = page.extract_tables()
                
                if page_tables:
                    logger.info(f"Found {len(page_tables)} tables on page {page_num + 1}")
                
                for table_num, table in enumerate(page_tables):
                    if table and len(table) > 0:
                        # Format the table as a string
                        table_str = f"\n--- TABLE START ---\n"
                        
                        # Calculate column widths for better formatting
                        col_widths = [max(len(str(row[i])) if i < len(row) else 0 for row in table) for i in range(max(len(row) for row in table))]
                        
                        # Format each row
                        for row in table:
                            row_str = ""
                            for i, cell in enumerate(row):
                                cell_text = str(cell).strip() if cell else ""
                                row_str += f"{cell_text:{col_widths[i] + 2}}"
                            table_str += row_str + "\n"
                        
                        table_str += "--- TABLE END ---\n"
                        
                        # Get table position on page
                        # Note: pdfplumber tables have bbox attribute (x0, top, x1, bottom)
                        table_bbox = None
                        if hasattr(page, 'find_tables') and callable(page.find_tables):
                            tables_info = page.find_tables()
                            if table_num < len(tables_info):
                                table_bbox = tables_info[table_num].bbox
                                logger.debug(f"Table {table_num + 1} position: {table_bbox}")
                        
                        tables_with_position.append({
                            "page_num": page_num + 1,
                            "table_num": table_num + 1,
                            "content": table_str,
                            "position": table_bbox  # This will be None if position can't be determined
                        })
                        
                        logger.debug(f"Extracted table {table_num + 1} from page {page_num + 1} with {len(table)} rows")
        
        logger.info(f"Completed table extraction: {len(tables_with_position)} tables found")
        return tables_with_position
        
    except Exception as e:
        logger.error(f"Error extracting tables from PDF {pdf_path}: {str(e)}")
        return []

def clean_extracted_text(text: str) -> str:
    """
    Customize this heavily based on your PDF structure!
    
    Args:
        text (str): Raw extracted text
        
    Returns:
        str: Cleaned text with preserved table formatting
    """
    logger.info(f"Cleaning extracted text ({len(text)} characters)")
    
    # Split the text by table markers to preserve table formatting
    table_pattern = r'(--- TABLE START ---[\s\S]*?--- TABLE END ---)'  
    parts = re.split(table_pattern, text)
    
    logger.info(f"Text split into {len(parts)} parts for cleaning")
    table_count = sum(1 for i, part in enumerate(parts) if i % 2 == 1 and re.match(table_pattern, part))
    logger.info(f"Found {table_count} table sections to preserve")
    
    cleaned_parts = []
    for i, part in enumerate(parts):
        # Check if this part is a table (matches our table marker pattern)
        if i % 2 == 1 and re.match(table_pattern, part):
            # This is a table section - preserve it exactly as is
            logger.debug(f"Preserving table section {(i+1)//2} ({len(part)} characters)")
            cleaned_parts.append(part)
        else:
            # This is regular text - apply cleaning
            original_length = len(part)
            
            # Remove excessive newlines (more than 2 consecutive)
            cleaned_part = re.sub(r'\n{3,}', '\n\n', part)
            
            # Remove leading/trailing whitespace from each line while preserving indentation
            # Use rstrip instead of strip to preserve leading spaces for formatting
            cleaned_part = "\n".join([line.rstrip() for line in cleaned_part.split('\n')])
            
            # Remove extra spaces within lines (but preserve indentation)
            cleaned_part = re.sub(r'([^ ])  +', r'\1 ', cleaned_part)
            
            # Remove page markers
            cleaned_part = re.sub(r'--- Page \d+ ---', '', cleaned_part)
            
            # Remove common PDF artifacts
            cleaned_part = re.sub(r'\f', '', cleaned_part)  # Form feed characters
            cleaned_part = re.sub(r'\x0c', '', cleaned_part)  # Page break characters
            
            # Remove empty lines but preserve paragraph breaks
            cleaned_part = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_part)
            
            new_length = len(cleaned_part)
            reduction = original_length - new_length
            logger.debug(f"Cleaned text part {(i+1)//2}: {reduction} characters removed ({reduction/original_length*100:.1f}% reduction)")
            
            cleaned_parts.append(cleaned_part)
    
    # Join all parts back together
    result = ''.join(cleaned_parts)
    final_result = result.strip()
    
    logger.info(f"Text cleaning complete: {len(text) - len(final_result)} characters removed ({(len(text) - len(final_result))/len(text)*100:.1f}% reduction)")
    return final_result

def identify_key_sections(text: str) -> Dict[str, str]:
    """
    Tries to identify key sections in the text based on common report patterns.
    This is highly dependent on report structure.
    
    Args:
        text (str): Cleaned text content
        
    Returns:
        Dict[str, str]: Dictionary with section names as keys and content as values
    """
    sections = {}
    
    # Common section patterns for factory/operations reports
    section_patterns = {
        "executive_summary": r"(?:executive summary|summary|overview)\s*:?\s*\n(.*?)(?=\n\n[A-Z][^\n]*:?\s*\n|$)",
        "daily_output": r"(?:daily output|production|output)\s*:?\s*\n(.*?)(?=\n\n[A-Z][^\n]*:?\s*\n|$)",
        "anomalies": r"(?:anomalies|issues|problems|alerts)\s*:?\s*\n(.*?)(?=\n\n[A-Z][^\n]*:?\s*\n|$)",
        "events": r"(?:events|incidents|activities)\s*:?\s*\n(.*?)(?=\n\n[A-Z][^\n]*:?\s*\n|$)",
        "recommendations": r"(?:recommendations|actions|next steps)\s*:?\s*\n(.*?)(?=\n\n[A-Z][^\n]*:?\s*\n|$)",
        "metrics": r"(?:metrics|kpis?|performance|statistics)\s*:?\s*\n(.*?)(?=\n\n[A-Z][^\n]*:?\s*\n|$)"
    }
    
    for section_name, pattern in section_patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            sections[section_name] = match.group(1).strip()
    
    # If no specific sections found, return the full text
    if not sections:
        sections["full_report"] = text
    
    return sections

def extract_numerical_data(text: str) -> List[Dict[str, str]]:
    """
    Extracts numerical data and metrics from the text.
    
    Args:
        text (str): Text content to analyze
        
    Returns:
        List[Dict[str, str]]: List of extracted numerical data with context
    """
    numerical_data = []
    
    # Pattern to find numbers with units or context
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(units?|pieces?|items?|kg|tons?|hours?|minutes?|%|percent)',
        r'(\d+(?:\.\d+)?)\s*(efficiency|productivity|output|production)',
        r'(temperature|pressure|speed|rate)\s*:?\s*(\d+(?:\.\d+)?)\s*(°[CF]|psi|rpm|%)?'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            numerical_data.append({
                "value": match.group(1) if len(match.groups()) >= 1 else match.group(0),
                "unit": match.group(2) if len(match.groups()) >= 2 else "",
                "context": match.group(0),
                "position": match.start()
            })
    
    return numerical_data

def merge_tables_with_text(text: str, tables: List[Dict[str, Any]]) -> str:
    """
    Merges tables with text content at appropriate positions based on page markers.
    
    Args:
        text (str): Raw text content with page markers
        tables (List[Dict[str, Any]]): List of tables with page numbers
        
    Returns:
        str: Text with tables integrated at appropriate positions
    """
    logger.info(f"Merging {len(tables)} tables with text content")
    
    # Group tables by page
    tables_by_page = {}
    for table in tables:
        page_num = table["page_num"]
        if page_num not in tables_by_page:
            tables_by_page[page_num] = []
        tables_by_page[page_num].append(table)
    
    logger.info(f"Tables grouped by page: {len(tables_by_page)} pages have tables")
    for page, page_tables in tables_by_page.items():
        logger.debug(f"Page {page}: {len(page_tables)} tables")
    
    # Split text by page markers
    page_pattern = r'--- Page \d+ ---'
    page_markers = re.finditer(page_pattern, text)
    page_positions = [(m.start(), m.group()) for m in page_markers]
    
    if not page_positions:
        # No page markers found, return original text
        logger.warning("No page markers found in text, returning original text")
        return text
    
    logger.info(f"Found {len(page_positions)} page markers in text")
    
    # Add end position
    page_positions.append((len(text), ""))
    
    # Build new text with tables inserted
    result_text = text[:page_positions[0][0]]
    tables_inserted = 0
    
    for i in range(len(page_positions) - 1):
        current_marker = page_positions[i][1]
        current_pos = page_positions[i][0]
        next_pos = page_positions[i+1][0]
        
        # Extract page number from marker
        page_match = re.search(r'\d+', current_marker)
        if not page_match:
            logger.warning(f"Could not extract page number from marker: {current_marker}")
            continue
            
        page_num = int(page_match.group())
        page_content = text[current_pos:next_pos]
        
        logger.debug(f"Processing page {page_num} content ({len(page_content)} characters)")
        
        # Add page marker
        result_text += current_marker
        
        # Add page content with tables
        if page_num in tables_by_page:
            # For simplicity, add tables at the end of the page content
            # A more sophisticated approach would use table positions to insert at exact locations
            page_text = page_content[len(current_marker):]
            for table in tables_by_page[page_num]:
                page_text += table["content"]
                tables_inserted += 1
                logger.debug(f"Inserted table {table['table_num']} into page {page_num}")
            result_text += page_text
        else:
            result_text += page_content[len(current_marker):]
    
    logger.info(f"Merged {tables_inserted} tables into text, resulting in {len(result_text)} characters")
    return result_text

def save_processed_text(text: str, pdf_path: str, text_type: str) -> str:
    """
    Save processed text to a plaintext file for debugging purposes.
    
    Args:
        text (str): The text to save
        pdf_path (str): Original PDF path
        text_type (str): Type of text (raw, merged, cleaned)
        
    Returns:
        str: Path to the saved file
    """
    logger.info(f"Saving {text_type} text for {os.path.basename(pdf_path)}")
    
    # Create the output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                             "data", "processed_plaintext")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a filename based on the original PDF name
    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{base_filename}_{text_type}_{timestamp}.txt"
    output_path = os.path.join(output_dir, output_filename)
    
    logger.debug(f"Writing {len(text)} characters to {output_path}")
    
    # Save the text
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"Saved {text_type} text to {output_path}")
    return output_path

def process_pdf_report(pdf_path: str) -> Dict[str, Any]:
    """
    Complete pipeline to process a PDF report.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        Dict[str, Any]: Processed report data
    """
    logger.info(f"Starting PDF processing pipeline for: {os.path.basename(pdf_path)}")
    start_time = datetime.datetime.now()
    
    # Extract text
    logger.info("Step 1: Extracting text")
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text:
        logger.error("Failed to extract text from PDF")
        return {"error": "Failed to extract text from PDF"}
    
    # Save raw text for debugging
    logger.info("Step 2: Saving raw text for debugging")
    save_processed_text(raw_text, pdf_path, "raw")
    
    # Extract tables with position information
    logger.info("Step 3: Extracting tables")
    tables = extract_tables_from_pdf(pdf_path)
    
    # Merge tables with text at appropriate positions
    logger.info("Step 4: Merging tables with text")
    merged_text = merge_tables_with_text(raw_text, tables)
    
    # Save merged text for debugging
    logger.info("Step 5: Saving merged text for debugging")
    save_processed_text(merged_text, pdf_path, "merged")
    
    # Clean text (after merging tables)
    logger.info("Step 6: Cleaning text")
    cleaned_text = clean_extracted_text(merged_text)
    
    # Save cleaned text for debugging
    logger.info("Step 7: Saving cleaned text for debugging")
    save_processed_text(cleaned_text, pdf_path, "cleaned")
    
    # Identify sections
    logger.info("Step 8: Identifying key sections")
    sections = identify_key_sections(cleaned_text)
    
    # Extract numerical data
    logger.info("Step 9: Extracting numerical data")
    numerical_data = extract_numerical_data(cleaned_text)
    
    # Try to extract title from the text
    logger.info("Step 10: Extracting title")
    title = "Unknown Report"
    title_match = re.search(r'^([^\n]+)', cleaned_text)
    if title_match:
        title = title_match.group(1).strip()
        logger.info(f"Extracted title: {title}")
    else:
        logger.warning("Could not extract title, using default")
    
    # Prepare result
    logger.info("Step 11: Preparing result dictionary")
    result = {
        "filename": os.path.basename(pdf_path),
        "title": title,
        "raw_text_length": len(raw_text),
        "cleaned_text_length": len(cleaned_text),
        "sections": sections,
        "numerical_data": numerical_data,
        "tables_count": len(tables),
        "full_text": cleaned_text
    }
    
    end_time = datetime.datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    logger.info(f"PDF processing completed in {processing_time:.2f} seconds")
    logger.info(f"Extracted {len(sections)} sections, {len(numerical_data)} numerical data points, and {len(tables)} tables")
    
    return result

if __name__ == "__main__":
    # Test the parser with a sample PDF
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        result = process_pdf_report(pdf_path)
        print("\nProcessing Result:")
        print(f"Sections found: {list(result.get('sections', {}).keys())}")
        print(f"Numerical data points: {len(result.get('numerical_data', []))}")
        print(f"Tables extracted: {result.get('tables_count', 0)}")
    else:
        print("Usage: python pdf_parser.py <path_to_pdf>")
        print("Or import this module to use its functions.")