import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensures that a directory exists, creating it if necessary.
    
    Args:
        directory_path (str): Path to the directory
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False

def get_file_hash(file_path: str) -> Optional[str]:
    """
    Generates MD5 hash of a file for change detection.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        Optional[str]: MD5 hash of the file, None if error
    """
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error generating hash for {file_path}: {e}")
        return None

def validate_pdf_file(file_path: str) -> bool:
    """
    Validates if a file is a valid PDF.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        bool: True if valid PDF, False otherwise
    """
    if not os.path.exists(file_path):
        return False
    
    if not file_path.lower().endswith('.pdf'):
        return False
    
    try:
        # Check PDF header
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except Exception:
        return False

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Safely loads a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        Optional[Dict[str, Any]]: Loaded JSON data, None if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {e}")
        return None

def save_json_file(data: Dict[str, Any], file_path: str, indent: int = 2) -> bool:
    """
    Safely saves data to a JSON file.
    
    Args:
        data (Dict[str, Any]): Data to save
        file_path (str): Path to save the file
        indent (int): JSON indentation level
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        ensure_directory_exists(os.path.dirname(file_path))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON file {file_path}: {e}")
        return False

def get_timestamp(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """
    Returns current timestamp in specified format.
    
    Args:
        format_str (str): Timestamp format string
        
    Returns:
        str: Formatted timestamp
    """
    return datetime.now().strftime(format_str)

def generate_output_filename(source_pdf: str, suffix: str = "summary") -> str:
    """
    Generates output filename based on source PDF name.
    
    Args:
        source_pdf (str): Source PDF filename
        suffix (str): Suffix to add to the filename
        
    Returns:
        str: Generated output filename
    """
    base_name = Path(source_pdf).stem
    timestamp = get_timestamp()
    return f"{base_name}_{suffix}_{timestamp}.json"

def find_pdf_files(directory: str) -> List[str]:
    """
    Finds all PDF files in a directory.
    
    Args:
        directory (str): Directory to search
        
    Returns:
        List[str]: List of PDF file paths
    """
    pdf_files = []
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return pdf_files
    
    try:
        for file in os.listdir(directory):
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(directory, file)
                if validate_pdf_file(file_path):
                    pdf_files.append(file_path)
                else:
                    print(f"Invalid PDF file skipped: {file}")
    except Exception as e:
        print(f"Error scanning directory {directory}: {e}")
    
    return pdf_files

def validate_summary_structure(summary: Dict[str, Any]) -> bool:
    """
    Validates the structure of a generated summary.
    
    Args:
        summary (Dict[str, Any]): Summary data to validate
        
    Returns:
        bool: True if structure is valid, False otherwise
    """
    required_fields = [
        'executive_summary',
        'key_insights',
        'daily_output',
        'anomalies',
        'events',
        'recommendations',
        'metrics',
        'dashboard_alerts'
    ]
    
    try:
        # Check required top-level fields
        for field in required_fields:
            if field not in summary:
                print(f"Missing required field: {field}")
                return False
        
        # Validate specific field types
        if not isinstance(summary['key_insights'], list):
            print("key_insights must be a list")
            return False
        
        if not isinstance(summary['daily_output'], dict):
            print("daily_output must be a dictionary")
            return False
        
        if not isinstance(summary['anomalies'], list):
            print("anomalies must be a list")
            return False
        
        if not isinstance(summary['events'], list):
            print("events must be a list")
            return False
        
        if not isinstance(summary['recommendations'], list):
            print("recommendations must be a list")
            return False
        
        if not isinstance(summary['metrics'], dict):
            print("metrics must be a dictionary")
            return False
        
        if not isinstance(summary['dashboard_alerts'], list):
            print("dashboard_alerts must be a list")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error validating summary structure: {e}")
        return False

def format_file_size(size_bytes: int) -> str:
    """
    Formats file size in human-readable format.
    
    Args:
        size_bytes (int): File size in bytes
        
    Returns:
        str: Formatted file size
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Gets comprehensive file information.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        Dict[str, Any]: File information
    """
    try:
        stat = os.stat(file_path)
        
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size_bytes": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "hash": get_file_hash(file_path)
        }
    except Exception as e:
        print(f"Error getting file info for {file_path}: {e}")
        return {"error": str(e)}

def create_processing_log(log_data: Dict[str, Any], log_file: str = None) -> bool:
    """
    Creates a processing log entry.
    
    Args:
        log_data (Dict[str, Any]): Log data to save
        log_file (str): Optional log file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    if log_file is None:
        log_file = f"processing_log_{get_timestamp()}.json"
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "data": log_data
    }
    
    return save_json_file(log_entry, log_file)

def print_processing_stats(stats: Dict[str, Any]) -> None:
    """
    Prints processing statistics in a formatted way.
    
    Args:
        stats (Dict[str, Any]): Processing statistics
    """
    print("\n" + "="*50)
    print("PROCESSING STATISTICS")
    print("="*50)
    
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"\n{key.upper().replace('_', ' ')}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key.replace('_', ' ').title()}: {sub_value}")
        else:
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("="*50 + "\n")

class ProgressTracker:
    """
    Simple progress tracker for batch operations.
    """
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1) -> None:
        """
        Updates progress counter.
        
        Args:
            increment (int): Amount to increment
        """
        self.current += increment
        self._print_progress()
    
    def _print_progress(self) -> None:
        """
        Prints current progress.
        """
        if self.total > 0:
            percentage = (self.current / self.total) * 100
            elapsed = datetime.now() - self.start_time
            
            print(f"\r{self.description}: {self.current}/{self.total} ({percentage:.1f}%) - Elapsed: {elapsed}", end="")
            
            if self.current >= self.total:
                print()  # New line when complete

if __name__ == "__main__":
    # Test utility functions
    print("Testing utility functions...")
    
    # Test timestamp generation
    print(f"Current timestamp: {get_timestamp()}")
    
    # Test filename generation
    test_filename = generate_output_filename("sample_report.pdf")
    print(f"Generated filename: {test_filename}")
    
    # Test file size formatting
    print(f"File size formatting: {format_file_size(1536)} (1536 bytes)")
    
    # Test progress tracker
    tracker = ProgressTracker(5, "Testing")
    for i in range(5):
        tracker.update()
        import time
        time.sleep(0.1)
    
    print("Utility functions test completed.")