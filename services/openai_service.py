import os
import json
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# Configure module-level logger
logger = logging.getLogger(__name__)

load_dotenv()
# Using Google Gemini's OpenAI-compatible endpoint (free tier supported).
# Get a key at https://aistudio.google.com/apikey
client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"),
)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

def _is_quota_exceeded(e: Exception) -> bool:
    """Detects 429 / 'quota' / 'resource exhausted' API errors (free-tier limits)."""
    status = getattr(e, "status_code", None)
    message = str(e).lower()
    return status == 429 or "quota" in message or "resource_exhausted" in message

# Advanced Retry Logic: Backoff exponentially, retry up to 5 times for transient errors
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
    before_sleep=lambda retry_state: logger.warning(
        f"API call failed! Retrying... (Attempt {retry_state.attempt_number})"
    ),
    reraise=True
)
async def analyze_text(text: str) -> dict:
    """
    Analyzes text asynchronously using Google Gemini (via its OpenAI-compatible endpoint).
    Features built-in retry mechanisms and robust error handling for production scale.
    """
    if not text or not text.strip():
        return {"sentiment": "neutral", "topics": [], "summary": "Empty text provided."}

    system_prompt = (
        "You are an expert social media data analyst. Analyze the provided text and "
        "output a JSON object with exactly the following three keys:\n"
        "1. 'sentiment': A string that must be exactly 'positive', 'negative', or 'neutral'.\n"
        "2. 'topics': A list of short strings representing the main topics discussed.\n"
        "3. 'summary': A concise one-sentence summary of the text."
    )

    try:
        response = await client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result_content = response.choices[0].message.content
        if result_content:
            return json.loads(result_content)
        return {}
        
    except Exception as e:
        logger.error(f"Unrecoverable error during OpenAI API call: {e}")
        return {
            "error": "quota_exceeded" if _is_quota_exceeded(e) else str(e),
            "sentiment": "neutral",
            "topics": [],
            "summary": "Failed to analyze due to an API error."
        }
