"""
Groq API Integration for FoodAnalyzer
Handles ingredient extraction from Open Food Facts and healthier alternatives retrieval
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file (override system variables)
# Use absolute path to ensure .env is found regardless of how module is imported
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    print(f"📁 Loading .env from: {env_path}")
    load_dotenv(env_path, override=True)
else:
    print(f"⚠️ Warning: .env file not found at {env_path}")

# Initialize Groq client
try:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("❌ Error: GROQ_API_KEY not found in environment variables")
        print("   Please add GROQ_API_KEY to your .env file or system environment variables")
        client = None
    else:
        print(f"✅ GROQ_API_KEY found (length: {len(api_key)} characters)")
        # Remove proxy environment variables that might interfere
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized successfully")
except TypeError as e:
    if "proxies" in str(e):
        print(f"⚠️ Groq version compatibility issue. Trying alternative initialization...")
        try:
            # Try importing and checking version
            import groq
            print(f"   Groq version: {groq.__version__ if hasattr(groq, '__version__') else 'unknown'}")
            print("   Try upgrading: pip install --upgrade groq")
            client = None
        except:
            client = None
    else:
        print(f"❌ Error: Groq client initialization failed: {e}")
        print(f"   Make sure GROQ_API_KEY is set in .env file")
        client = None
except Exception as e:
    print(f"❌ Error: Groq client initialization failed: {e}")
    print(f"   Make sure GROQ_API_KEY is set in .env file")
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
        print("Error: Groq API client not initialized. Check GROQ_API_KEY in .env file.")
        return {
            "product_name": product_name,
            "ingredients": "",
            "brand": "Unknown",
            "found": False,
            "error": "Groq API not configured. Set GROQ_API_KEY in .env file in the main FoodAnalyzer folder.",
            "fallback": True
        }

    print(
        f"Requesting ingredients for '{product_name}' in category '{category}'")
    print("Sending request to Groq API...")

    try:
        print(f"🔄 Calling Groq API for product: {product_name}")
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

        # Log the response for debugging
        print(f"✅ Groq API response received: {response_text[:100]}...")

        # Try to parse JSON response
        result = json.loads(response_text)
        print(f"📊 Parsed result - Found: {result.get('found')}, Has ingredients: {bool(result.get('ingredients', '').strip())}")

        # Check if ingredients are actually found and not empty
        if result.get("found") and result.get("ingredients", "").strip():
            print(f"✅ Successfully retrieved ingredients for: {result.get('product_name')}")
            return result
        else:
            # If Groq couldn't find it, still return the data but mark as fallback-needed
            print(f"⚠️ Groq marked product as not found or no ingredients returned")
            result["fallback"] = True
            result["groq_found"] = result.get("found")
            return result

    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error from Groq response: {e}")
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
        error_msg = str(e)
        print(f"❌ Groq API error: {error_msg}")
        
        # Check if it's an API key issue
        if "API key" in error_msg or "401" in error_msg or "Unauthorized" in error_msg:
            print("⚠️ API Key issue detected - check your GROQ_API_KEY in .env")
            specific_error = "Invalid or expired Groq API key. Check your .env file."
        # Check if it's rate limiting
        elif "429" in error_msg or "rate" in error_msg.lower():
            print("⚠️ Rate limit hit - too many requests to Groq")
            specific_error = "Groq API rate limit exceeded. Please try again in a moment."
        # Check if it's a network issue
        elif "Connection" in error_msg or "timeout" in error_msg.lower():
            print("⚠️ Network issue - check internet connection")
            specific_error = "Network error connecting to Groq API. Check your internet connection."
        else:
            specific_error = f"Groq API error: {error_msg}"
        
        return {
            "product_name": product_name,
            "ingredients": "",
            "brand": "Unknown",
            "found": False,
            "error": specific_error,
            "fallback": True,
            "api_error": True
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
