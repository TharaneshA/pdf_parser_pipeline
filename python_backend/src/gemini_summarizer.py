import os
import json
import datetime
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiSummarizer:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Configure Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
            
        genai.configure(api_key=api_key)
        
        # Set model configuration
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4096"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.2"))
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "max_output_tokens": self.max_tokens,
                "temperature": self.temperature
            }
        )
    
    def create_summary_prompt(self, report_data: Dict[str, Any]) -> str:
        """
        Create a structured prompt for Gemini based on the processed report data.
        
        Args:
            report_data: Processed report data from the PDF parser
            
        Returns:
            str: Formatted prompt for Gemini
        """
        # Extract data from the report
        title = report_data.get("title", "Unknown Report")
        sections = report_data.get("sections", {})
        numerical_data = report_data.get("numerical_data", [])
        tables = report_data.get("tables", [])
        
        # Create a structured prompt
        prompt = f"""You are an expert data analyst for Satori XR, specializing in summarizing technical reports for visualization in XR environments. 

Analyze the following report and create a structured summary in VALID JSON format.

REPORT TITLE: {title}

"""
        
        # Add sections content
        if sections:
            prompt += "REPORT SECTIONS:\n"
            for section_name, section_content in sections.items():
                prompt += f"\n## {section_name}\n{section_content}\n"
        
        # Add numerical data
        if numerical_data:
            prompt += "\nNUMERICAL DATA POINTS:\n"
            for data_point in numerical_data:
                prompt += f"- {data_point['context']}: {data_point['value']} {data_point.get('unit', '')}\n"
        
        # Add tables
        if tables:
            prompt += "\nTABLES:\n"
            for i, table in enumerate(tables):
                prompt += f"\nTable {i+1}:\n{table}\n"
        
        # Add output format instructions
        prompt += """

Your task is to create a comprehensive summary of this report in the following JSON format:


{
  "title": "Report Title",
  "summary": "A concise 2-3 sentence overview of the entire report",
  "key_findings": [
    "Finding 1",
    "Finding 2",
    "Finding 3"
  ],
  "sections": [
    {
      "name": "Section Name",
      "summary": "Brief summary of this section"
    }
  ],
  "metrics": [
    {
      "name": "Metric Name",
      "value": "Numerical value",
      "unit": "Unit of measurement",
      "context": "Brief explanation of what this metric means",
      "trend": "increasing/decreasing/stable"
    }
  ],
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2"
  ],
  "visualization_suggestions": [
    {
      "type": "chart_type",
      "title": "Suggested visualization title",
      "description": "What data should be visualized and why",
      "data_points": ["relevant metric names"]
    }
  ]
}


Ensure your response is ONLY valid JSON without any additional text or explanation. Extract the most important information from the report, focusing on key metrics, trends, and insights that would be valuable in an XR visualization environment.
"""
        
        return prompt
    
    def summarize_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of the report using Gemini.
        
        Args:
            report_data: Processed report data from the PDF parser
            
        Returns:
            Dict[str, Any]: Generated summary with metadata
        """
        # Create the prompt
        prompt = self.create_summary_prompt(report_data)
        
        try:
            # Call Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Extract JSON from response
            try:
                # Try to parse the response as JSON
                if "```json" in response_text:
                    # Extract JSON from code block
                    json_text = response_text.split("```json")[1].split("```")[0].strip()
                    summary_data = json.loads(json_text)
                else:
                    # Try to parse the whole response as JSON
                    summary_data = json.loads(response_text)
                
                # Add metadata
                summary_data["metadata"] = {
                    "source_file": report_data.get("filename", "Unknown"),
                    "processing_timestamp": self._get_timestamp(),
                    "model_used": self.model_name,
                    "response_tokens": len(response_text.split()) # Approximate token count
                }
                
                return summary_data
                
            except json.JSONDecodeError:
                # If JSON parsing fails, create a fallback summary
                print("Error parsing Gemini response as JSON. Creating fallback summary.")
                fallback_summary = self._create_fallback_summary(report_data, response_text)
                return fallback_summary
                
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            fallback_summary = self._create_fallback_summary(report_data, str(e))
            return fallback_summary
    
    def _create_fallback_summary(self, report_data: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """
        Create a basic fallback summary when the API call or JSON parsing fails.
        
        Args:
            report_data: Processed report data from the PDF parser
            error_message: Error message from the API call or JSON parsing
            
        Returns:
            Dict[str, Any]: Basic fallback summary
        """
        title = report_data.get("title", "Unknown Report")
        sections = list(report_data.get("sections", {}).keys())
        
        fallback_summary = {
            "title": title,
            "summary": f"This is an automatically generated fallback summary for {title}.",
            "key_findings": ["Automatic summary generation encountered an error."],
            "sections": [{
                "name": section_name,
                "summary": f"Content from {section_name}"
            } for section_name in sections[:3]],  # Include up to 3 sections
            "metrics": [],
            "recommendations": ["Please review the original document."],
            "visualization_suggestions": [],
            "metadata": {
                "source_file": report_data.get("filename", "Unknown"),
                "processing_timestamp": self._get_timestamp(),
                "model_used": f"{self.model_name} (fallback)",
                "error": error_message
            }
        }
        
        # Add some metrics if available
        numerical_data = report_data.get("numerical_data", [])
        for data_point in numerical_data[:5]:  # Include up to 5 metrics
            fallback_summary["metrics"].append({
                "name": data_point.get("context", "Unknown Metric"),
                "value": data_point.get("value", "N/A"),
                "unit": data_point.get("unit", ""),
                "context": "Automatically extracted from document",
                "trend": "unknown"
            })
        
        return fallback_summary
    
    def _get_timestamp(self) -> str:
        """
        Get the current timestamp in ISO format.
        
        Returns:
            str: Current timestamp
        """
        return datetime.datetime.now().isoformat()
    
    def batch_summarize(self, reports_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate summaries for multiple reports.
        
        Args:
            reports_data: List of processed report data
            
        Returns:
            List[Dict[str, Any]]: List of generated summaries
        """
        summaries = []
        for report_data in reports_data:
            summary = self.summarize_report(report_data)
            summaries.append(summary)
        return summaries
    
    def save_summary(self, summary: Dict[str, Any], output_path: str) -> None:
        """
        Save the summary to a JSON file.
        
        Args:
            summary: Generated summary
            output_path: Path to save the summary
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Summary saved to {output_path}")

# For testing
if __name__ == "__main__":
    # Sample data for testing
    sample_data = {
        "filename": "test_report.pdf",
        "title": "Manufacturing Efficiency Report Q2 2023",
        "sections": {
            "Executive Summary": "This report analyzes the manufacturing efficiency of our facilities in Q2 2023. Overall efficiency increased by 12% compared to Q1.",
            "Production Metrics": "Production increased by 15% while defect rates decreased by 7%. The new automated line contributed significantly to these improvements."
        },
        "numerical_data": [
            {"context": "Efficiency Increase", "value": "12", "unit": "%"},
            {"context": "Production Increase", "value": "15", "unit": "%"},
            {"context": "Defect Rate Decrease", "value": "7", "unit": "%"}
        ]
    }
    
    # Test the summarizer
    summarizer = GeminiSummarizer()
    summary = summarizer.summarize_report(sample_data)
    
    print(json.dumps(summary, indent=2))