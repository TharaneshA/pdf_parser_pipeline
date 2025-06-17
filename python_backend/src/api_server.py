import os
import json
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import shutil

# Import our modules
from src.pdf_parser import process_pdf_report
from src.gemini_summarizer import GeminiSummarizer
from src.utils import ensure_directory_exists, generate_output_filename

# Define paths
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DIR = BASE_DIR / "data" / "input_pdfs"
OUTPUT_DIR = BASE_DIR / "data" / "output_summaries"

# Ensure directories exist
ensure_directory_exists(str(INPUT_DIR))
ensure_directory_exists(str(OUTPUT_DIR))

# Create FastAPI app
app = FastAPI(
    title="Satori XR Report Summarizer API",
    description="API for processing PDF reports and generating summaries for XR visualization using Google Gemini",
    version="1.0.0"
)

# Add CORS middleware to allow requests from the Unity XR application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your Unity app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store background tasks status
background_tasks_status = {}

@app.get("/")
async def root():
    """Root endpoint to check if API is running"""
    return {"status": "online", "message": "Satori XR Report Summarizer API using Google Gemini"}

@app.post("/process-pdf/")
async def process_pdf(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    """Process a PDF file and generate a summary"""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create a unique task ID
    import uuid
    task_id = str(uuid.uuid4())
    
    # Save the uploaded file temporarily
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        # Copy uploaded file to temp file
        shutil.copyfileobj(file.file, temp_file)
        temp_file.close()
        
        # Save a copy to input directory for reference
        pdf_path = os.path.join(str(INPUT_DIR), file.filename)
        shutil.copy(temp_file.name, pdf_path)
        
        # Add task to background processing
        background_tasks_status[task_id] = {
            "status": "processing", 
            "filename": file.filename
        }
        background_tasks.add_task(
            process_pdf_background, 
            task_id, 
            temp_file.name, 
            file.filename
        )
        
        return {
            "task_id": task_id, 
            "status": "processing", 
            "message": "PDF processing started"
        }
        
    except Exception as e:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Check the status of a background processing task"""
    if task_id not in background_tasks_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return background_tasks_status[task_id]

@app.get("/summaries/")
async def list_summaries():
    """List all available summaries"""
    summaries = []
    
    try:
        for file in os.listdir(str(OUTPUT_DIR)):
            if file.endswith(".json"):
                file_path = os.path.join(str(OUTPUT_DIR), file)
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        # Just read the metadata to avoid loading large files
                        data = json.load(f)
                        summary_info = {
                            "filename": file,
                            "source_file": data.get("metadata", {}).get("source_file", "Unknown"),
                            "timestamp": data.get("metadata", {}).get("processing_timestamp", "Unknown"),
                            "model_used": data.get("metadata", {}).get("model_used", "Unknown"),
                            "file_path": file_path
                        }
                        summaries.append(summary_info)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing summaries: {str(e)}")
    
    return {"summaries": summaries}

@app.get("/summary/{filename}")
async def get_summary(filename: str):
    """Get a specific summary by filename"""
    file_path = os.path.join(str(OUTPUT_DIR), filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Summary not found")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading summary: {str(e)}")

async def process_pdf_background(task_id: str, temp_file_path: str, original_filename: str):
    """Background task to process a PDF file"""
    try:
        # Process the PDF
        report_data = process_pdf_report(temp_file_path)
        
        if "error" in report_data:
            background_tasks_status[task_id] = {
                "status": "error",
                "filename": original_filename,
                "error": report_data["error"]
            }
            return
        
        # Generate summary using Gemini
        summarizer = GeminiSummarizer()
        summary = summarizer.summarize_report(report_data)
        
        # Save summary
        output_filename = generate_output_filename(original_filename)
        output_path = os.path.join(str(OUTPUT_DIR), output_filename)
        
        summarizer.save_summary(summary, output_path)
        
        # Update task status
        background_tasks_status[task_id] = {
            "status": "completed",
            "filename": original_filename,
            "output_file": output_filename,
            "output_path": output_path,
            "model_used": summary.get("metadata", {}).get("model_used", "gemini-pro")
        }
        
    except Exception as e:
        background_tasks_status[task_id] = {
            "status": "error",
            "filename": original_filename,
            "error": str(e)
        }
    finally:
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

def start_server(host="0.0.0.0", port=8000):
    """Start the FastAPI server"""
    uvicorn.run("src.api_server:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    # Start the server when run directly
    start_server()