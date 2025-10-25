from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class RecipeURLRequest(BaseModel):
    url: str

class Ingredient(BaseModel):
    name: str
    amount: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None

class RecipeStep(BaseModel):
    step_number: int
    instruction: str
    time_estimate: Optional[int] = None  # minutes
    parallel_tasks: Optional[List[str]] = None

class PrepStep(BaseModel):
    instruction: str
    time_estimate: Optional[int] = None
    category: Optional[str] = None  # 'chopping', 'measuring', 'preheating', etc.

class CookStep(BaseModel):
    step_number: int
    instruction: str
    time_estimate: Optional[int] = None
    parallel_tasks: Optional[List[str]] = None

class OptimizedRecipe(BaseModel):
    title: str
    ingredients: List[Ingredient]
    prep_phase: List[PrepStep]
    cook_phase: List[CookStep]
    recipe_id: Optional[int] = None
    total_time: Optional[int] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None

class VoiceCommandRequest(BaseModel):
    command: str  # 'next', 'repeat', 'what_prep', 'pause', 'resume'
    session_id: int

class CookingSessionResponse(BaseModel):
    session_id: int
    recipe_title: str
    current_step: Optional[str] = None
    current_phase: Optional[str] = None
    is_active: bool
    started_at: datetime