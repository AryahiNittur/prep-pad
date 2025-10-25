import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, List, Optional
import re
from urllib.parse import urlparse

class RecipeScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_recipe(self, url: str) -> Dict:
        """
        Scrape recipe content from a given URL
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find recipe data in JSON-LD format (common on recipe sites)
            recipe_data = self._extract_json_ld(soup)
            if recipe_data:
                return recipe_data
            
            # Fallback to HTML parsing
            return self._extract_from_html(soup, url)
            
        except Exception as e:
            raise Exception(f"Failed to scrape recipe from {url}: {str(e)}")
    
    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Extract recipe data from JSON-LD structured data
        """
        json_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                
                # Handle both single objects and arrays
                if isinstance(data, list):
                    data = data[0]
                
                if data.get('@type') == 'Recipe':
                    return {
                        'title': data.get('name', ''),
                        'description': data.get('description', ''),
                        'ingredients': data.get('recipeIngredient', []),
                        'instructions': data.get('recipeInstructions', []),
                        'cookTime': data.get('cookTime', ''),
                        'prepTime': data.get('prepTime', ''),
                        'totalTime': data.get('totalTime', ''),
                        'recipeYield': data.get('recipeYield', ''),
                        'author': data.get('author', {}).get('name', '') if isinstance(data.get('author'), dict) else data.get('author', '')
                    }
            except (json.JSONDecodeError, KeyError):
                continue
        
        return None
    
    def _extract_from_html(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Fallback HTML parsing for recipe content
        """
        # Common selectors for recipe elements
        title_selectors = [
            'h1[class*="recipe"]', 'h1[class*="title"]', 
            '.recipe-title', '.entry-title', 'h1'
        ]
        
        ingredient_selectors = [
            '[class*="ingredient"]', '[class*="ingredients"]',
            '.recipe-ingredients', '.ingredients-list'
        ]
        
        instruction_selectors = [
            '[class*="instruction"]', '[class*="directions"]',
            '.recipe-instructions', '.directions', 'ol li', 'ul li'
        ]
        
        # Extract title
        title = self._extract_text_by_selectors(soup, title_selectors)
        
        # Extract ingredients
        ingredients = self._extract_ingredients(soup, ingredient_selectors)
        
        # Extract instructions
        instructions = self._extract_instructions(soup, instruction_selectors)
        
        return {
            'title': title or 'Untitled Recipe',
            'description': '',
            'ingredients': ingredients,
            'instructions': instructions,
            'cookTime': '',
            'prepTime': '',
            'totalTime': '',
            'recipeYield': '',
            'author': '',
            'source_url': url
        }
    
    def _extract_text_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Extract text using multiple CSS selectors"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return ''
    
    def _extract_ingredients(self, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        """Extract ingredients list"""
        ingredients = []
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                # Look for list items or paragraphs within the ingredient container
                items = element.find_all(['li', 'p'])
                if items:
                    for item in items:
                        text = item.get_text(strip=True)
                        if text and len(text) > 3:  # Filter out very short text
                            ingredients.append(text)
                    if ingredients:
                        break
            if ingredients:
                break
        
        return ingredients
    
    def _extract_instructions(self, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        """Extract cooking instructions"""
        instructions = []
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                # Look for ordered list items (numbered steps) or paragraphs
                items = element.find_all(['li', 'p'])
                if items:
                    for item in items:
                        text = item.get_text(strip=True)
                        if text and len(text) > 10:  # Filter out very short text
                            instructions.append(text)
                    if instructions:
                        break
            if instructions:
                break
        
        return instructions