# PDF Parser Pipeline   

An AI-powered backend pipeline for extracting, summarizing, and structuring key information from PDF reports—optimized for integration with visualization tools or downstream applications.

## Overview

The **PDF Parser Pipeline** is designed to process factory and operations reports in PDF format, extract key information, and generate structured summaries using GPT-4. It provides a modular backend system with support for multiple PDF parsing approaches and is built with FastAPI for RESTful access.

This repository contains only the **backend pipeline**. Future visual or XR integrations should be handled in external or downstream projects.

## Features

- **PDF Text Extraction (Main Branch)**: Extracts text using **PyMuPDF** and tables using **pdfplumber**, then combines the outputs.
- **Alternative PDF Processing (Unstructured Branch)**: Uses the [Unstructured](https://github.com/Unstructured-IO/unstructured) library for unified document parsing optimized for LLMs.
- **GPT-4 Summarization**: Generates concise and structured report summaries using OpenAI GPT-4.
- **Key Metrics Identification**: Extracts numerical data and operational KPIs.
- **Structured Output**: Outputs JSON files designed for easy integration with dashboards or analytics tools.
- **REST API with FastAPI**: Serve and manage PDF summarization tasks over HTTP.
- **Batch Mode Support**: Efficiently process multiple PDFs in batch.

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
   git clone https://github.com/TharaneshA/pdf_parser_pipeline.git
   cd pdf_parser_pipeline
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

- Enhanced PDF parsing with hybrid techniques
- Improved table extraction using layout-aware models
- Real-time data ingestion and streaming
- Multi-document comparison and trend summarization
- Integration with external dashboards or BI tools

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Gemini API
- PyMuPDF and pdfplumber for PDF parsing
- Unstructured for document layout extraction (used in the unstructured branch)
- FastAPI for the REST API framework
