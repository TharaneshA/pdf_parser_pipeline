import fitz  # PyMuPDF
import re
import os
import pdfplumber
from typing import Dict, List, Optional, Any, Tuple

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts raw text content from all pages of a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content from all pages
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return ""
    
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        doc.close()
        return text
        
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return ""

def extract_tables_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts tables from a PDF file using pdfplumber with position information.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        List[Dict[str, Any]]: List of extracted tables with page number, position and formatted content
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return []
    
    tables_with_position = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                
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
                        
                        tables_with_position.append({
                            "page_num": page_num + 1,
                            "table_num": table_num + 1,
                            "content": table_str,
                            "position": table_bbox  # This will be None if position can't be determined
                        })
        
        return tables_with_position
        
    except Exception as e:
        print(f"Error extracting tables from PDF {pdf_path}: {e}")
        return []

def clean_extracted_text(text: str) -> str:
    """
    Performs basic cleaning of the extracted text.
    Customize this heavily based on your PDF structure!
    
    Args:
        text (str): Raw extracted text
        
    Returns:
        str: Cleaned text
    """
    # Remove excessive newlines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace from each line
    text = "\n".join([line.strip() for line in text.split('\n')])
    
    # Remove extra spaces within lines
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove page markers
    text = re.sub(r'--- Page \d+ ---', '', text)
    
    # Remove common PDF artifacts
    text = re.sub(r'\f', '', text)  # Form feed characters
    text = re.sub(r'\x0c', '', text)  # Page break characters
    
    # Remove empty lines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

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
    # Group tables by page
    tables_by_page = {}
    for table in tables:
        page_num = table["page_num"]
        if page_num not in tables_by_page:
            tables_by_page[page_num] = []
        tables_by_page[page_num].append(table)
    
    # Split text by page markers
    page_pattern = r'--- Page \d+ ---'
    page_markers = re.finditer(page_pattern, text)
    page_positions = [(m.start(), m.group()) for m in page_markers]
    
    if not page_positions:
        # No page markers found, return original text
        return text
    
    # Add end position
    page_positions.append((len(text), ""))
    
    # Build new text with tables inserted
    result_text = text[:page_positions[0][0]]
    
    for i in range(len(page_positions) - 1):
        current_marker = page_positions[i][1]
        current_pos = page_positions[i][0]
        next_pos = page_positions[i+1][0]
        
        # Extract page number from marker
        page_match = re.search(r'\d+', current_marker)
        if not page_match:
            continue
            
        page_num = int(page_match.group())
        page_content = text[current_pos:next_pos]
        
        # Add page marker
        result_text += current_marker
        
        # Add page content with tables
        if page_num in tables_by_page:
            # For simplicity, add tables at the end of the page content
            # A more sophisticated approach would use table positions to insert at exact locations
            page_text = page_content[len(current_marker):]
            for table in tables_by_page[page_num]:
                page_text += table["content"]
            result_text += page_text
        else:
            result_text += page_content[len(current_marker):]
    
    return result_text

def process_pdf_report(pdf_path: str) -> Dict[str, Any]:
    """
    Complete pipeline to process a PDF report.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        Dict[str, Any]: Processed report data
    """
    print(f"Processing PDF: {pdf_path}")
    
    # Extract text
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text:
        return {"error": "Failed to extract text from PDF"}
    
    # Extract tables with position information
    tables = extract_tables_from_pdf(pdf_path)
    
    # Merge tables with text at appropriate positions
    merged_text = merge_tables_with_text(raw_text, tables)
    
    # Clean text (after merging tables)
    cleaned_text = clean_extracted_text(merged_text)
    
    # Identify sections
    sections = identify_key_sections(cleaned_text)
    
    # Extract numerical data
    numerical_data = extract_numerical_data(cleaned_text)
    
    # Try to extract title from the text
    title = "Unknown Report"
    title_match = re.search(r'^([^\n]+)', cleaned_text)
    if title_match:
        title = title_match.group(1).strip()
    
    # Prepare result
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
    
    print(f"Extracted {len(sections)} sections, {len(numerical_data)} numerical data points, and {len(tables)} tables")
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