import json
import pytest

from services.data_processing import normalize_text, process_social_media_file


def test_normalize_text_removes_urls_mentions_and_emojis():
    text = "Check this https://example.com/abc @user123 😀🔥\n\nGreat product!"
    cleaned = normalize_text(text)
    assert "http" not in cleaned
    assert "@" not in cleaned
    assert "😀" not in cleaned
    assert "🔥" not in cleaned
    assert "\n" not in cleaned
    assert "  " not in cleaned
    assert "Great product!" in cleaned


def test_normalize_text_collapses_whitespace():
    cleaned = normalize_text("  hello   world \t here ")
    assert cleaned == "hello world here"


def test_normalize_text_empty_and_none():
    assert normalize_text("") == ""
    assert normalize_text(None) == ""


def test_process_social_media_file_valid():
    texts = process_social_media_file("data/sample_input.json")
    assert isinstance(texts, list)
    assert len(texts) == 3
    assert all(isinstance(t, str) and t.strip() for t in texts)


def test_process_social_media_file_missing_file():
    with pytest.raises(FileNotFoundError):
        process_social_media_file("data/does_not_exist.json")


def test_process_social_media_file_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError):
        process_social_media_file(bad)


def test_process_social_media_file_schema_violation(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"platform": "twitter", "posts": [{"id": "1"}]}), encoding="utf-8")
    with pytest.raises(ValueError):
        process_social_media_file(bad)


def test_process_social_media_file_drops_empty_posts(tmp_path):
    only_emoji = tmp_path / "emoji.json"
    only_emoji.write_text(
        json.dumps({
            "platform": "twitter",
            "posts": [
                {"id": "1", "text": "🎉🎉", "user": "u1", "timestamp": "2023-10-01T12:00:00Z"},
                {"id": "2", "text": "Real content here", "user": "u2", "timestamp": "2023-10-01T12:00:00Z"},
            ],
        }),
        encoding="utf-8",
    )
    texts = process_social_media_file(only_emoji)
    assert texts == ["Real content here"]
