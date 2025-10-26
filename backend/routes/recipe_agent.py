from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from backend.app.db.database import get_db
from backend.app.models.models import Recipe, CookingSession, VoiceCommand, Favorite
from backend.app.schemas.schemas import (
    RecipeURLRequest, OptimizedRecipe, VoiceCommandRequest, 
    CookingSessionResponse, RecipeModificationRequest, RecipeModificationResponse
)
from backend.scrapers.recipe_scraper import RecipeScraper
from backend.app.agents.recipe_optimizer import RecipeOptimizer
from backend.app.agents.recipe_modifier import RecipeModifier
from backend.app.agents.voice_assistant import VoiceCookingAssistant
import json
from datetime import datetime
from typing import List

router = APIRouter()

# Initialize services
scraper = RecipeScraper()
optimizer = RecipeOptimizer()
recipe_modifier = RecipeModifier()
voice_assistant = VoiceCookingAssistant()

@router.post("/create_recipe", response_model=OptimizedRecipe)
async def create_recipe(recipe_data: OptimizedRecipe, db: Session = Depends(get_db)):
    """
    Create a recipe directly without scraping
    """
    try:
        # Save to database
        recipe = Recipe(
            title=recipe_data.title,
            source_url="direct_creation",
            original_recipe=json.dumps({"title": recipe_data.title}),
            prep_phase=json.dumps([step.dict() for step in recipe_data.prep_phase]),
            cook_phase=json.dumps([step.dict() for step in recipe_data.cook_phase]),
            ingredients=json.dumps([ing.dict() for ing in recipe_data.ingredients]),
            total_time=recipe_data.total_time,
            prep_time=recipe_data.prep_time,
            cook_time=recipe_data.cook_time,
            servings=recipe_data.servings,
            difficulty=recipe_data.difficulty,
            user_id="test_user"
        )
        
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        
        return recipe_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create recipe: {str(e)}")

@router.post("/parse_recipe", response_model=OptimizedRecipe)
async def parse_recipe(request: RecipeURLRequest, db: Session = Depends(get_db)):
    """
    Parse a recipe from a URL and optimize it for mise-en-place cooking
    """
    try:
        # Scrape the recipe from the URL
        scraped_data = scraper.scrape_recipe(request.url)
        
        # Optimize the recipe
        optimized_recipe = optimizer.optimize_recipe(scraped_data)
        
        # Save to database
        recipe = Recipe(
            title=optimized_recipe.title,
            source_url=request.url,
            original_recipe=json.dumps(scraped_data),
            prep_phase=json.dumps([step.dict() for step in optimized_recipe.prep_phase]),
            cook_phase=json.dumps([step.dict() for step in optimized_recipe.cook_phase]),
            ingredients=json.dumps([ing.dict() for ing in optimized_recipe.ingredients]),
            total_time=optimized_recipe.total_time,
            prep_time=optimized_recipe.prep_time,
            cook_time=optimized_recipe.cook_time,
            servings=optimized_recipe.servings,
            difficulty=optimized_recipe.difficulty,
            user_id="default_user"  # In a real app, this would come from authentication
        )
        
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        
        optimized_recipe.recipe_id = recipe.id
        return optimized_recipe
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse recipe: {str(e)}")

@router.get("/recipes")
def get_recipes(db: Session = Depends(get_db)):
    """
    Get all saved recipes
    """
    recipes = db.exec(select(Recipe)).all()
    return {"recipes": recipes}

@router.get("/recipe/{recipe_id}")
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """
    Get a specific recipe by ID
    """
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Parse JSON fields back to objects
    optimized_recipe = OptimizedRecipe(
        title=recipe.title,
        ingredients=[json.loads(ing) for ing in json.loads(recipe.ingredients)],
        prep_phase=[json.loads(step) for step in json.loads(recipe.prep_phase)],
        cook_phase=[json.loads(step) for step in json.loads(recipe.cook_phase)],
        total_time=recipe.total_time,
        prep_time=recipe.prep_time,
        cook_time=recipe.cook_time,
        servings=recipe.servings,
        difficulty=recipe.difficulty
    )
    
    return optimized_recipe

