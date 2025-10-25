"""
client.py
---------------
Handles all GPT-based reasoning for Mise-en-Place AI.
Supports structured parsing, workflow optimization, and conversational cooking.
"""

from __future__ import annotations
import os
import json
from typing import Any, Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# ------------------------------------------------------------
# Initialization
# ------------------------------------------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------------------------------------------------
# In-memory context (replace with DB/Redis later)
# ------------------------------------------------------------
memory: List[Dict[str, str]] = []


# ------------------------------------------------------------
# Core Chat Function
# ------------------------------------------------------------
def chat_with_gpt(
    prompt: str,
    model: str = "gpt-4o-mini",
    mode: str = "general",
    context_data: Optional[Dict[str, Any]] = None,
    temperature: float = 0.5,
) -> str:
    """
    Send a prompt to ChatGPT with mode- and context-aware reasoning.

    Args:
        prompt: User input or task.
        model: LLM model (default gpt-4o-mini).
        mode: 'recipe_parser', 'workflow_optimizer', 'culinary_chat', or 'general'.
        context_data: Optional supporting data.
        temperature: Creativity control.
    """

    system_role = "You are an expert culinary assistant named Mise-en-Place AI."

    if mode == "recipe_parser":
        system_role += " Extract ingredients and steps from messy text, returning structured JSON."
    elif mode == "workflow_optimizer":
        system_role += " Rewrite cooking steps into prep-first and parallel-friendly workflows."
    elif mode == "culinary_chat":
        system_role += " Speak casually like a sous-chef guiding a home cook in real time."

    # Build messages
    messages = [{"role": "system", "content": system_role}]
    messages.extend(memory)

    if context_data:
        messages.append({
            "role": "system",
            "content": f"Context data:\n{json.dumps(context_data, indent=2)}"
        })

    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )

        reply = response.choices[0].message.content.strip()

        # Update memory
        memory.append({"role": "user", "content": prompt})
        memory.append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        return f"Error calling ChatGPT: {e}"


# ------------------------------------------------------------
# Manual Testing
# ------------------------------------------------------------
if __name__ == "__main__":
    raw_recipe = """
    Grandma's Garlic Pasta:
    Boil 2 cups penne. While boiling, chop 4 cloves garlic and sauté in olive oil.
    Add cream and toss pasta.
    """
    structured = chat_with_gpt(
        f"Parse this recipe: {raw_recipe}",
        mode="recipe_parser",
        temperature=0.2,
    )
    print("Parsed Recipe:\n", structured)

    context = {
        "ingredients": ["2 cups penne", "4 cloves garlic", "1 cup cream"],
        "steps": ["Boil pasta", "Chop garlic", "Sauté garlic", "Add cream"],
    }
    optimized = chat_with_gpt(
        "Rewrite into prep and cook phases with parallel steps.",
        mode="workflow_optimizer",
        context_data=context,
    )
    print("Optimized Workflow:\n", optimized)

    reply = chat_with_gpt(
        "What should I do while the pasta boils?",
        mode="culinary_chat",
        temperature=0.8,
    )
    print("Chatbot Reply:\n", reply)
