import fitz  # PyMuPDF
import re
import os
from typing import Dict, List, Optional

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

def process_pdf_report(pdf_path: str) -> Dict[str, any]:
    """
    Complete pipeline to process a PDF report.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        Dict[str, any]: Processed report data
    """
    print(f"Processing PDF: {pdf_path}")
    
    # Extract text
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text:
        return {"error": "Failed to extract text from PDF"}
    
    # Clean text
    cleaned_text = clean_extracted_text(raw_text)
    
    # Identify sections
    sections = identify_key_sections(cleaned_text)
    
    # Extract numerical data
    numerical_data = extract_numerical_data(cleaned_text)
    
    # Prepare result
    result = {
        "source_file": os.path.basename(pdf_path),
        "raw_text_length": len(raw_text),
        "cleaned_text_length": len(cleaned_text),
        "sections": sections,
        "numerical_data": numerical_data,
        "full_text": cleaned_text
    }
    
    print(f"Extracted {len(sections)} sections and {len(numerical_data)} numerical data points")
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
    else:
        print("Usage: python pdf_parser.py <path_to_pdf>")
        print("Or import this module to use its functions.")