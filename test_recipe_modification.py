#!/usr/bin/env python3
"""
Test script for the AI-heavy recipe modification functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.agents.recipe_modifier import RecipeModifier
from backend.app.schemas.schemas import (
    OptimizedRecipe, Ingredient, PrepStep, CookStep, 
    AvailableIngredient, RecipeModificationResponse
)

def test_ai_recipe_modification():
    """Test the AI-powered recipe modification functionality"""
    
    print("Testing AI-Heavy Recipe Modification System")
    print("=" * 60)
    
    # Create a sample recipe
    sample_recipe = OptimizedRecipe(
        title="Classic Beef Stir Fry",
        ingredients=[
            Ingredient(name="beef sirloin", amount="1", unit="lb", notes="cut into strips"),
            Ingredient(name="soy sauce", amount="3", unit="tbsp", notes=""),
            Ingredient(name="garlic", amount="4", unit="cloves", notes="minced"),
            Ingredient(name="ginger", amount="1", unit="tbsp", notes="fresh, grated"),
            Ingredient(name="onion", amount="1", unit="medium", notes="sliced"),
            Ingredient(name="bell pepper", amount="2", unit="large", notes="sliced"),
            Ingredient(name="vegetable oil", amount="2", unit="tbsp", notes=""),
            Ingredient(name="cornstarch", amount="1", unit="tbsp", notes="for thickening")
        ],
        prep_phase=[
            PrepStep(instruction="Cut beef into thin strips", time_estimate=8, category="chopping"),
            PrepStep(instruction="Mince garlic and grate ginger", time_estimate=3, category="chopping"),
            PrepStep(instruction="Slice onion and bell peppers", time_estimate=5, category="chopping"),
            PrepStep(instruction="Mix soy sauce with cornstarch", time_estimate=2, category="measuring")
        ],
        cook_phase=[
            CookStep(step_number=1, instruction="Heat oil in wok, add beef and cook until browned", time_estimate=6, parallel_tasks=[]),
            CookStep(step_number=2, instruction="Add garlic and ginger, stir fry for 1 minute", time_estimate=1, parallel_tasks=[]),
            CookStep(step_number=3, instruction="Add vegetables and cook until tender-crisp", time_estimate=4, parallel_tasks=[]),
            CookStep(step_number=4, instruction="Add soy sauce mixture and cook until thickened", time_estimate=2, parallel_tasks=[])
        ],
        total_time=25,
        prep_time=18,
        cook_time=13,
        servings=4,
        difficulty="medium"
    )
    
    # Create available ingredients (missing beef, have tofu instead)
    available_ingredients = [
        AvailableIngredient(name="extra firm tofu", amount="1", unit="lb", notes="pressed and cubed"),
        AvailableIngredient(name="soy sauce", amount="1", unit="bottle", notes=""),
        AvailableIngredient(name="garlic", amount="1", unit="bulb", notes=""),
        AvailableIngredient(name="fresh ginger", amount="1", unit="piece", notes=""),
        AvailableIngredient(name="onion", amount="2", unit="medium", notes=""),
        AvailableIngredient(name="bell pepper", amount="3", unit="large", notes=""),
        AvailableIngredient(name="sesame oil", amount="1", unit="bottle", notes=""),
        AvailableIngredient(name="cornstarch", amount="1", unit="box", notes=""),
        AvailableIngredient(name="mushrooms", amount="8", unit="oz", notes="shiitake")
    ]
    
    # Create modification request
    modification_request = {
        "available_ingredients": available_ingredients,
        "target_servings": 6,  # Scale up from 4 to 6 servings
        "dietary_preferences": ["vegetarian", "healthier"],
        "substitution_preferences": {"beef": "tofu", "vegetable oil": "sesame oil"}
    }
    
    try:
        modifier = RecipeModifier()
        
        print(f"Original Recipe: {sample_recipe.title}")
        print(f"Original Servings: {sample_recipe.servings}")
        print(f"Original Ingredients: {len(sample_recipe.ingredients)}")
        print(f"Total Time: {sample_recipe.total_time} minutes")
        print()
        
        print("Processing AI-powered modifications...")
        print("-" * 40)
        
        # Modify the recipe using AI
        result = modifier.modify_recipe(sample_recipe, modification_request)
        
        print("AI MODIFICATION RESULTS:")
        print("=" * 30)
        print(f"Modified Recipe: {result.modified_recipe.title}")
        print(f"New Servings: {result.new_servings}")
        print(f"Scaling Factor: {result.scaling_applied['factor']:.2f}" if result.scaling_applied else "No scaling")
        print()
        
        print("AI-POWERED SUBSTITUTIONS:")
        print("-" * 25)
        for i, sub in enumerate(result.substitutions_made, 1):
            print(f"{i}. {sub.original_name} ({sub.original_amount} {sub.original_unit})")
            print(f"   -> {sub.substitute_name} ({sub.substitute_amount} {sub.substitute_unit})")
            print(f"   AI Reason: {sub.substitution_reason}")
            if sub.substitution_notes:
                print(f"   Notes: {sub.substitution_notes}")
            print()
        
        print("AI-GENERATED MODIFICATION SUMMARY:")
        print("-" * 35)
        print(result.modification_notes)
        print()
        
        print("MODIFIED INGREDIENTS (AI-OPTIMIZED):")
        print("-" * 35)
        for ing in result.modified_recipe.ingredients:
            print(f"• {ing.name}: {ing.amount} {ing.unit}")
            if ing.notes:
                print(f"  {ing.notes}")
        print()
        
        print("MODIFIED PREP STEPS (AI-ADJUSTED):")
        print("-" * 30)
        for step in result.modified_recipe.prep_phase:
            print(f"• {step.instruction} ({step.time_estimate} min)")
        print()
        
        print("MODIFIED COOK STEPS (AI-OPTIMIZED):")
        print("-" * 30)
        for step in result.modified_recipe.cook_phase:
            print(f"{step.step_number}. {step.instruction} ({step.time_estimate} min)")
        print()
        
        print("UPDATED TIMING:")
        print("-" * 15)
        print(f"Total Time: {result.modified_recipe.total_time} minutes")
        print(f"Prep Time: {result.modified_recipe.prep_time} minutes")
        print(f"Cook Time: {result.modified_recipe.cook_time} minutes")
        print()
        
        print("AI ANALYSIS COMPLETE!")
        print("All modifications applied successfully using AI intelligence")
        
    except Exception as e:
        print(f"Error during AI recipe modification: {str(e)}")
        import traceback
        traceback.print_exc()

def test_ai_ingredient_analysis():
    """Test AI-powered ingredient analysis"""
    
    print("\nTesting AI-Powered Ingredient Analysis")
    print("=" * 40)
    
    modifier = RecipeModifier()
    
    # Test AI substitution analysis
    recipe_ingredients = [
        Ingredient(name="chicken breast", amount="1", unit="lb"),
        Ingredient(name="heavy cream", amount="1", unit="cup"),
        Ingredient(name="butter", amount="2", unit="tbsp"),
        Ingredient(name="all-purpose flour", amount="1", unit="cup")
    ]
    
    available_ingredients = [
        AvailableIngredient(name="extra firm tofu", amount="1", unit="lb"),
        AvailableIngredient(name="coconut cream", amount="1", unit="can"),
        AvailableIngredient(name="olive oil", amount="1", unit="bottle"),
        AvailableIngredient(name="almond flour", amount="1", unit="bag")
    ]
    
    print("Analyzing ingredients with AI...")
    
    try:
        substitutions = modifier._ai_analyze_and_suggest_substitutions(
            OptimizedRecipe(
                title="Test Recipe",
                ingredients=recipe_ingredients,
                prep_phase=[],
                cook_phase=[],
                servings=4
            ),
            available_ingredients,
            ["vegan", "gluten-free"],
            {"chicken": "tofu", "butter": "olive oil"}
        )
        
        print("AI SUBSTITUTION ANALYSIS:")
        print("-" * 25)
        for sub in substitutions:
            print(f"{sub.original_name} -> {sub.substitute_name}")
            print(f"   AI Reasoning: {sub.substitution_reason}")
            print(f"   Amount: {sub.substitute_amount} {sub.substitute_unit}")
            if sub.substitution_notes:
                print(f"   Notes: {sub.substitution_notes}")
            print()
        
        print("AI ingredient analysis test completed!")
        
    except Exception as e:
        print(f"Error during AI ingredient analysis: {str(e)}")

if __name__ == "__main__":
    test_ai_recipe_modification()
    test_ai_ingredient_analysis()
