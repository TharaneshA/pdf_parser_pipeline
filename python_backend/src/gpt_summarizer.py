import os
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GPTSummarizer:
    """
    GPT-4 based summarizer for factory/operations reports.
    Generates structured summaries optimized for XR dashboard visualization.
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.max_tokens = int(os.getenv('MAX_TOKENS', 2000))
        self.temperature = float(os.getenv('TEMPERATURE', 0.3))
        
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
    
    def create_summary_prompt(self, report_data: Dict[str, Any]) -> str:
        """
        Creates a structured prompt for GPT-4 to generate report summaries.
        
        Args:
            report_data (Dict[str, Any]): Processed report data from PDF parser
            
        Returns:
            str: Formatted prompt for GPT-4
        """
        sections = report_data.get('sections', {})
        numerical_data = report_data.get('numerical_data', [])
        
        prompt = f"""
You are an AI assistant specialized in analyzing factory and operations reports. 
Analyze the following report and create a structured summary optimized for XR dashboard visualization.

SOURCE: {report_data.get('source_file', 'Unknown')}

REPORT CONTENT:
"""
        
        # Add sections to prompt
        for section_name, content in sections.items():
            prompt += f"\n\n{section_name.upper().replace('_', ' ')}:\n{content[:1000]}..."
        
        # Add numerical data context
        if numerical_data:
            prompt += "\n\nKEY METRICS FOUND:\n"
            for data in numerical_data[:10]:  # Limit to first 10 metrics
                prompt += f"- {data.get('context', 'N/A')}\n"
        
        prompt += """

Please provide a JSON response with the following structure:
{
  "executive_summary": "Brief 2-3 sentence overview of the report",
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
  "events": [
    {
      "time": "Time if available",
      "event": "Event description",
      "category": "Maintenance/Production/Safety/Other"
    }
  ],
  "recommendations": [
    {
      "priority": "High/Medium/Low",
      "action": "Recommended action",
      "timeline": "Suggested timeline"
    }
  ],
  "metrics": {
    "production_volume": "Number with unit",
    "quality_score": "Percentage or score",
    "downtime": "Time duration",
    "energy_consumption": "Number with unit"
  },
  "dashboard_alerts": [
    {
      "level": "Info/Warning/Critical",
      "message": "Alert message for XR display",
      "action_required": true/false
    }
  ]
}

Ensure all numerical values include appropriate units. If specific data is not available, use "N/A" or reasonable estimates based on context.
"""
        
        return prompt
    
    def summarize_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a structured summary using GPT-4.
        
        Args:
            report_data (Dict[str, Any]): Processed report data from PDF parser
            
        Returns:
            Dict[str, Any]: Structured summary for XR dashboard
        """
        try:
            prompt = self.create_summary_prompt(report_data)
            
            print("Sending request to GPT-4...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert factory operations analyst. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            summary_text = response.choices[0].message.content
            summary = json.loads(summary_text)
            
            # Add metadata
            summary['metadata'] = {
                'source_file': report_data.get('source_file', 'Unknown'),
                'processing_timestamp': self._get_timestamp(),
                'model_used': self.model,
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
            
            print(f"Summary generated successfully. Tokens used: {response.usage.total_tokens if response.usage else 'Unknown'}")
            return summary
            
        except json.JSONDecodeError as e:
            print(f"Error parsing GPT-4 response as JSON: {e}")
            return self._create_fallback_summary(report_data)
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return self._create_fallback_summary(report_data)
    
    def _create_fallback_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a basic fallback summary when GPT-4 fails.
        
        Args:
            report_data (Dict[str, Any]): Original report data
            
        Returns:
            Dict[str, Any]: Basic summary structure
        """
        sections = report_data.get('sections', {})
        
        return {
            "executive_summary": "Report processed successfully. Manual review recommended.",
            "key_insights": [
                "Report contains multiple sections",
                "Numerical data extracted",
                "Manual analysis recommended"
            ],
            "daily_output": {
                "total_production": "N/A",
                "efficiency_rate": "N/A",
                "status": "Unknown"
            },
            "anomalies": [],
            "events": [],
            "recommendations": [
                {
                    "priority": "Medium",
                    "action": "Review original report manually",
                    "timeline": "ASAP"
                }
            ],
            "metrics": {
                "production_volume": "N/A",
                "quality_score": "N/A",
                "downtime": "N/A",
                "energy_consumption": "N/A"
            },
            "dashboard_alerts": [
                {
                    "level": "Warning",
                    "message": "Automated summary failed - manual review needed",
                    "action_required": True
                }
            ],
            "metadata": {
                "source_file": report_data.get('source_file', 'Unknown'),
                "processing_timestamp": self._get_timestamp(),
                "model_used": "Fallback",
                "tokens_used": 0
            }
        }
    
    def _get_timestamp(self) -> str:
        """
        Returns current timestamp in ISO format.
        
        Returns:
            str: Current timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def batch_summarize(self, report_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processes multiple reports in batch.
        
        Args:
            report_data_list (List[Dict[str, Any]]): List of processed report data
            
        Returns:
            List[Dict[str, Any]]: List of summaries
        """
        summaries = []
        
        for i, report_data in enumerate(report_data_list):
            print(f"Processing report {i+1}/{len(report_data_list)}: {report_data.get('source_file', 'Unknown')}")
            summary = self.summarize_report(report_data)
            summaries.append(summary)
        
        return summaries
    
    def save_summary(self, summary: Dict[str, Any], output_path: str) -> bool:
        """
        Saves summary to JSON file.
        
        Args:
            summary (Dict[str, Any]): Summary data
            output_path (str): Path to save the summary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"Summary saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving summary: {e}")
            return False

if __name__ == "__main__":
    # Test the summarizer
    print("Testing GPT Summarizer...")
    
    try:
        summarizer = GPTSummarizer()
        
        # Create sample report data for testing
        sample_data = {
            "source_file": "test_report.pdf",
            "sections": {
                "executive_summary": "Daily production report showing normal operations with minor equipment issues.",
                "daily_output": "Total production: 1250 units. Efficiency: 87%. Line 2 experienced 30 minutes downtime.",
                "anomalies": "Conveyor belt speed fluctuation detected at 14:30. Temperature sensor reading inconsistent."
            },
            "numerical_data": [
                {"value": "1250", "unit": "units", "context": "Total production: 1250 units"},
                {"value": "87", "unit": "%", "context": "Efficiency: 87%"}
            ]
        }
        
        summary = summarizer.summarize_report(sample_data)
        print("\nGenerated Summary:")
        print(json.dumps(summary, indent=2))
        
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure to set up your .env file with OPENAI_API_KEY")