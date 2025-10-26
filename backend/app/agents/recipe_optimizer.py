from langchain_openai import ChatOpenAI
from backend.app.schemas.schemas import OptimizedRecipe, Ingredient, PrepStep, CookStep
import json
import os
from dotenv import load_dotenv

load_dotenv()

class RecipeOptimizer:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def optimize_recipe(self, scraped_data: dict) -> OptimizedRecipe:
        """
        Transform a scraped recipe into an optimized prep-first workflow for Prep Pad
        """
        # Create the optimization prompt
        prompt = self._create_optimization_prompt(scraped_data)
        
        # Get AI response
        response = self.llm.invoke(prompt)
        
        # Parse the response into structured data
        try:
            optimized_data = json.loads(response.content)
            return self._parse_optimized_recipe(optimized_data)
        except json.JSONDecodeError:
            # Fallback parsing if JSON parsing fails
            return self._fallback_parse(response.content, scraped_data)
    
    def _create_optimization_prompt(self, scraped_data: dict) -> str:
        """Create the prompt for recipe optimization"""
        return f"""
You are a professional chef and cooking workflow expert. Your task is to transform this recipe into a "mise-en-place" (everything in its place) optimized workflow.

Original Recipe:
Title: {scraped_data.get('title', 'Untitled')}
Ingredients: {json.dumps(scraped_data.get('ingredients', []), indent=2)}
Instructions: {json.dumps(scraped_data.get('instructions', []), indent=2)}
Servings: {scraped_data.get('servings', 'unknown')}

Your job is to:
1. Parse and clean the ingredients list
2. Adjust ingredient quantities and instructions if the ingredients or serving size have changed
3. Create a "Prep Phase" with all preparation tasks that can be done ahead of time
4. Create a "Cook Phase" with optimized cooking steps that can be done in parallel where possible
5. Estimate timing for each step
6. Identify parallel tasks

Return your response as a JSON object with this exact structure:
{{
    "title": "Recipe Title",
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

Guidelines:
- Group prep tasks by type (chopping, measuring, preheating)
- Identify what can be done in parallel during cooking
- Be specific about timing estimates
- Make instructions clear and actionable
- Consider mise-en-place principles (prep everything before cooking)
- If the ingredients or serving size have changed, update the recipe accordingly
"""
    
    def _parse_optimized_recipe(self, data: dict) -> OptimizedRecipe:
        """Parse the AI response into OptimizedRecipe object"""
        ingredients = [Ingredient(**ing) for ing in data.get('ingredients', [])]
        prep_steps = [PrepStep(**step) for step in data.get('prep_phase', [])]
        cook_steps = [CookStep(**step) for step in data.get('cook_phase', [])]
        
        return OptimizedRecipe(
            title=data.get('title', 'Optimized Recipe'),
            ingredients=ingredients,
            prep_phase=prep_steps,
            cook_phase=cook_steps,
            total_time=data.get('total_time'),
            prep_time=data.get('prep_time'),
            cook_time=data.get('cook_time'),
            servings=data.get('servings'),
            difficulty=data.get('difficulty')
        )
    
    def _fallback_parse(self, content: str, scraped_data: dict) -> OptimizedRecipe:
        """Fallback parsing if JSON parsing fails"""
        # Simple fallback - create basic structure
        ingredients = [Ingredient(name=ing, amount="", unit="", notes="") 
                     for ing in scraped_data.get('ingredients', [])]
        
        prep_steps = [PrepStep(instruction="Prepare all ingredients", time_estimate=15, category="general")]
        
        cook_steps = [CookStep(step_number=1, instruction="Follow original recipe steps", 
                              time_estimate=30, parallel_tasks=[])]
        
        return OptimizedRecipe(
            title=scraped_data.get('title', 'Optimized Recipe'),
            ingredients=ingredients,
            prep_phase=prep_steps,
            cook_phase=cook_steps,
            total_time=45,
            prep_time=15,
            cook_time=30,
            servings=scraped_data.get('servings', 4),
            difficulty="medium"
        )
