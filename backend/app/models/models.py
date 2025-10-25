from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional, List
import json

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(unique=True, index=True)
    name: str
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Recipe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    source_url: str
    original_recipe: str  # JSON string of original parsed recipe
    prep_phase: str  # JSON string of prep steps
    cook_phase: str  # JSON string of cooking steps
    ingredients: str  # JSON string of ingredients list
    total_time: Optional[int] = None  # Total cooking time in minutes
    prep_time: Optional[int] = None  # Prep time in minutes
    cook_time: Optional[int] = None  # Cook time in minutes
    servings: Optional[int] = None
    difficulty: Optional[str] = None  # easy, medium, hard
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CookingSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id")
    user_id: str
    current_step: Optional[str] = None
    current_phase: Optional[str] = None  # 'prep' or 'cook'
    is_active: bool = Field(default=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class VoiceCommand(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="cookingsession.id")
    command: str  # 'next', 'repeat', 'what_prep', etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)