from typing import Dict, Any, List, Optional, Tuple
from backend.app.schemas.schemas import (
    OptimizedRecipe, Ingredient, PrepStep, CookStep, 
    AvailableIngredient, IngredientSubstitution, RecipeModificationResponse
)
from langchain_openai import ChatOpenAI
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
class RecipeModifier:
    def __init__(self):
        # Use GPT-4 for sophisticated recipe analysis and modification
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.ingredient_llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    def modify_recipe(self, recipe: OptimizedRecipe, modification_request: Dict[str, Any]) -> RecipeModificationResponse:
        """
        Main method to modify a recipe based on available ingredients, serving size, and preferences.
        All substitutions and modifications are suggested by OpenAI, not a local database.
        """
        available_ingredients = modification_request.get("available_ingredients", [])
        target_servings = modification_request.get("target_servings")
        dietary_preferences = modification_request.get("dietary_preferences", [])
        substitution_preferences = modification_request.get("substitution_preferences", {})

        # Step 1: Ask OpenAI for missing ingredients and substitutions
        substitutions = self._find_substitutions_openai(
            recipe.ingredients,
            available_ingredients,
            dietary_preferences,
            substitution_preferences
        )

        # Step 2: Scale recipe if serving size changed
        scaling_factor = None
        if target_servings and recipe.servings:
            scaling_factor = target_servings / recipe.servings

        # Step 3: Generate modified recipe using OpenAI
        modified_recipe = self._generate_modified_recipe(
            recipe,
            substitutions,
            scaling_factor,
            dietary_preferences,
            available_ingredients
        )

        # Step 4: Create response
        return RecipeModificationResponse(
            modified_recipe=modified_recipe,
            substitutions_made=substitutions,
            scaling_applied={"factor": scaling_factor} if scaling_factor else None,
            modification_notes=self._generate_modification_notes(substitutions, scaling_factor, dietary_preferences),
            original_servings=recipe.servings or 1,
            new_servings=target_servings or recipe.servings or 1
        )

    def _find_substitutions_openai(self, recipe_ingredients: List[Ingredient],
                                   available_ingredients: List[AvailableIngredient],
                                   dietary_preferences: List[str],
                                   substitution_preferences: Dict[str, str]) -> List[IngredientSubstitution]:
        """
        Use OpenAI to suggest substitutions for missing ingredients.
        """
        prompt = self._create_substitution_prompt(
            recipe_ingredients,
            available_ingredients,
            dietary_preferences,
            substitution_preferences
        )
        response = self.ingredient_llm.invoke(prompt)
        try:
            data = json.loads(response.content)
            return [IngredientSubstitution(**sub) for sub in data.get("substitutions", [])]
        except Exception:
            return []

    def _create_substitution_prompt(self, recipe_ingredients, available_ingredients, dietary_preferences, substitution_preferences):
        """
        Create a prompt for OpenAI to suggest ingredient substitutions.
        """
        recipe_ings = "\n".join([f"- {ing.name} ({ing.amount or ''} {ing.unit or ''})" for ing in recipe_ingredients])
        available_ings = "\n".join([f"- {ing.name} ({ing.amount or ''} {ing.unit or ''})" for ing in available_ingredients])
        dietary = ", ".join(dietary_preferences) if dietary_preferences else "None"
        user_prefs = "\n".join([f"{k}: {v}" for k, v in substitution_preferences.items()]) if substitution_preferences else "None"

        return f"""
You are a culinary expert. Given the following recipe ingredients and available ingredients, suggest substitutions for any missing ingredients.
- Recipe Ingredients:
{recipe_ings}
- Available Ingredients:
{available_ings}
- Dietary Preferences: {dietary}
- User Substitution Preferences:
{user_prefs}

For each missing ingredient, suggest a substitution using only available ingredients and respecting dietary/user preferences.
Return a JSON list in this format:
{{
  "substitutions": [
    {{
      "original_name": "string",
      "original_amount": "string",
      "original_unit": "string",
      "substitute_name": "string",
      "substitute_amount": "string",
      "substitute_unit": "string",
      "substitution_reason": "string",
      "substitution_notes": "string"
    }}
  ]
}}
"""

    def _generate_modified_recipe(self, original_recipe: OptimizedRecipe,
                                  substitutions: List[IngredientSubstitution],
                                  scaling_factor: Optional[float],
                                  dietary_preferences: List[str],
                                  available_ingredients: List[AvailableIngredient]) -> OptimizedRecipe:
        """
        Use OpenAI to generate a modified recipe.
        """
        substitution_map = {sub.original_name: sub for sub in substitutions}
        prompt = self._create_modification_prompt(
            original_recipe, substitution_map, scaling_factor, dietary_preferences, available_ingredients
        )
        response = self.llm.invoke(prompt)
        try:
            modified_data = json.loads(response.content)
            return self._parse_modified_recipe(modified_data)
        except Exception:
            return self._manual_recipe_modification(original_recipe, substitutions, scaling_factor)

    def _create_modification_prompt(self, recipe: OptimizedRecipe,
                                    substitution_map: Dict[str, IngredientSubstitution],
                                    scaling_factor: Optional[float],
                                    dietary_preferences: List[str],
                                    available_ingredients: List[AvailableIngredient]) -> str:
        """
        Create prompt for AI recipe modification.
        """
        substitutions_text = "\n".join([
            f"- {sub.original_name} ({sub.original_amount} {sub.original_unit}) -> {sub.substitute_name} ({sub.substitute_amount} {sub.substitute_unit}) - {sub.substitution_reason}"
            for sub in substitution_map.values()
        ])
        available_text = "\n".join([
            f"- {ing.name} ({ing.amount} {ing.unit})" if ing.amount and ing.unit
            else f"- {ing.name}" for ing in available_ingredients
        ])
        scaling_text = f"Scale recipe from {recipe.servings} servings to {int(recipe.servings * scaling_factor)} servings" if scaling_factor else "Keep original serving size"

        return f"""
You are a professional chef and recipe modification expert. Modify this recipe based on the available ingredients and requirements.

ORIGINAL RECIPE:
Title: {recipe.title}
Servings: {recipe.servings}
Ingredients: {json.dumps([ing.dict() for ing in recipe.ingredients], indent=2)}
Prep Phase: {json.dumps([step.dict() for step in recipe.prep_phase], indent=2)}
Cook Phase: {json.dumps([step.dict() for step in recipe.cook_phase], indent=2)}

MODIFICATIONS REQUIRED:
1. Ingredient Substitutions:
{substitutions_text}

2. Available Ingredients:
{available_text}

3. Serving Size: {scaling_text}

4. Dietary Preferences: {', '.join(dietary_preferences) if dietary_preferences else 'None'}

INSTRUCTIONS:
1. Apply all ingredient substitutions listed above
2. Adjust cooking instructions to work with substituted ingredients
3. Scale all ingredient amounts proportionally if serving size changes
4. Modify prep and cooking steps to accommodate substitutions
5. Ensure the recipe maintains its core flavor profile and cooking method
6. Update timing estimates if needed
7. Add notes about any significant changes

Return the modified recipe in this exact JSON format:
{{
    "title": "Modified Recipe Title",
    "ingredients": [
        {{"name": "ingredient name", "amount": "quantity", "unit": "unit", "notes": "prep notes"}}
    ],
    "prep_phase": [
        {{"instruction": "prep task", "time_estimate": minutes, "category": "chopping/measuring/preheating/etc"}}
    ],
    "cook_phase": [
        {{"step_number": 1, "instruction": "cooking step", "time_estimate": minutes, "parallel_tasks": ["task1", "task2"]}}
    ],
    "total_time": total_minutes,
    "prep_time": prep_minutes,
    "cook_time": cook_minutes,
    "servings": number_of_servings,
    "difficulty": "easy/medium/hard"
}}
"""

    def _parse_modified_recipe(self, data: dict) -> OptimizedRecipe:
        """Parse AI response into OptimizedRecipe object"""
        ingredients = [Ingredient(**ing) for ing in data.get('ingredients', [])]
        prep_steps = [PrepStep(**step) for step in data.get('prep_phase', [])]
        cook_steps = [CookStep(**step) for step in data.get('cook_phase', [])]

        return OptimizedRecipe(
            title=data.get('title', 'Modified Recipe'),
            ingredients=ingredients,
            prep_phase=prep_steps,
            cook_phase=cook_steps,
            total_time=data.get('total_time'),
            prep_time=data.get('prep_time'),
            cook_time=data.get('cook_time'),
            servings=data.get('servings'),
            difficulty=data.get('difficulty')
        )

    def _manual_recipe_modification(self, original_recipe: OptimizedRecipe,
                                    substitutions: List[IngredientSubstitution],
                                    scaling_factor: Optional[float]) -> OptimizedRecipe:
        """
        Fallback manual recipe modification (if OpenAI fails).
        """
        substitution_map = {sub.original_name: sub for sub in substitutions}
        modified_ingredients = []
        for ingredient in original_recipe.ingredients:
            if ingredient.name in substitution_map:
                sub = substitution_map[ingredient.name]
                modified_ingredients.append(Ingredient(
                    name=sub.substitute_name,
                    amount=sub.substitute_amount,
                    unit=sub.substitute_unit,
                    notes=f"Substituted for {ingredient.name}"
                ))
            else:
                if scaling_factor and ingredient.amount:
                    try:
                        amount = float(re.findall(r'\d+\.?\d*', ingredient.amount)[0])
                        scaled_amount = amount * scaling_factor
                        modified_ingredients.append(Ingredient(
                            name=ingredient.name,
                            amount=str(scaled_amount),
                            unit=ingredient.unit,
                            notes=ingredient.notes
                        ))
                    except:
                        modified_ingredients.append(ingredient)
                else:
                    modified_ingredients.append(ingredient)

        modified_prep_steps = []
        for step in original_recipe.prep_phase:
            modified_instruction = step.instruction
            for sub in substitutions:
                modified_instruction = modified_instruction.replace(
                    sub.original_name, sub.substitute_name
                )
            modified_prep_steps.append(PrepStep(
                instruction=modified_instruction,
                time_estimate=step.time_estimate,
                category=step.category
            ))

        modified_cook_steps = []
        for step in original_recipe.cook_phase:
            modified_instruction = step.instruction
            for sub in substitutions:
                modified_instruction = modified_instruction.replace(
                    sub.original_name, sub.substitute_name
                )
            modified_cook_steps.append(CookStep(
                step_number=step.step_number,
                instruction=modified_instruction,
                time_estimate=step.time_estimate,
                parallel_tasks=step.parallel_tasks
            ))

        new_servings = int(original_recipe.servings * scaling_factor) if scaling_factor else original_recipe.servings

        return OptimizedRecipe(
            title=f"Modified {original_recipe.title}",
            ingredients=modified_ingredients,
            prep_phase=modified_prep_steps,
            cook_phase=modified_cook_steps,
            total_time=original_recipe.total_time,
            prep_time=original_recipe.prep_time,
            cook_time=original_recipe.cook_time,
            servings=new_servings,
            difficulty=original_recipe.difficulty
        )

    def _generate_modification_notes(self, substitutions: List[IngredientSubstitution],
                                     scaling_factor: Optional[float],
                                     dietary_preferences: List[str]) -> str:
        """Generate human-readable notes about modifications"""
        notes = []
        if substitutions:
            notes.append(f"Made {len(substitutions)} ingredient substitutions:")
            for sub in substitutions:
                notes.append(f"- {sub.original_name} → {sub.substitute_name} ({sub.substitution_reason})")
        if scaling_factor:
            notes.append(f"Scaled recipe by factor of {scaling_factor:.2f}")
        if dietary_preferences:
            notes.append(f"Applied dietary preferences: {', '.join(dietary_preferences)}")
        return "\n".join(notes) if notes else "No modifications applied"

    def adjust_recipe_for_dietary_needs(self, recipe: OptimizedRecipe, dietary_preference: str, servings: int = None) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility - now uses the main modify_recipe method
        """
        modification_request = {
            "available_ingredients": [],
            "target_servings": servings,
            "dietary_preferences": [dietary_preference],
            "substitution_preferences": {}
        }
        result = self.modify_recipe(recipe, modification_request)
        return {
            "adjusted_ingredients": [
                {
                    "name": ing.name,
                    "amount": ing.amount,
                    "unit": ing.unit,
                    "substitution_note": ing.notes
                } for ing in result.modified_recipe.ingredients
            ],
            "dietary_notes": result.modification_notes,
            "serving_size": result.new_servings
        }
