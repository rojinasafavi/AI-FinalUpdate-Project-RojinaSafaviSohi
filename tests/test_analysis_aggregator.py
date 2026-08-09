import asyncio
from unittest.mock import patch

from services.analysis_aggregator import aggregate_social_media_data


def run(coro):
    return asyncio.run(coro)


def test_aggregate_empty_texts():
    result = run(aggregate_social_media_data([]))
    assert result["total_processed"] == 0
    assert result["sentiment_distribution"] == {}
    assert result["common_topics"] == []
    assert result["sample_summaries"] == []


def test_aggregate_all_failures_returns_error():
    async def fake_analyze(text):
        return {"error": "API exploded"}

    with patch("services.analysis_aggregator.analyze_text", side_effect=fake_analyze):
        result = run(aggregate_social_media_data(["a", "b"]))

    assert "error" in result


def test_aggregate_all_quota_failures_returns_quota_message():
    async def fake_analyze(text):
        return {"error": "quota_exceeded"}

    with patch("services.analysis_aggregator.analyze_text", side_effect=fake_analyze):
        result = run(aggregate_social_media_data(["a", "b"]))

    assert "quota" in result["error"].lower()
    assert "20 requests per day" in result["error"]


def test_aggregate_exception_results_are_skipped():
    async def fake_analyze(text):
        if text == "bad":
            raise RuntimeError("API call failed")
        return {"sentiment": "positive", "topics": ["AI", "ML"], "summary": "Great!"}

    with patch("services.analysis_aggregator.analyze_text", side_effect=fake_analyze):
        result = run(aggregate_social_media_data(["bad", "good"]))

    assert result["total_processed"] == 1
    assert result["sentiment_distribution"] == {"positive": 100.0}
    assert result["common_topics"][0]["topic"] == "Ai"


def test_aggregate_distribution_and_topics():
    responses = [
        {"sentiment": "positive", "topics": ["AI", "speed"], "summary": "s1"},
        {"sentiment": "negative", "topics": ["bugs", "app"], "summary": "s2"},
        {"sentiment": "neutral", "topics": ["support"], "summary": "s3"},
        {"sentiment": "positive", "topics": ["AI"], "summary": "s4"},
    ]

    async def fake_analyze(text):
        return responses.pop(0)

    with patch("services.analysis_aggregator.analyze_text", side_effect=fake_analyze):
        result = run(aggregate_social_media_data(["a", "b", "c", "d"]))

    assert result["total_processed"] == 4
    assert result["sentiment_distribution"] == {"positive": 50.0, "negative": 25.0, "neutral": 25.0}
    topics = {t["topic"] for t in result["common_topics"]}
    assert "Ai" in topics
    assert len(result["sample_summaries"]) == 4
