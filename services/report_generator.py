import json
import logging
from typing import Dict, Any
from services.openai_service import client, GEMINI_MODEL
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from openai import RateLimitError, APITimeoutError, APIError

logger = logging.getLogger(__name__)

# Apply robust retry logic to the report generation as well
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
    before_sleep=lambda retry_state: logger.warning(
        f"Report generator API call failed: Retrying... (Attempt {retry_state.attempt_number})"
    ),
    reraise=True
)
async def generate_management_report(aggregated_data: Dict[str, Any]) -> str:
    """
    Sends aggregated social media analysis data to Google Gemini and generates 
    a highly concise, professional management report.
    """
    if not aggregated_data or aggregated_data.get("total_processed", 0) == 0:
        return "No data available to generate a report."
        
    data_context = json.dumps(aggregated_data, indent=2)
    
    system_prompt = (
        "You are an executive business consultant. Review the provided aggregated "
        "social media data and produce a highly concise, professional management report. "
        "Your report must be formatted in clear Markdown and must include exactly "
        "these sections:\n"
        "1. **Executive Summary**: A brief 1-2 sentence overview of the data.\n"
        "2. **Key Risks**: Highlight any significant concerns, negative sentiment trends, or immediate threats.\n"
        "3. **Opportunities**: Highlight positive trends and areas for potential growth, marketing, or product improvement.\n"
        "4. **Actionable Insights**: Specific, strategic recommendations for the management team."
    )
    
    user_prompt = f"Aggregated Data:\n{data_context}\n\nPlease generate the management report."
    
    try:
        response = await client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        report_content = response.choices[0].message.content
        return str(report_content) if report_content else "No report generated."
        
    except Exception as e:
        logger.error(f"Error generating management report: {e}")
        return f"Failed to generate report due to an API error: {str(e)}"
