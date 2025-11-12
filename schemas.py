"""
Database Schemas for StartupMate

Each Pydantic model represents a collection in MongoDB. The collection name is the lowercase of the class name.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr

class IdeaAnalysis(BaseModel):
    idea: str = Field(..., description="User-entered startup idea text")
    summary: str
    market: str
    target_audience: str
    competitors: List[str] = []
    risks: List[str] = []
    next_steps: List[str] = []
    score_overall: Optional[int] = Field(None, ge=0, le=100)
    tags: List[str] = []

class DeckAnalysis(BaseModel):
    filename: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    overall_score: int = Field(..., ge=0, le=100)
    category_scores: Dict[str, int] = Field(default_factory=dict)
    suggestions: List[str] = []
    extracted_text_preview: Optional[str] = None

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str

# Example schemas retained for reference but not used directly by the app
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = Field(None, ge=0, le=120)
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    category: str
    in_stock: bool = True
