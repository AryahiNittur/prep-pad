#!/usr/bin/env python3
"""
Test script to create a sample recipe and cooking session for testing voice commands
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def create_test_recipe():
    """Create a test recipe"""
    test_recipe_data = {
        "title": "Test Scrambled Eggs",
        "ingredients": [
            {"name": "eggs", "amount": "2", "unit": "large", "notes": "room temperature"},
            {"name": "butter", "amount": "1", "unit": "tbsp", "notes": "unsalted"},
            {"name": "salt", "amount": "1/4", "unit": "tsp", "notes": "to taste"},
            {"name": "pepper", "amount": "1/8", "unit": "tsp", "notes": "freshly ground"}
        ],
        "prep_phase": [
            {"instruction": "Crack eggs into a bowl", "time_estimate": 1, "category": "preparation"},
            {"instruction": "Beat eggs with a fork until well combined", "time_estimate": 2, "category": "mixing"},
            {"instruction": "Season with salt and pepper", "time_estimate": 1, "category": "seasoning"},
            {"instruction": "Heat butter in a non-stick pan over medium heat", "time_estimate": 2, "category": "preheating"}
        ],
        "cook_phase": [
            {"step_number": 1, "instruction": "Pour beaten eggs into the hot pan", "time_estimate": 1, "parallel_tasks": []},
            {"step_number": 2, "instruction": "Gently stir eggs with a spatula", "time_estimate": 3, "parallel_tasks": ["Keep stirring continuously"]},
            {"step_number": 3, "instruction": "Remove from heat when eggs are still slightly runny", "time_estimate": 1, "parallel_tasks": []},
            {"step_number": 4, "instruction": "Serve immediately", "time_estimate": 1, "parallel_tasks": []}
        ],
        "total_time": 12,
        "prep_time": 6,
        "cook_time": 6,
        "servings": 1,
        "difficulty": "easy"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/create_recipe", 
                               json=test_recipe_data)
        
        if response.status_code == 200:
            print("✅ Test recipe created successfully!")
            return response.json()
        else:
            print(f"❌ Failed to create test recipe: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating test recipe: {str(e)}")
        return None

def start_test_cooking_session():
    """Start a test cooking session"""
    try:
        response = requests.post(f"{BASE_URL}/api/start_cooking/1")
        
        if response.status_code == 200:
            session = response.json()
            print(f"✅ Test cooking session started!")
            print(f"   Session ID: {session['session_id']}")
            print(f"   Recipe: {session['recipe_title']}")
            print(f"   Current step: {session['current_step']}")
            print(f"   Phase: {session['current_phase']}")
            return session['session_id']
        else:
            print(f"❌ Failed to start cooking session: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error starting cooking session: {str(e)}")
        return None

def test_voice_commands(session_id):
    """Test voice commands"""
    commands = [
        ("next", "Move to next step"),
        ("repeat", "Repeat current step"),
        ("what prep", "Show prep phase"),
        ("time", "Get remaining time"),
        ("ingredients", "List ingredients")
    ]
    
    print(f"\n🧪 Testing voice commands for session {session_id}...")
    
    for cmd, description in commands:
        try:
            response = requests.post(f"{BASE_URL}/api/voice_command",
                                   json={"command": cmd, "session_id": session_id})
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ '{cmd}': {result['response']}")
            else:
                print(f"❌ '{cmd}' failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ '{cmd}' error: {str(e)}")

def main():
    """Run all tests"""
    print("🍳 Prep Pad Voice Command Testing")
    print("=" * 40)
    
    # Test 1: Create test recipe
    print("\n1. Creating test recipe...")
    recipe = create_test_recipe()
    
    if not recipe:
        print("❌ Cannot proceed without a test recipe")
        return
    
    # Test 2: Start cooking session
    print("\n2. Starting cooking session...")
    session_id = start_test_cooking_session()
    
    if not session_id:
        print("❌ Cannot proceed without a cooking session")
        return
    
    # Test 3: Test voice commands
    print("\n3. Testing voice commands...")
    test_voice_commands(session_id)
    
    print("\n✅ Voice command testing complete!")
    print(f"\n🎯 You can now test the frontend at: http://localhost:3000/cooking/{session_id}")

if __name__ == "__main__":
    main()
