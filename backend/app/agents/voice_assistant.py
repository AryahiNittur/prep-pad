from langchain_openai import ChatOpenAI
from backend.app.schemas.schemas import OptimizedRecipe, PrepStep, CookStep
from backend.app.models.models import CookingSession
from sqlmodel import Session, select
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

class VoiceCookingAssistant:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def process_voice_command(self, command: str, session: CookingSession, 
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
                response_text = f"Next prep step: {session.current_step}"
            else:
                # Move to cooking phase
                session.current_phase = 'cook'
                if recipe.cook_phase and len(recipe.cook_phase) > 0:
                    session.current_step = recipe.cook_phase[0].instruction
                    response_text = f"Prep complete! Starting cooking phase. Step 1: {session.current_step}"
                else:
                    session.is_active = False
                    response_text = "Prep complete! No cooking steps available."
        elif session.current_phase == 'cook' and recipe.cook_phase:
            # Handle cooking steps
            current_cook_index = self._get_current_cook_index(session, recipe)
            if current_cook_index < len(recipe.cook_phase) - 1:
                next_cook_index = current_cook_index + 1
                session.current_step = recipe.cook_phase[next_cook_index].instruction
                response_text = f"Step {next_cook_index + 1}: {session.current_step}"
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
    
    def _handle_unknown_command(self, command: str) -> Dict[str, Any]:
        """Handle unknown commands"""
        return {
            "response": f"I didn't understand '{command}'. Try saying 'next', 'repeat', 'what prep', 'pause', or 'resume'.",
            "suggestions": ["next", "repeat", "what prep", "pause", "resume", "time", "ingredients"]
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