# src/config.py

import os
import json
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Gemini API Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please create a .env file.")

# --- Target JSON Schema ---
# This defines the exact structure we want the LLM to return.
TARGET_SCHEMA = {
    "Company name": "string",
    "Industry group": "string",
    "Country": "string",
    "Full time employees": "string (e.g., '4,000' or 'N/A')",
    "Risk rating score": "string (e.g., '28.9')",
    "Risk rating assessment": "string ('Low Risk', 'Medium Risk', 'High Risk', or 'N/A')",
    "Industry group position": "string (e.g., '432')",
    "Industry group positions total": "string (e.g., '450')",
    "Universe position": "string (e.g., '9143')",
    "Universe positions total": "string (e.g., '14689')",
    "Company description": "string (a concise, professional summary of the company's core business)"
}

# --- Gemini Prompt Template ---
# A detailed, zero-shot prompt that instructs the model on its task.
PROMPT_TEMPLATE = f"""
You are a world-class financial and ESG data analyst. Your task is to carefully review the provided text from an ESG report and extract only the information requested in the schema below.

**IMPORTANT INSTRUCTIONS:**
1. Carefully analyze the provided document text, which has been extracted from a PDF.
2. Extract values for **each key** in the "Desired JSON Schema" shown below.
3. If a specific value is **not explicitly present or cannot be confidently extracted**, return the string **"N/A"** for that key. Do not infer, fabricate, or leave fields blank.
4. Your response **must be a single, syntactically valid JSON object**. Do not include extra commentary, explanations, or formatting (e.g., do not wrap with ```).
5. Maintain the original structure and formatting of the schema keys. Do not modify key names or nesting.

**Desired JSON Schema:**
{json.dumps(TARGET_SCHEMA, indent=4)}

Document Text to Analyze:
--- BEGIN DOCUMENT ---
{{esg_report_text}}
--- END DOCUMENT ---

Your JSON Output:
"""
