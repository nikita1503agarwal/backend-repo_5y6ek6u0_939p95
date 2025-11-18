"""
Database Schemas for Blog Platform (Hashnode-like)

Each Pydantic model represents a MongoDB collection. The collection name is
lowercase of the class name (e.g., User -> "user").

Collections:
- user
- post
- comment
"""

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class User(BaseModel):
    """
    Users collection schema
    Collection name: "user"
    """
    username: str = Field(..., min_length=3, max_length=30, description="Unique username")
    name: str = Field(..., min_length=1, max_length=120, description="Display name")
    email: EmailStr = Field(..., description="Email address")
    bio: Optional[str] = Field(None, max_length=500, description="Short bio")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")
    website: Optional[str] = Field(None, description="Personal website")


class Comment(BaseModel):
    """Embedded comment schema used when creating a comment"""
    author_username: str = Field(..., min_length=3, description="Username of commenter")
    content: str = Field(..., min_length=1, max_length=5000, description="Comment content")


class Post(BaseModel):
    """
    Posts collection schema
    Collection name: "post"
    """
    title: str = Field(..., min_length=3, max_length=200, description="Post title")
    body: str = Field(..., min_length=1, description="Post body (Markdown supported)")
    author_username: str = Field(..., min_length=3, description="Author username")
    tags: List[str] = Field(default_factory=list, description="List of tags")
    cover_image: Optional[str] = Field(None, description="Cover image URL")
    published: bool = Field(default=True, description="Published status")
