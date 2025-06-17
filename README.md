# Satori XR Report Summarizer

An AI-powered tool for extracting, summarizing, and visualizing key information from PDF reports for XR dashboards.

## Overview

The Satori XR Report Summarizer is designed to process factory and operations reports in PDF format, extract key information, and generate structured summaries optimized for visualization in XR (Extended Reality) environments. The system uses GPT-4 to analyze report content and create insightful summaries that can be displayed on XR dashboards.

## Features

- **PDF Text Extraction**: Extract text content from PDF reports using PyMuPDF
- **Intelligent Summarization**: Generate structured summaries using GPT-4
- **Key Metrics Identification**: Automatically identify and extract numerical data and metrics
- **XR-Ready Output**: Produce JSON output optimized for XR visualization
- **API Server**: REST API for integration with XR applications
- **Batch Processing**: Process multiple PDF reports in batch mode

## Project Structure

```
├── python_backend/           # Python backend for PDF processing and summarization
│   ├── data/                 # Data directories
│   │   ├── input_pdfs/       # Place PDF reports here
│   │   └── output_summaries/ # Generated summaries are saved here
│   ├── src/                  # Source code
│   │   ├── __init__.py       # Package initialization
│   │   ├── pdf_parser.py     # PDF text extraction and processing
│   │   ├── gpt_summarizer.py # GPT-4 based summarization
│   │   ├── utils.py          # Utility functions
│   │   ├── main.py           # Command-line interface
│   │   └── api_server.py     # FastAPI server for REST API
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Example environment variables
└── unity_frontend/          # Unity XR frontend (to be implemented)
```

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key for GPT-4 access

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/satori_xr_report_summarizer.git
   cd satori_xr_report_summarizer
   ```

2. Install Python dependencies:
   ```bash
   cd python_backend
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file to add your OpenAI API key
   ```

## Usage

### Command Line Interface

Process a single PDF file:
```bash
python -m src.main --input path/to/report.pdf
```

Process all PDFs in a directory:
```bash
python -m src.main --batch --input path/to/pdf_directory
```

### API Server

Start the API server:
```bash
python -m src.api_server
```

The API will be available at `http://localhost:8000` with the following endpoints:

- `GET /`: Check if API is running
- `POST /process-pdf/`: Upload and process a PDF file
- `GET /task-status/{task_id}`: Check processing status
- `GET /summaries/`: List all available summaries
- `GET /summary/{filename}`: Get a specific summary

## Output Format

The system generates structured JSON summaries with the following format:

```json
{
  "executive_summary": "Brief overview of the report",
  "key_insights": [
    "Insight 1",
    "Insight 2",
    "Insight 3"
  ],
  "daily_output": {
    "total_production": "Number with unit",
    "efficiency_rate": "Percentage",
    "status": "Normal/Warning/Critical"
  },
  "anomalies": [
    {
      "type": "Equipment/Process/Quality",
      "description": "Brief description",
      "severity": "Low/Medium/High",
      "impact": "Brief impact description"
    }
  ],
  "events": [...],
  "recommendations": [...],
  "metrics": {...},
  "dashboard_alerts": [...],
  "metadata": {
    "source_file": "original_file.pdf",
    "processing_timestamp": "2023-05-01T12:34:56",
    "model_used": "gpt-4",
    "tokens_used": 1234
  }
}
```

## Future Development

- Unity XR frontend for immersive data visualization
- Real-time data streaming and updates
- Multi-document comparison and trend analysis
- Custom visualization templates for different report types
- Integration with existing factory management systems

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4
- PyMuPDF for PDF processing
- FastAPI for the REST API framework