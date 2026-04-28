"""
Groq API Integration for FoodAnalyzer
Handles ingredient extraction from Open Food Facts and healthier alternatives retrieval
"""

import json
import os
from groq import Groq

# Initialize Groq client
try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    print(f"Warning: Groq client initialization failed. Make sure GROQ_API_KEY is set: {e}")
    client = None

def get_ingredients_from_groq(product_name: str, category: str) -> dict:
    """
    Get ingredient list for a product from Open Food Facts database using Groq
    
    Args:
        product_name: Name of the food product
        category: Category of product (snacks, biscuits, juice)
    
    Returns:
        dict with ingredient list and product details
    """
    if not client:
        return {
            "product_name": product_name,
            "ingredients": "",
            "brand": "Unknown",
            "found": False,
            "error": "Groq API not configured. Set GROQ_API_KEY environment variable.",
            "fallback": True
        }
    
    try:
        message = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a food database expert with access to Open Food Facts database.
Find the ingredient list for the product: "{product_name}" (Category: {category})

Return ONLY a JSON response with exactly this structure (no markdown, no code blocks, raw JSON):
{{
    "product_name": "exact product name",
    "ingredients": "comma-separated ingredient list",
    "brand": "brand name if available",
    "found": true/false
}}

If you can't find the exact product, search for similar products with the same name in the {category} category and return the closest match.
If no product found even after searching similar names, use "found": false and provide typical ingredients for similar {category} products with that name pattern."""
                }
            ]
        )
        
        response_text = message.choices[0].message.content.strip()
        
        # Try to parse JSON response
        result = json.loads(response_text)
        
        # Check if ingredients are actually found and not empty
        if result.get("found") and result.get("ingredients", "").strip():
            return result
        else:
            # If Groq couldn't find it, still return the data but mark as fallback-needed
            result["fallback"] = True
            return result
            
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        # Fallback if JSON parsing fails
        return {
            "product_name": product_name,
            "ingredients": "",
            "brand": "Unknown",
            "found": False,
            "error": f"Could not parse ingredient data: {str(e)}",
            "fallback": True
        }
    except Exception as e:
        print(f"Groq API error: {e}")
        return {
            "product_name": product_name,
            "ingredients": "",
            "brand": "Unknown",
            "found": False,
            "error": str(e),
            "fallback": True
        }


def get_healthier_alternatives_from_groq(product_name: str, category: str, harmful_count: int = 0) -> list:
    """
    Get healthier alternatives for a product using Groq
    
    Args:
        product_name: Name of the food product
        category: Category of product (snacks, biscuits, juice)
        harmful_count: Number of harmful ingredients found (helps prioritize cleaner options)
    
    Returns:
        list of healthier alternatives
    """
    if not client:
        return []
    
    try:
        priority = "very clean and natural options" if harmful_count > 0 else "healthier alternatives"
        
        message = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=600,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a food nutrition expert. Find {priority} for the product: "{product_name}" ({category})

Return ONLY a JSON array with exactly 3-4 alternatives in this format (no markdown, no code blocks, raw JSON):
[
    {{
        "name": "product name",
        "brand": "brand name",
        "reason": "brief reason why it's healthier (one sentence, max 15 words)"
    }}
]

Guidelines:
- Suggest REAL products available in Indian markets
- Focus on products with FEWER artificial additives and preservatives
- Prefer natural/organic options if harmful ingredients were found
- Include at least one budget-friendly option
- Each reason should clearly state what makes it healthier (e.g., "No artificial colors, natural ingredients", "Whole grain, high fiber")
- Only return the JSON array, nothing else"""
                }
            ]
        )
        
        response_text = message.choices[0].message.content.strip()
        
        # Try to parse JSON response
        alternatives = json.loads(response_text)
        return alternatives if isinstance(alternatives, list) else []
    except json.JSONDecodeError:
        # Fallback to empty list if parsing fails
        return []
    except Exception as e:
        print(f"Error getting alternatives from Groq: {e}")
        return []
