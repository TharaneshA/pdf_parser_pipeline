import json
import logging
import google.generativeai as genai
from src.config import GOOGLE_API_KEY, PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

# Configure the Gemini client
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    logger.error(f"Failed to configure Gemini API. Ensure GOOGLE_API_KEY is valid. Error: {e}")
    raise

def extract_esg_data(markdown_content: str) -> dict | None:
    """
    Uses the Gemini API to extract structured ESG data from the parsed markdown text.

    Args:
        markdown_content: The text content parsed from the ESG report.

    Returns:
        A dictionary containing the extracted data, or None on failure.
    """
    logger.info("Preparing to send content to Gemini for data extraction...")
    
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    prompt = PROMPT_TEMPLATE.replace("{{esg_report_text}}", markdown_content)
    
    try:
        response = model.generate_content(prompt)
        
        # Robustly find and parse the JSON block from the model's response
        response_text = response.text
        
        # Find the start and end of the JSON object
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            logger.error(f"Could not find a valid JSON object in Gemini's response. Raw response: {response_text}")
            return None
            
        json_string = response_text[json_start:json_end]
        
        logger.info("Received response from Gemini. Parsing JSON...")
        extracted_data = json.loads(json_string)
        
        logger.info("Successfully extracted and parsed data from Gemini.")
        return extracted_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from Gemini's response. Error: {e}. Raw text: '{json_string}'")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during Gemini API call. Error: {e}", exc_info=True)
        return None