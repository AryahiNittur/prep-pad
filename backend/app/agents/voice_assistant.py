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
        elif command in ['time', 'how long', 'timer']:
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
    
    
    def process_voice_command(self, command: str, session: CookingSession, 
        recipe: OptimizedRecipe, db: Session) -> Dict[str, Any]:
   
        command_lower = command.lower().strip()
    
        # Handle dietary and serving adjustments
        if any(keyword in command_lower for keyword in ['vegan', 'vegetarian', 'gluten-free', 'dairy-free']):
            dietary_pref = next((pref for pref in ['vegan', 'vegetarian', 'gluten-free', 'dairy-free'] 
                               if pref in command_lower), None)
            servings = None
            
            # Check for serving size changes
            serving_match = re.search(r'(\d+)\s*(?:serving|people|person|servings)', command_lower)
            if serving_match:
                servings = int(serving_match.group(1))
            
            return self._handle_dietary_adjustment(recipe, dietary_pref, servings, db)
            
        # Check for serving size adjustments
        elif any(keyword in command_lower for keyword in ['adjust', 'change', 'scale', 'serving', 'double', 'half']):
            return self._handle_serving_adjustment(recipe, command, db)
            
        # Handle existing commands
        else:
            return self._process_voice_command(command, session, recipe, db)
        
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