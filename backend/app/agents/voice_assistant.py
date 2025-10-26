from langchain_openai import ChatOpenAI
from backend.app.schemas.schemas import OptimizedRecipe, PrepStep, CookStep
from backend.app.models.models import CookingSession
from sqlmodel import Session, select
import os
import re
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from .recipe_modifier import RecipeModifier

load_dotenv()

class VoiceCookingAssistant:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.recipe_modifier = RecipeModifier()
    
    def _process_voice_command(self, command: str, session: CookingSession, 
                            recipe: OptimizedRecipe, db: Session) -> Dict[str, Any]:
        """
        Process voice commands and return appropriate responses
        """
        command = command.lower().strip()
        
        if command in ['next', 'next step', 'continue']:
            return self._handle_next_step(session, recipe, db)
        elif command in ['repeat', 'say again', 'repeat step']:
            return self._handle_repeat_step(session, recipe)
        elif command in ['what prep', 'prep', 'preparation']:
            return self._handle_prep_query(session, recipe)
        elif command in ['pause', 'stop']:
            return self._handle_pause(session, db)
        elif command in ['resume', 'continue cooking']:
            return self._handle_resume(session, db)
        elif command in ['time', 'how long', 'time left']:
            return self._handle_time_query(session, recipe)
        elif command in ['timer info', 'timer help']:
            return self._handle_timer_info(session, recipe)
        elif command in ['start timer', 'begin timer']:
            return self._handle_start_timer(session, recipe)
        elif command in ['pause timer', 'stop timer']:
            return self._handle_pause_timer(session)
        elif command in ['resume timer', 'restart timer', 'continue timer']:
            return self._handle_resume_timer(session)
        elif command in ['ingredients', 'what ingredients']:
            return self._handle_ingredients_query(recipe)
        elif command in ['make vegetarian', 'vegetarian version', 'make it vegetarian', 'vegetarian']:
            return self._handle_make_vegetarian(session, recipe, db)
        elif command in ['make vegan', 'vegan version', 'make it vegan', 'vegan']:
            return self._handle_make_vegan(session, recipe, db)
        elif command in ['make gluten free', 'gluten free version', 'make it gluten free', 'gluten free', 'gluten-free']:
            return self._handle_make_gluten_free(session, recipe, db)
        elif command in ['make dairy free', 'dairy free version', 'make it dairy free', 'dairy free', 'dairy-free']:
            return self._handle_make_dairy_free(session, recipe, db)
        elif command in ['scale up', 'double recipe', 'make more']:
            return self._handle_scale_recipe(session, recipe, db, 2.0)
        elif command in ['scale down', 'half recipe', 'make less']:
            return self._handle_scale_recipe(session, recipe, db, 0.5)
        elif command in ['substitute', 'replace ingredient', 'swap ingredient']:
            return self._handle_substitute_ingredient(session, recipe, db)
        else:
            return self._handle_unknown_command(command)
    
    def _handle_next_step(self, session: CookingSession, recipe: OptimizedRecipe, db: Session) -> Dict[str, Any]:
        """Move to the next step in the cooking process"""
        # Check if recipe has data
        if not recipe.prep_phase and not recipe.cook_phase:
            return {
                "response": "No recipe steps available. Please parse a recipe first.",
                "current_step": session.current_step,
                "current_phase": session.current_phase,
                "is_complete": False
            }
        
        if session.current_phase == 'prep' and recipe.prep_phase:
            # Find current prep step and move to next
            current_prep_index = self._get_current_prep_index(session, recipe)
            if current_prep_index < len(recipe.prep_phase) - 1:
                next_prep_index = current_prep_index + 1
                session.current_step = recipe.prep_phase[next_prep_index].instruction
                timer_info = self._enhance_step_with_timer_info(session.current_step)
                response_text = f"Next prep step: {session.current_step}"
                if timer_info["has_timer"]:
                    response_text += f" {timer_info['timer_message']}"
            else:
                # Move to cooking phase
                session.current_phase = 'cook'
                if recipe.cook_phase and len(recipe.cook_phase) > 0:
                    session.current_step = recipe.cook_phase[0].instruction
                    timer_info = self._enhance_step_with_timer_info(session.current_step)
                    response_text = f"Prep complete! Starting cooking phase. Step 1: {session.current_step}"
                    if timer_info["has_timer"]:
                        response_text += f" {timer_info['timer_message']}"
                else:
                    session.is_active = False
                    response_text = "Prep complete! No cooking steps available."
        elif session.current_phase == 'cook' and recipe.cook_phase:
            # Handle cooking steps
            current_cook_index = self._get_current_cook_index(session, recipe)
            if current_cook_index < len(recipe.cook_phase) - 1:
                next_cook_index = current_cook_index + 1
                session.current_step = recipe.cook_phase[next_cook_index].instruction
                timer_info = self._enhance_step_with_timer_info(session.current_step)
                response_text = f"Step {next_cook_index + 1}: {session.current_step}"
                if timer_info["has_timer"]:
                    response_text += f" {timer_info['timer_message']}"
            else:
                # Recipe complete
                session.is_active = False
                response_text = "Congratulations! Your recipe is complete. Enjoy your meal!"
        else:
            response_text = "No more steps available in this phase."
        
        db.commit()
        return {
            "response": response_text,
            "current_step": session.current_step,
            "current_phase": session.current_phase,
            "is_complete": not session.is_active
        }
    
    def _handle_repeat_step(self, session: CookingSession, recipe: OptimizedRecipe) -> Dict[str, Any]:
        """Repeat the current step"""
        if session.current_step:
            response_text = f"Repeating: {session.current_step}"
        else:
            response_text = "No current step to repeat."
        
        return {
            "response": response_text,
            "current_step": session.current_step,
            "current_phase": session.current_phase
        }
    
    def _handle_prep_query(self, session: CookingSession, recipe: OptimizedRecipe) -> Dict[str, Any]:
        """Provide prep phase information"""
        prep_text = "Prep phase includes: "
        prep_list = [step.instruction for step in recipe.prep_phase]
        prep_text += "; ".join(prep_list)
        
        return {
            "response": prep_text,
            "prep_steps": prep_list,
            "current_phase": session.current_phase
        }
    
    def _handle_pause(self, session: CookingSession, db: Session) -> Dict[str, Any]:
        """Pause the cooking session"""
        session.is_active = False
        db.commit()
        
        return {
            "response": "Cooking session paused. Say 'resume' when ready to continue.",
            "is_active": False
        }
    
    def _handle_resume(self, session: CookingSession, db: Session) -> Dict[str, Any]:
        """Resume the cooking session"""
        session.is_active = True
        db.commit()
        
        return {
            "response": f"Resuming cooking. Current step: {session.current_step}",
            "is_active": True,
            "current_step": session.current_step
        }
    
    def _handle_time_query(self, session: CookingSession, recipe: OptimizedRecipe) -> Dict[str, Any]:
        """Provide timing information"""
        if session.current_phase == 'prep':
            remaining_prep = self._calculate_remaining_prep_time(session, recipe)
            response_text = f"Prep phase: {remaining_prep} minutes remaining"
        else:
            remaining_cook = self._calculate_remaining_cook_time(session, recipe)
            response_text = f"Cooking phase: {remaining_cook} minutes remaining"
        
        return {
            "response": response_text,
            "current_phase": session.current_phase
        }
    
    def _handle_ingredients_query(self, recipe: OptimizedRecipe) -> Dict[str, Any]:
        """List all ingredients"""
        ingredients_text = "Ingredients needed: "
        ingredients_list = [f"{ing.amount} {ing.unit} {ing.name}" for ing in recipe.ingredients]
        ingredients_text += "; ".join(ingredients_list)
        
        return {
            "response": ingredients_text,
            "ingredients": ingredients_list
        }
    
    def _handle_timer_info(self, session: CookingSession, recipe: OptimizedRecipe) -> Dict[str, Any]:
        """Provide timer information for the current step"""
        timer_info = self._enhance_step_with_timer_info(session.current_step)
        
        if timer_info["has_timer"]:
            response_text = timer_info["timer_message"]
        else:
            response_text = "The current step doesn't require a timer. If you need to time something manually, you can use your own timer or ask me to help with timing."
        
        return {
            "response": response_text,
            "timer_info": timer_info,
            "current_step": session.current_step,
            "current_phase": session.current_phase
        }
    
    def _handle_start_timer(self, session: CookingSession, recipe: OptimizedRecipe) -> Dict[str, Any]:
        """Start the timer for the current step if applicable"""
        timer_info = self._enhance_step_with_timer_info(session.current_step)
        
        if timer_info["has_timer"]:
            timer_minutes = timer_info["timer_minutes"]
            response_text = f"Starting timer for {timer_minutes} minute{'s' if timer_minutes != 1 else ''}. The timer is now running on your screen."
        else:
            response_text = "The current step doesn't have a timer requirement. You can start the timer manually from the timer component."
        
        return {
            "response": response_text,
            "timer_info": timer_info,
            "should_start_timer": timer_info["has_timer"],
            "current_step": session.current_step,
            "current_phase": session.current_phase
        }
    
    def _handle_pause_timer(self, session: CookingSession) -> Dict[str, Any]:
        """Pause the timer"""
        return {
            "response": "Timer paused. Say 'resume timer' to continue.",
            "should_pause_timer": True,
            "current_step": session.current_step,
            "current_phase": session.current_phase
        }
    
    def _handle_resume_timer(self, session: CookingSession) -> Dict[str, Any]:
        """Resume the timer"""
        return {
            "response": "Timer resumed. You can control the timer manually from the screen.",
            "should_resume_timer": True,
            "current_step": session.current_step,
            "current_phase": session.current_phase
        }

    def _handle_ingredient_removal(self, recipe: OptimizedRecipe, ingredient_name: str, db: Session) -> Dict[str, Any]:
        """
        Use OpenAI to analyze the impact of removing an ingredient and suggest replacements or adjustments.
        """
        # Compose a prompt for OpenAI
        prompt = (
            f"You are a cooking assistant. The user wants to remove '{ingredient_name}' from this recipe:\n"
            f"Ingredients: {[f'{ing.amount} {ing.unit} {ing.name}' for ing in recipe.ingredients]}\n"
            f"Instructions: {[step.instruction for step in recipe.prep_phase + recipe.cook_phase]}\n"
            "What will happen to the recipe if this ingredient is removed? Suggest any replacements or adjustments needed. "
            "Also, mention if the servings or outcome will be affected."
        )
        # Get response from OpenAI
        response = self.llm.invoke(prompt)
        return {
            "response": response.content,
            "voice": True  # Indicate this should be read aloud
        }

    def process_voice_command(self, command: str, session: CookingSession, 
        recipe: OptimizedRecipe, db: Session) -> Dict[str, Any]:
        command_lower = command.lower().strip()

        # Ingredient removal intent
        remove_match = re.search(r'remove (.+?)(?: from|$)', command_lower)
        if remove_match:
            ingredient_name = remove_match.group(1).strip()
            return self._handle_ingredient_removal(recipe, ingredient_name, db)

        # Handle dietary adjustments using new methods
        if any(keyword in command_lower for keyword in ['vegan', 'vegetarian', 'gluten-free', 'dairy-free']):
            if 'vegan' in command_lower:
                return self._handle_make_vegan(session, recipe, db)
            elif 'vegetarian' in command_lower:
                return self._handle_make_vegetarian(session, recipe, db)
            elif 'gluten-free' in command_lower or 'gluten free' in command_lower:
                return self._handle_make_gluten_free(session, recipe, db)
            elif 'dairy-free' in command_lower or 'dairy free' in command_lower:
                return self._handle_make_dairy_free(session, recipe, db)

        # Check for serving size adjustments
        elif any(keyword in command_lower for keyword in ['adjust', 'change', 'scale', 'serving', 'double', 'half']):
            return self._handle_serving_adjustment(recipe, command, db)

        # Handle existing commands
        else:
            return self._process_voice_command(command, session, recipe, db)
    
    def _handle_unknown_command(self, command: str) -> Dict[str, Any]:
        """Handle unknown commands"""
        return {
            "response": f"I didn't understand '{command}'. Try saying 'next', 'repeat', 'what prep', 'pause', 'resume', 'start timer', 'pause timer', 'resume timer', or 'timer info'.",
            "suggestions": ["next", "repeat", "what prep", "pause", "resume", "time", "ingredients", "timer info", "start timer", "pause timer", "resume timer"]
        }
    
    def _get_current_prep_index(self, session: CookingSession, recipe: OptimizedRecipe) -> int:
        """Get the current prep step index"""
        if not session.current_step or not recipe.prep_phase:
            return 0
        
        for i, step in enumerate(recipe.prep_phase):
            if step.instruction == session.current_step:
                return i
        return 0
    
    def _get_current_cook_index(self, session: CookingSession, recipe: OptimizedRecipe) -> int:
        """Get the current cooking step index"""
        if not session.current_step or not recipe.cook_phase:
            return 0
        
        for i, step in enumerate(recipe.cook_phase):
            if step.instruction == session.current_step:
                return i
        return 0
    
    def _calculate_remaining_prep_time(self, session: CookingSession, recipe: OptimizedRecipe) -> int:
        """Calculate remaining prep time"""
        if not recipe.prep_phase:
            return 0
        current_index = self._get_current_prep_index(session, recipe)
        remaining_steps = recipe.prep_phase[current_index:]
        return sum(step.time_estimate or 0 for step in remaining_steps)
    
    def _calculate_remaining_cook_time(self, session: CookingSession, recipe: OptimizedRecipe) -> int:
        """Calculate remaining cooking time"""
        if not recipe.cook_phase:
            return 0
        current_index = self._get_current_cook_index(session, recipe)
        remaining_steps = recipe.cook_phase[current_index:]
        return sum(step.time_estimate or 0 for step in remaining_steps)
    
    def _detect_timer_in_instruction(self, instruction: str) -> Optional[int]:
        """Detect if instruction contains a timer and return the time in minutes"""
        # Regex patterns to detect time mentions in instructions
        time_patterns = [
            r'(\d+)\s*minutes?',
            r'(\d+)\s*mins?',
            r'(\d+)\s*min',
            r'for\s*(\d+)\s*minutes?',
            r'cook\s*for\s*(\d+)\s*minutes?',
            r'bake\s*for\s*(\d+)\s*minutes?',
            r'simmer\s*for\s*(\d+)\s*minutes?',
            r'boil\s*for\s*(\d+)\s*minutes?',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                time_str = match.group(1)
                if time_str:
                    time = int(time_str)
                    if 0 < time <= 300:  # Reasonable cooking time range (0-5 hours)
                        return time
        return None
    
    def _enhance_step_with_timer_info(self, instruction: str) -> Dict[str, Any]:
        """Enhance step information with timer detection"""
        timer_minutes = self._detect_timer_in_instruction(instruction)
        
        result = {
            "instruction": instruction,
            "has_timer": timer_minutes is not None,
        }
        
        if timer_minutes:
            result["timer_minutes"] = timer_minutes
            result["timer_message"] = f"This step requires {timer_minutes} minute{'s' if timer_minutes != 1 else ''}. A timer will be available to help you track the time."
        
        return result

    def _handle_dietary_adjustment(self, recipe: OptimizedRecipe, dietary_pref: str, servings: Optional[int], db: Session) -> Dict[str, Any]:
        """Handle dietary preference adjustments"""
        # Get adjusted recipe from the recipe modifier
        adjusted_data = self.recipe_modifier.adjust_recipe_for_dietary_needs(recipe, dietary_pref, servings)
        
        # Apply the adjustments to the recipe
        updated_recipe = self.apply_adjusted_recipe(recipe, adjusted_data)
        
        # Prepare response
        response_text = f"Recipe adjusted for {dietary_pref}"
        if servings:
            response_text += f" and scaled to {servings} servings"
        
        # If there are substitution notes, add them to the response
        substitution_notes = [ing.get('substitution_note') for ing in adjusted_data['adjusted_ingredients'] if ing.get('substitution_note')]
        if substitution_notes:
            response_text += ". Notes: " + "; ".join(substitution_notes)
        
        return {
            "response": response_text,
            "recipe": updated_recipe,
            "dietary_notes": adjusted_data.get('dietary_notes', ""),
            "success": True
        }

    def _handle_make_vegetarian(self, session: CookingSession, recipe: OptimizedRecipe, db: Session) -> Dict[str, Any]:
        """Create a vegetarian version of the current recipe"""
        try:
            modification_request = {
                "available_ingredients": [],
                "target_servings": recipe.servings,
                "dietary_preferences": ["vegetarian"],
                "substitution_preferences": {}
            }
            
            modification_result = self.recipe_modifier.modify_recipe(recipe, modification_request)
            
            # Save the modified recipe as a new recipe
            new_recipe_id = self._save_modified_recipe(modification_result.modified_recipe, db, "vegetarian")
            
            return {
                "response": f"I've created a vegetarian version of {recipe.title}. The new recipe has been saved.",
                "new_recipe_id": new_recipe_id,
                "modified_recipe": modification_result.modified_recipe,
                "modification_notes": modification_result.modification_notes,
                "success": True
            }
        except Exception as e:
            return {
                "response": f"Sorry, I couldn't create a vegetarian version: {str(e)}",
                "success": False
            }
    
    def _handle_make_vegan(self, session: CookingSession, recipe: OptimizedRecipe, db: Session) -> Dict[str, Any]:
        """Create a vegan version of the current recipe"""
        try:
            modification_request = {
                "available_ingredients": [],
                "target_servings": recipe.servings,
                "dietary_preferences": ["vegan"],
                "substitution_preferences": {}
            }
            
            modification_result = self.recipe_modifier.modify_recipe(recipe, modification_request)
            
            # Save the modified recipe as a new recipe
            new_recipe_id = self._save_modified_recipe(modification_result.modified_recipe, db, "vegan")
            
            return {
                "response": f"I've created a vegan version of {recipe.title}. The new recipe has been saved with ID {new_recipe_id}.",
                "new_recipe_id": new_recipe_id,
                "modified_recipe": modification_result.modified_recipe,
                "modification_notes": modification_result.modification_notes,
                "success": True
            }
        except Exception as e:
            return {
                "response": f"Sorry, I couldn't create a vegan version: {str(e)}",
                "success": False
            }
    
    def _handle_make_gluten_free(self, session: CookingSession, recipe: OptimizedRecipe, db: Session) -> Dict[str, Any]:
        """Create a gluten-free version of the current recipe"""
        try:
            modification_request = {
                "available_ingredients": [],
                "target_servings": recipe.servings,
                "dietary_preferences": ["gluten-free"],
                "substitution_preferences": {}
            }
            
            modification_result = self.recipe_modifier.modify_recipe(recipe, modification_request)
            
            # Save the modified recipe as a new recipe
            new_recipe_id = self._save_modified_recipe(modification_result.modified_recipe, db, "gluten-free")
            
            return {
                "response": f"I've created a gluten-free version of {recipe.title}. The new recipe has been saved with ID {new_recipe_id}.",
                "new_recipe_id": new_recipe_id,
                "modified_recipe": modification_result.modified_recipe,
                "modification_notes": modification_result.modification_notes,
                "success": True
            }
        except Exception as e:
            return {
                "response": f"Sorry, I couldn't create a gluten-free version: {str(e)}",
                "success": False
            }
    
    def _handle_make_dairy_free(self, session: CookingSession, recipe: OptimizedRecipe, db: Session) -> Dict[str, Any]:
        """Create a dairy-free version of the current recipe"""
        try:
            modification_request = {
                "available_ingredients": [],
                "target_servings": recipe.servings,
                "dietary_preferences": ["dairy-free"],
                "substitution_preferences": {}
            }
            
            modification_result = self.recipe_modifier.modify_recipe(recipe, modification_request)
            
            # Save the modified recipe as a new recipe
            new_recipe_id = self._save_modified_recipe(modification_result.modified_recipe, db, "dairy-free")
            
            return {
                "response": f"I've created a dairy-free version of {recipe.title}. The new recipe has been saved with ID {new_recipe_id}.",
                "new_recipe_id": new_recipe_id,
                "modified_recipe": modification_result.modified_recipe,
                "modification_notes": modification_result.modification_notes,
                "success": True
            }
        except Exception as e:
            return {
                "response": f"Sorry, I couldn't create a dairy-free version: {str(e)}",
                "success": False
            }
    
    def _handle_scale_recipe(self, session: CookingSession, recipe: OptimizedRecipe, db: Session, scale_factor: float) -> Dict[str, Any]:
        """Scale the recipe up or down"""
        try:
            new_servings = int(recipe.servings * scale_factor) if recipe.servings else int(4 * scale_factor)
            
            modification_request = {
                "available_ingredients": [],
                "target_servings": new_servings,
                "dietary_preferences": [],
                "substitution_preferences": {}
            }
            
            modification_result = self.recipe_modifier.modify_recipe(recipe, modification_request)
            
            # Save the modified recipe as a new recipe
            new_recipe_id = self._save_modified_recipe(modification_result.modified_recipe, db, f"scaled_{scale_factor}x")
            
            return {
                "response": f"I've scaled the recipe to {new_servings} servings. The new recipe has been saved with ID {new_recipe_id}.",
                "new_recipe_id": new_recipe_id,
                "modified_recipe": modification_result.modified_recipe,
                "modification_notes": modification_result.modification_notes,
                "success": True
            }
        except Exception as e:
            return {
                "response": f"Sorry, I couldn't scale the recipe: {str(e)}",
                "success": False
            }
    
    def _handle_substitute_ingredient(self, session: CookingSession, recipe: OptimizedRecipe, db: Session) -> Dict[str, Any]:
        """Handle ingredient substitution requests"""
        return {
            "response": "To substitute ingredients, please specify which ingredient you'd like to replace and what you'd like to use instead. For example: 'replace chicken with tofu'.",
            "success": False
        }
    
    def _save_modified_recipe(self, modified_recipe: OptimizedRecipe, db: Session, modification_type: str) -> int:
        """Save a modified recipe as a new recipe in the database"""
        from backend.app.models.models import Recipe
        import json
        
        # Create new recipe entry
        new_recipe = Recipe(
            title=f"{modified_recipe.title} ({modification_type.title()})",
            source_url="voice_modified",
            original_recipe=json.dumps({"title": modified_recipe.title, "modification_type": modification_type}),
            prep_phase=json.dumps([step.dict() for step in modified_recipe.prep_phase]),
            cook_phase=json.dumps([step.dict() for step in modified_recipe.cook_phase]),
            ingredients=json.dumps([ing.dict() for ing in modified_recipe.ingredients]),
            total_time=modified_recipe.total_time,
            prep_time=modified_recipe.prep_time,
            cook_time=modified_recipe.cook_time,
            servings=modified_recipe.servings,
            difficulty=modified_recipe.difficulty,
            user_id="default_user"
        )
        
        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)
        
        return new_recipe.id

    def _handle_serving_adjustment(self, recipe: OptimizedRecipe, command: str, db: Session) -> Dict[str, Any]:
        """Handle serving size adjustments"""
        command_lower = command.lower()
        new_servings = None
        
        # Check for specific serving numbers
        serving_match = re.search(r'(\d+)\s*(?:serving|people|person|servings)', command_lower)
        if serving_match:
            new_servings = int(serving_match.group(1))
        # Check for double/half adjustments
        elif 'double' in command_lower:
            new_servings = recipe.servings * 2
        elif 'half' in command_lower:
            new_servings = max(1, recipe.servings // 2)
            
        if new_servings:
            # Get adjusted recipe from the recipe modifier
            adjusted_data = self.recipe_modifier.adjust_recipe_for_dietary_needs(recipe, None, new_servings)
            updated_recipe = self.apply_adjusted_recipe(recipe, adjusted_data)
            
            return {
                "response": f"Recipe adjusted for {new_servings} servings",
                "recipe": updated_recipe,
                "success": True
            }
        else:
            return {
                "response": "I couldn't determine how to adjust the serving size. Please specify a number of servings or say 'double' or 'half'.",
                "success": False
            }
    
    
        
    def apply_adjusted_recipe(self, recipe: OptimizedRecipe, adjusted_data: dict) -> OptimizedRecipe:
   
    # Update ingredients
     for adj_ing in adjusted_data['adjusted_ingredients']:
        for ing in recipe.ingredients:
            if ing.name.lower() == adj_ing['name'].lower():
                ing.amount = adj_ing['amount']
                ing.unit = adj_ing['unit']
    
    # Update servings if provided
     if 'serving_size' in adjusted_data:
        recipe.servings = adjusted_data['serving_size']
    
        return recipe