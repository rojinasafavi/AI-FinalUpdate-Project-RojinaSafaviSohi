from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class SocialMediaPost(BaseModel):
    id: str = Field(..., description="Unique identifier for the post")
    text: str = Field(..., description="Content of the post")
    user: str = Field(..., description="Username or ID of the author")
    timestamp: datetime = Field(..., description="Time when the post was created in ISO format")
    likes: Optional[int] = Field(default=0, description="Number of likes")
    replies: Optional[int] = Field(default=0, description="Number of replies")

class SocialMediaIngestion(BaseModel):
    platform: str = Field(..., description="The source platform (e.g., twitter, instagram, linkedin)")
    posts: List[SocialMediaPost] = Field(..., description="List of posts ingested from the platform")

if __name__ == "__main__":
    # Provides an easy way to dump the JSON schema if the file is executed directly
    import json
    print(json.dumps(SocialMediaIngestion.model_json_schema(), indent=2))
