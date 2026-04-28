"""
Ingredient Analyzer - Flask Backend
Analyzes Indian food product ingredients for safety, allergens, and health score
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import json
import re
import os
import numpy as np
from analysis_engine import IngredientAnalyzer
from groq_integration import get_ingredients_from_groq, get_healthier_alternatives_from_groq

app = Flask(__name__, template_folder="../templates", static_folder="../frontend/static")
CORS(app)

# Initialize analyzer
analyzer = IngredientAnalyzer()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Analyze a product by name (uses Groq to fetch ingredients from Open Food Facts)
    Falls back to direct ingredient analysis if Groq fails
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    product_name = data.get("product_name", "").strip()
    ingredients_direct = data.get("ingredients", "").strip()
    category = data.get("category", "snacks").lower()

    # Validate inputs
    if not product_name:
        return jsonify({"error": "Product name is required"}), 400

    valid_categories = ["snacks", "biscuits", "juice"]
    if category not in valid_categories:
        return jsonify({"error": f"Category must be one of: {', '.join(valid_categories)}"}), 400

    try:
        # Check if user provided direct ingredients
        if ingredients_direct:
            print(f"✅ Using direct ingredients for: {product_name}")
            ingredients_text = ingredients_direct
            actual_product_name = product_name
            ingredients_source = "User provided"
        else:
            # Step 1: Try to get ingredients from Groq using Open Food Facts
            print(f"🔍 Fetching ingredients from Groq for: {product_name}")
            groq_result = get_ingredients_from_groq(product_name, category)
            
            # Check if we got valid ingredients
            if groq_result.get("ingredients", "").strip():
                ingredients_text = groq_result.get("ingredients", "")
                actual_product_name = groq_result.get("product_name", product_name)
                ingredients_source = "Open Food Facts (via Groq)"
                print(f"✅ Found ingredients for: {actual_product_name}")
            else:
                # Groq failed - return error asking for ingredients
                print(f"⚠️  Groq could not find: {product_name}")
                return jsonify({
                    "error": f"Could not find '{product_name}' in Open Food Facts database.",
                    "suggestion": "Please provide the ingredient list manually or try a different product name.",
                    "product_name": product_name,
                    "needs_ingredients": True  # Signal frontend to ask for manual ingredients
                }), 400

        # Step 2: Analyze ingredients using ML model
        print(f"🔬 Analyzing ingredients for: {actual_product_name}")
        analysis_result = analyzer.analyze(ingredients_text, actual_product_name, category)
        
        # Step 3: Get healthier alternatives from Groq
        harmful_count = analysis_result.get("harmful_count", 0)
        groq_alternatives = get_healthier_alternatives_from_groq(actual_product_name, category, harmful_count)
        
        # Use Groq alternatives if available, otherwise fall back to rule-based alternatives
        if groq_alternatives and len(groq_alternatives) > 0:
            analysis_result["alternatives"] = groq_alternatives[:3]
            analysis_result["alternatives_source"] = "Groq AI"
        else:
            analysis_result["alternatives_source"] = "Rule-based database"

        # Add source information
        analysis_result["ingredients_source"] = ingredients_source
        analysis_result["model_used"] = "ML + Rule-based" if analyzer.model_loaded else "Rule-based"
        
        print(f"✅ Analysis complete. Score: {analysis_result.get('health_score')}/5")
        return jsonify(analysis_result)
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/api/analyze-direct", methods=["POST"])
def analyze_direct():
    """
    Analyze ingredients directly without needing Groq
    Useful for testing or when ingredients are already known
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    product_name = data.get("product_name", "Unknown Product").strip()
    ingredients = data.get("ingredients", "").strip()
    category = data.get("category", "snacks").lower()

    # Validate inputs
    if not ingredients:
        return jsonify({"error": "Ingredients list is required"}), 400

    valid_categories = ["snacks", "biscuits", "juice"]
    if category not in valid_categories:
        return jsonify({"error": f"Category must be one of: {', '.join(valid_categories)}"}), 400

    try: 
        analysis_result = analyzer.analyze(ingredients, product_name, category)
        groq_alternatives = get_healthier_alternatives_from_groq(product_name, category, analysis_result.get("harmful_count", 0))
        
        if groq_alternatives and len(groq_alternatives) > 0:
            analysis_result["alternatives"] = groq_alternatives[:3]
            analysis_result["alternatives_source"] = "Groq AI"
        else:
            analysis_result["alternatives_source"] = "Rule-based database"

        # Add source information
        analysis_result["ingredients_source"] = "Direct input"
        analysis_result["model_used"] = "ML + Rule-based" if analyzer.model_loaded else "Rule-based"
        
        return jsonify(analysis_result)
        
    except Exception as e:
        print(f"❌ Error during direct analysis: {e}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500



@app.route("/api/products/sample", methods=["GET"])
def sample_products():
    """Return sample Indian products for demo"""
    samples = [
        {
            "product_name": "Kurkure Masala Munch",
            "category": "snacks",
            "ingredients": "Cornmeal, Edible Vegetable Oil, Rice Meal, Wheat Flour, Spices and Condiments (3%), Salt, Sugar, Maize Flour, Monosodium Glutamate, Artificial Flavour (Masala), TBHQ"
        },
        {
            "product_name": "Parle-G Gluco Biscuits",
            "category": "biscuits",
            "ingredients": "Wheat Flour, Sugar, Edible Vegetable Oil, Invert Syrup, Milk Solids, Leavening Agents, Salt, Artificial Flavour (Vanilla)"
        },
        {
            "product_name": "Frooti Mango Drink",
            "category": "juice",
            "ingredients": "Water, Mango Pulp (10%), Sugar, Citric Acid, Artificial Mango Flavour, Sodium Benzoate (E211), Sunset Yellow FCF (E110)"
        },
        {
            "product_name": "Act II Butter Popcorn",
            "category": "snacks",
            "ingredients": "Corn, Partially Hydrogenated Vegetable Oil, Salt, Artificial Butter Flavour, TBHQ, Yellow 5"
        },
        {
            "product_name": "Paper Boat Aam Panna",
            "category": "juice",
            "ingredients": "Water, Raw Mango Pulp, Sugar, Salt, Roasted Cumin, Black Pepper, Mint Extract, Citric Acid"
        },
        {
            "product_name": "Britannia NutriChoice",
            "category": "biscuits",
            "ingredients": "Whole Wheat Flour, Oats, Sugar, Vegetable Oil, Milk Solids, Salt, Leavening Agents"
        }
    ]
    return jsonify(samples)


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint showing system status"""
    return jsonify({
        "status": "healthy",
        "model_loaded": analyzer.model_loaded,
        "analysis_engine": "ML + Rule-based" if analyzer.model_loaded else "Rule-based only",
        "version": "2.0 - ML Integrated"
    })



if __name__ == "__main__":
    app.run(debug=True, port=5000)