@router.delete("/recipe/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """
    Delete a recipe by ID
    """
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    db.delete(recipe)
    db.commit()
    
    return {"message": "Recipe deleted successfully"}

@router.post("/start_cooking/{recipe_id}", response_model=CookingSessionResponse)
def start_cooking_session(recipe_id: int, db: Session = Depends(get_db)):
    """
    Start a new cooking session for a recipe
    """
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Create new cooking session
    session = CookingSession(
        recipe_id=recipe_id,
        user_id="default_user",  # In a real app, this would come from authentication
        current_step=json.loads(recipe.prep_phase)[0]["instruction"] if json.loads(recipe.prep_phase) else None,
        current_phase="prep",
        is_active=True
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return CookingSessionResponse(
        session_id=session.id,
        recipe_title=recipe.title,
        current_step=session.current_step,
        current_phase=session.current_phase,
        is_active=session.is_active,
        started_at=session.started_at
    )

@router.post("/voice_command")
def process_voice_command(request: VoiceCommandRequest, db: Session = Depends(get_db)):
    """
    Process voice commands during cooking
    """
    session = db.get(CookingSession, request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Cooking session not found")
    
    recipe = db.get(Recipe, session.recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Parse recipe data safely
    try:
        ingredients_data = json.loads(recipe.ingredients) if recipe.ingredients else []
        prep_phase_data = json.loads(recipe.prep_phase) if recipe.prep_phase else []
        cook_phase_data = json.loads(recipe.cook_phase) if recipe.cook_phase else []
        
        optimized_recipe = OptimizedRecipe(
            title=recipe.title,
            ingredients=ingredients_data,
            prep_phase=prep_phase_data,
            cook_phase=cook_phase_data,
            total_time=recipe.total_time,
            prep_time=recipe.prep_time,
            cook_time=recipe.cook_time,
            servings=recipe.servings,
            difficulty=recipe.difficulty
        )
    except (json.JSONDecodeError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse recipe data: {str(e)}")
    
    # Process the voice command
    response = voice_assistant.process_voice_command(
        request.command, session, optimized_recipe, db
    )
    
    # Log the voice command
    voice_cmd = VoiceCommand(
        session_id=request.session_id,
        command=request.command
    )
    db.add(voice_cmd)
    db.commit()
    
    return response

@router.get("/cooking_session/{session_id}")
def get_cooking_session(session_id: int, db: Session = Depends(get_db)):
    """
    Get current status of a cooking session
    """
    session = db.get(CookingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Cooking session not found")
    
    recipe = db.get(Recipe, session.recipe_id)
    
    return CookingSessionResponse(
        session_id=session.id,
        recipe_title=recipe.title if recipe else "Unknown Recipe",
        current_step=session.current_step,
        current_phase=session.current_phase,
        is_active=session.is_active,
        started_at=session.started_at
    )
@router.post("/favorites/{recipe_id}")
def add_to_favorites(recipe_id: int, db: Session = Depends(get_db)):
    """
    Add a recipe to favorites
    """
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Check if already favorited
    existing_favorite = db.exec(
        select(Favorite).where(
            Favorite.user_id == "default_user",
            Favorite.recipe_id == recipe_id
        )
    ).first()
    
    if existing_favorite:
        raise HTTPException(status_code=400, detail="Recipe already in favorites")
    
    favorite = Favorite(
        user_id="default_user",
        recipe_id=recipe_id
    )
    
    db.add(favorite)
    db.commit()
    
    return {"message": "Recipe added to favorites"}

@router.delete("/favorites/{recipe_id}")
def remove_from_favorites(recipe_id: int, db: Session = Depends(get_db)):
    """
    Remove a recipe from favorites
    """
    favorite = db.exec(
        select(Favorite).where(
            Favorite.user_id == "default_user",
            Favorite.recipe_id == recipe_id
        )
    ).first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Recipe not in favorites")
    
    db.delete(favorite)
    db.commit()
    
    return {"message": "Recipe removed from favorites"}

@router.get("/favorites")
def get_favorites(db: Session = Depends(get_db)):
    """
    Get all favorite recipes for the user
    """
    favorites = db.exec(
        select(Favorite).where(Favorite.user_id == "default_user")
    ).all()
    
    favorite_recipes = []
    for favorite in favorites:
        recipe = db.get(Recipe, favorite.recipe_id)
        if recipe:
            favorite_recipes.append(recipe)
    
    return {"recipes": favorite_recipes}

@router.get("/favorites/check/{recipe_id}")
def check_if_favorite(recipe_id: int, db: Session = Depends(get_db)):
    """
    Check if a recipe is favorited by the user
    """
    favorite = db.exec(
        select(Favorite).where(
            Favorite.user_id == "default_user",
            Favorite.recipe_id == recipe_id
        )
    ).first()
    
    return {"is_favorite": favorite is not None}

@router.post("/modify_recipe", response_model=RecipeModificationResponse)
async def modify_recipe(request: RecipeModificationRequest, db: Session = Depends(get_db)):
    """
    Modify a recipe based on available ingredients, serving size, and dietary preferences
    """
    try:
        # Get the original recipe
        recipe = db.get(Recipe, request.recipe_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Parse the recipe data
        try:
            ingredients_data = json.loads(recipe.ingredients) if recipe.ingredients else []
            prep_phase_data = json.loads(recipe.prep_phase) if recipe.prep_phase else []
            cook_phase_data = json.loads(recipe.cook_phase) if recipe.cook_phase else []
            
            original_recipe = OptimizedRecipe(
                title=recipe.title,
                ingredients=ingredients_data,
                prep_phase=prep_phase_data,
                cook_phase=cook_phase_data,
                total_time=recipe.total_time,
                prep_time=recipe.prep_time,
                cook_time=recipe.cook_time,
                servings=recipe.servings,
                difficulty=recipe.difficulty
            )
        except (json.JSONDecodeError, TypeError) as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse recipe data: {str(e)}")
        
        # Prepare modification request
        modification_request = {
            "available_ingredients": [ing.dict() for ing in request.available_ingredients],
            "target_servings": request.target_servings,
            "dietary_preferences": request.dietary_preferences or [],
            "substitution_preferences": request.substitution_preferences or {}
        }
        
        # Modify the recipe
        modification_result = recipe_modifier.modify_recipe(original_recipe, modification_request)
        
        return modification_result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to modify recipe: {str(e)}")

@router.post("/modify_recipe/{recipe_id}/save", response_model=OptimizedRecipe)
async def save_modified_recipe(recipe_id: int, modification_request: RecipeModificationRequest, db: Session = Depends(get_db)):
    """
    Modify a recipe and save the modified version to the database
    """
    try:
        # Get the original recipe
        original_recipe = db.get(Recipe, recipe_id)
        if not original_recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Parse the recipe data
        try:
            ingredients_data = json.loads(original_recipe.ingredients) if original_recipe.ingredients else []
            prep_phase_data = json.loads(original_recipe.prep_phase) if original_recipe.prep_phase else []
            cook_phase_data = json.loads(original_recipe.cook_phase) if original_recipe.cook_phase else []
            
            recipe_obj = OptimizedRecipe(
                title=original_recipe.title,
                ingredients=ingredients_data,
                prep_phase=prep_phase_data,
                cook_phase=cook_phase_data,
                total_time=original_recipe.total_time,
                prep_time=original_recipe.prep_time,
                cook_time=original_recipe.cook_time,
                servings=original_recipe.servings,
                difficulty=original_recipe.difficulty
            )
        except (json.JSONDecodeError, TypeError) as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse recipe data: {str(e)}")
        
        # Prepare modification request
        modification_data = {
            "available_ingredients": [ing.dict() for ing in modification_request.available_ingredients],
            "target_servings": modification_request.target_servings,
            "dietary_preferences": modification_request.dietary_preferences or [],
            "substitution_preferences": modification_request.substitution_preferences or {}
        }
        
        # Modify the recipe
        modification_result = recipe_modifier.modify_recipe(recipe_obj, modification_data)
        modified_recipe = modification_result.modified_recipe
        
        # Save the modified recipe to database
        new_recipe = Recipe(
            title=f"Modified {modified_recipe.title}",
            source_url=f"modified_from_{recipe_id}",
            original_recipe=json.dumps({"original_recipe_id": recipe_id, "modifications": modification_result.modification_notes}),
            prep_phase=json.dumps([step.dict() for step in modified_recipe.prep_phase]),
            cook_phase=json.dumps([step.dict() for step in modified_recipe.cook_phase]),
            ingredients=json.dumps([ing.dict() for ing in modified_recipe.ingredients]),
            total_time=modified_recipe.total_time,
            prep_time=modified_recipe.prep_time,
            cook_time=modified_recipe.cook_time,
            servings=modified_recipe.servings,
            difficulty=modified_recipe.difficulty,
            user_id="default_user"  # In a real app, this would come from authentication
        )
        
        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)
        
        return modified_recipe
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save modified recipe: {str(e)}")

@router.get("/recipe/{recipe_id}/modification_suggestions")
async def get_modification_suggestions(recipe_id: int, db: Session = Depends(get_db)):
    """
    Get AI-powered suggestions for modifying a recipe based on common dietary preferences and substitutions
    """
    try:
        recipe = db.get(Recipe, recipe_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Parse ingredients
        try:
            ingredients_data = json.loads(recipe.ingredients) if recipe.ingredients else []
        except (json.JSONDecodeError, TypeError):
            ingredients_data = []
        
        # Use AI to analyze the recipe and suggest modifications
        ingredients_text = "\n".join([
            f"- {ing.get('name', '')}: {ing.get('amount', '')} {ing.get('unit', '')}"
            for ing in ingredients_data
        ])
        
        # Create AI prompt for modification suggestions
        prompt = f"""
You are a professional chef and nutritionist. Analyze this recipe and provide intelligent modification suggestions.

RECIPE: {recipe.title}
INGREDIENTS:
{ingredients_text}

Provide suggestions for:
1. Dietary modifications (vegetarian, vegan, gluten-free, keto, etc.)
2. Healthier ingredient substitutions
3. Common ingredient alternatives
4. Serving size scaling options

Return your analysis as JSON with this structure:
{{
    "dietary_modifications": [
        {{
            "type": "vegetarian",
            "description": "Convert to vegetarian by substituting meat with plant-based alternatives",
            "affected_ingredients": ["ingredient1", "ingredient2"],
            "suggested_substitutes": ["tofu", "tempeh", "mushrooms"],
            "cooking_adjustments": "Additional notes about cooking changes needed"
        }}
    ],
    "healthier_substitutions": [
        {{
            "original": "ingredient name",
            "substitutes": ["healthier option 1", "healthier option 2"],
            "reason": "Why this substitution is healthier",
            "cooking_notes": "Any cooking adjustments needed"
        }}
    ],
    "common_alternatives": [
        {{
            "original": "ingredient name",
            "alternatives": ["alternative 1", "alternative 2"],
            "reason": "Why these work as alternatives"
        }}
    ],
    "serving_size_options": [1, 2, 4, 6, 8, 10, 12],
    "ai_insights": "Overall analysis and recommendations for this recipe"
}}
"""

        try:
            response = recipe_modifier.llm.invoke(prompt)
            suggestions = json.loads(response.content)
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to basic analysis if AI fails
            suggestions = {
                "dietary_modifications": [],
                "healthier_substitutions": [],
                "common_alternatives": [],
                "serving_size_options": [1, 2, 4, 6, 8, 10, 12],
                "ai_insights": "AI analysis temporarily unavailable. Basic suggestions provided."
            }
            
            # Basic analysis fallback
            for ingredient in ingredients_data:
                ing_name = ingredient.get('name', '').lower()
                if any(meat in ing_name for meat in ['chicken', 'beef', 'pork', 'fish', 'meat']):
                    suggestions["dietary_modifications"].append({
                        "type": "vegetarian",
                        "description": "Convert to vegetarian by substituting meat",
                        "affected_ingredients": [ingredient.get('name', '')],
                        "suggested_substitutes": ["tofu", "tempeh", "mushrooms"],
                        "cooking_adjustments": "Adjust cooking times for plant-based proteins"
                    })
        
        return suggestions
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get modification suggestions: {str(e)}")