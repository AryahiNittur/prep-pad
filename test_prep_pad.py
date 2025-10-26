#!/usr/bin/env python3
"""
Test script for Prep Pad cooking assistant
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_server_health():
    """Test if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is running: {data['message']}")
            return True
        else:
            print(f" Server error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(" Server is not running. Start it with: python run_server.py")
        return False

def test_recipe_parsing():
    """Test recipe parsing functionality"""
    print("\n Testing recipe parsing...")
    
    # Test with a simple recipe URL
    test_url = "https://www.allrecipes.com/recipe/213742/cheesy-chicken-broccoli-casserole/"
    
    try:
        response = requests.post(f"{BASE_URL}/api/parse_recipe", 
                               json={"url": test_url},
                               timeout=30)
        
        if response.status_code == 200:
            recipe = response.json()
            print(f"✅ Recipe parsed successfully!")
            print(f"   Title: {recipe['title']}")
            print(f"   Prep steps: {len(recipe['prep_phase'])}")
            print(f"   Cook steps: {len(recipe['cook_phase'])}")
            print(f"   Ingredients: {len(recipe['ingredients'])}")
            return recipe
        else:
            print(f"❌ Recipe parsing failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except requests.exceptions.Timeout:
        print("❌ Recipe parsing timed out (this is normal for first run)")
        return None
    except Exception as e:
        print(f"❌ Recipe parsing error: {str(e)}")
        return None

def test_get_recipes():
    """Test getting all recipes"""
    print("\n🧪 Testing get recipes...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/recipes")
        
        if response.status_code == 200:
            data = response.json()
            recipes = data.get('recipes', [])
            print(f"✅ Found {len(recipes)} recipes")
            return len(recipes) > 0
        else:
            print(f"❌ Get recipes failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Get recipes error: {str(e)}")
        return False

def test_cooking_session():
    """Test cooking session management"""
    print("\n🧪 Testing cooking session...")
    
    try:
        # Start cooking session (assuming recipe ID 1 exists)
        response = requests.post(f"{BASE_URL}/api/start_cooking/1")
        
        if response.status_code == 200:
            session = response.json()
            print(f"✅ Cooking session started!")
            print(f"   Session ID: {session['session_id']}")
            print(f"   Recipe: {session['recipe_title']}")
            print(f"   Current step: {session['current_step']}")
            print(f"   Phase: {session['current_phase']}")
            return session['session_id']
        else:
            print(f" Start cooking session failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"Cooking session error: {str(e)}")
        return None

def test_voice_commands(session_id):
    """Test voice command processing"""
    print("\n🧪 Testing voice commands...")
    
    commands = [
        ("next", "Move to next step"),
        ("repeat", "Repeat current step"),
        ("what prep", "Show prep phase"),
        ("time", "Get remaining time"),
        ("ingredients", "List ingredients")
    ]
    
    for cmd, description in commands:
        try:
            response = requests.post(f"{BASE_URL}/api/voice_command",
                                   json={"command": cmd, "session_id": session_id})
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ '{cmd}': {result['response'][:50]}...")
            else:
                print(f" '{cmd}' failed: {response.status_code}")
        except Exception as e:
            print(f" '{cmd}' error: {str(e)}")

def main():
    """Run all tests"""
    print("🍳 Prep Pad Testing Suite")
    print("=" * 40)
    
    # Test 1: Server health
    if not test_server_health():
        return
    
    # Test 2: Get existing recipes
    has_recipes = test_get_recipes()
    
    # Test 3: Recipe parsing (optional - might take time)
    print("\n⚠️  Recipe parsing test (optional - may take 30+ seconds)")
    user_input = input("Run recipe parsing test? (y/n): ").lower().strip()
    if user_input == 'y':
        recipe = test_recipe_parsing()
        if recipe:
            has_recipes = True
    
    # Test 4: Cooking session (only if we have recipes)
    if has_recipes:
        session_id = test_cooking_session()
        
        # Test 5: Voice commands (only if session started)
        if session_id:
            test_voice_commands(session_id)
    else:
        print("\n⚠️  Skipping cooking session tests - no recipes found")
        print("   Try running recipe parsing test first")
    
    print("\n✅ Testing complete!")
    print("\n📚 Next steps:")
    print("   - View API docs: http://localhost:8000/docs")
    print("   - Test with curl commands (see DEPLOYMENT.md)")
    print("   - Deploy to production when ready")

if __name__ == "__main__":
    main()
