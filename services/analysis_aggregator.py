import asyncio
import logging
from collections import Counter
from typing import List, Dict, Any

from services.openai_service import analyze_text

logger = logging.getLogger(__name__)

async def _analyze_single_text_with_semaphore(text: str, semaphore: asyncio.Semaphore) -> dict:
    """Helper function to bound the maximum number of concurrent requests."""
    async with semaphore:
        return await analyze_text(text)

async def aggregate_social_media_data(texts: List[str], max_concurrent: int = 10) -> Dict[str, Any]:
    """
    Processes texts asynchronously while strictly adhering to rate limits using Semaphores.
    Aggregates results into a high-level summary report.
    """
    if not texts:
        return {
            "total_processed": 0, "sentiment_distribution": {},
            "common_topics": [], "sample_summaries": []
        }
        
    logger.info(f"Starting async aggregation of {len(texts)} posts with max_concurrent={max_concurrent}")
    
    # Restrict concurrent API calls to avoid hitting rate limits instantly
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Create all background tasks
    tasks = [_analyze_single_text_with_semaphore(text, semaphore) for text in texts]
    
    # Gather responses efficiently using async
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    results = []
    errors = []
    for res in raw_results:
        if isinstance(res, Exception):
            logger.error(f"A task failed exceptionally: {res}")
            errors.append(str(res))
            continue
        if res and "error" not in res:
            results.append(res)
        elif res and "error" in res:
            errors.append(res.get("error"))
            
    total_valid = len(results)
    if total_valid == 0:
        if errors and all(e == "quota_exceeded" for e in errors):
            return {
                "error": (
                    "Google Gemini API quota exceeded. The free tier is limited to "
                    "about 20 requests per day per model. Wait for the daily reset, "
                    "switch GEMINI_MODEL in .env, or use a key with billing enabled."
                )
            }
        return {"error": "All API calls failed or did not return valid data."}
        
    # --- Aggregation Logic ---
    sentiment_counts = Counter(res.get("sentiment", "neutral").lower() for res in results)
    sentiment_distribution = {
        sentiment: round((count / total_valid) * 100, 2)
        for sentiment, count in sentiment_counts.items()
    }
    
    all_topics = []
    for res in results:
        topics = res.get("topics", [])
        if isinstance(topics, list):
            all_topics.extend([str(t).strip().lower() for t in topics])
            
    topic_counts = Counter(all_topics)
    common_topics = [
        {"topic": topic.title(), "count": count} 
        for topic, count in topic_counts.most_common(10)
    ]
    
    sample_summaries = [res.get("summary") for res in results if res.get("summary")][:5]
    
    logger.info("Async aggregation completed successfully.")
    
    return {
        "total_processed": total_valid,
        "sentiment_distribution": sentiment_distribution,
        "common_topics": common_topics,
        "sample_summaries": sample_summaries
    }
