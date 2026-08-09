import json
import re
from typing import List, Union
from pathlib import Path
from pydantic import ValidationError

from models.schemas import SocialMediaIngestion

def normalize_text(text: str) -> str:
    """
    Cleans and normalizes social media text by removing emojis, 
    URLs, mentions, line breaks, and extra whitespaces.
    """
    if not text:
        return ""
        
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove mentions (@username)
    text = re.sub(r'@\w+', '', text)
    
    # Remove emojis using a regex pattern capturing most emoji unicode ranges
    # Note: For highly rigorous production use, the external `emoji` package is recommended.
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags (iOS)
        "\u2702-\u27b0"
        "\u24c2-\U0001f251"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # Replace line breaks and tabs with space
    text = re.sub(r'[\n\t\r]', ' ', text)
    
    # Collapse multiple spaces into one and strip edge whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def process_social_media_file(file_path: Union[str, Path]) -> List[str]:
    """
    Loads a JSON file containing social media data, validates it against 
    the Pydantic schema, normalizes the text content, and returns a list 
    of clean texts ready for analysis.
    
    Args:
        file_path (Union[str, Path]): Path to the JSON data file.
        
    Returns:
        List[str]: A list of cleaned and normalized text strings.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        # Validate data against Pydantic schema
        validated_data = SocialMediaIngestion(**raw_data)
        
        # Normalize and collect text
        clean_texts = []
        for post in validated_data.posts:
            cleaned = normalize_text(post.text)
            if cleaned:  # Exclude entries that are empty after cleaning
                clean_texts.append(cleaned)
                
        return clean_texts
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON syntax in {file_path}: {e}")
    except ValidationError as e:
        raise ValueError(f"Schema Validation Error for {file_path}:\n{e}")
