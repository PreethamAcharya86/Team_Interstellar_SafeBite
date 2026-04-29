"""
Ingredient Analyzer - Flask Backend
Analyzes Indian food product ingredients for safety, allergens, and health score
"""

# Load environment variables FIRST before any imports that need them
from groq_integration import get_ingredients_from_groq, get_healthier_alternatives_from_groq
from analysis_engine import IngredientAnalyzer
import numpy as np
import os
import re
import json
from flask_cors import CORS
from flask import Flask, request, jsonify, render_template, send_from_directory
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path, override=True)


app = Flask(__name__, template_folder="../templates",
            static_folder="../frontend/static")
CORS(app)

# Initialize analyzer
analyzer = IngredientAnalyzer()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/compare")
def compare():
    return render_template("compare.html")


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
                actual_product_name = groq_result.get(
                    "product_name", product_name)
                ingredients_source = "Open Food Facts (via Groq)"
                print(f"✅ Found ingredients for: {actual_product_name}")
            else:
                # Groq failed - return detailed error asking for ingredients
                print(f"⚠️  Groq could not find: {product_name}")

                error_response = {
                    "product_name": product_name,
                    "needs_ingredients": True,  # Signal frontend to ask for manual ingredients
                    "groq_found": groq_result.get("groq_found", False),
                    "api_error": groq_result.get("api_error", False)
                }

                # Add specific error if Groq had an API error
                if groq_result.get("api_error"):
                    error_response["error"] = groq_result.get(
                        "error", "Groq API error")
                    error_response["suggestion"] = "The Groq API encountered an issue. Please:\n1. Verify your GROQ_API_KEY is valid\n2. Check your internet connection\n3. Or provide ingredients manually to proceed"
                else:
                    error_response["error"] = f"Could not find '{product_name}' in Open Food Facts database"
                    error_response["suggestion"] = "The product wasn't found in the database. Please provide ingredients manually to proceed"

                return jsonify(error_response), 400

        # Step 2: Analyze ingredients using ML model
        print(f"🔬 Analyzing ingredients for: {actual_product_name}")
        analysis_result = analyzer.analyze(
            ingredients_text, actual_product_name, category)

        # Step 3: Get healthier alternatives from Groq
        harmful_count = analysis_result.get("harmful_count", 0)
        groq_alternatives = get_healthier_alternatives_from_groq(
            actual_product_name, category, harmful_count)

        # Use Groq alternatives if available, otherwise fall back to rule-based alternatives
        if groq_alternatives and len(groq_alternatives) > 0:
            analysis_result["alternatives"] = groq_alternatives[:3]
            analysis_result["alternatives_source"] = "Groq AI"
        else:
            analysis_result["alternatives_source"] = "Rule-based database"

        # Add source information
        analysis_result["ingredients_source"] = ingredients_source
        analysis_result["model_used"] = "ML + Rule-based" if analyzer.model_loaded else "Rule-based"

        print(
            f"✅ Analysis complete. Score: {analysis_result.get('health_score')}/5")
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
        groq_alternatives = get_healthier_alternatives_from_groq(
            product_name, category, analysis_result.get("harmful_count", 0))

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


@app.route("/api/compare", methods=["POST"])
def compare_products():
    """
    Compare two products side-by-side
    Returns analysis for both products and determines the healthier one
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Get product 1 data
    product_1_data = data.get("product_1", {})
    product_1_name = product_1_data.get("product_name", "").strip()
    product_1_category = product_1_data.get("category", "snacks").lower()
    product_1_ingredients = product_1_data.get("ingredients", "").strip()

    # Get product 2 data
    product_2_data = data.get("product_2", {})
    product_2_name = product_2_data.get("product_name", "").strip()
    product_2_category = product_2_data.get("category", "snacks").lower()
    product_2_ingredients = product_2_data.get("ingredients", "").strip()

    # Validate inputs
    if not product_1_name or not product_2_name:
        return jsonify({"error": "Both product names are required"}), 400

    valid_categories = ["snacks", "biscuits", "juice"]
    if product_1_category not in valid_categories or product_2_category not in valid_categories:
        return jsonify({"error": f"Category must be one of: {', '.join(valid_categories)}"}), 400

    try:
        # Analyze Product 1
        print(f"🔍 Analyzing product 1: {product_1_name}")
        if product_1_ingredients:
            print(f"✅ Using direct ingredients for: {product_1_name}")
            ingredients_1 = product_1_ingredients
            actual_name_1 = product_1_name
        else:
            groq_result_1 = get_ingredients_from_groq(
                product_1_name, product_1_category)
            if groq_result_1.get("ingredients", "").strip():
                ingredients_1 = groq_result_1.get("ingredients", "")
                actual_name_1 = groq_result_1.get(
                    "product_name", product_1_name)
                print(f"✅ Found ingredients for: {actual_name_1}")
            else:
                return jsonify({
                    "error": f"Could not find '{product_1_name}' in database",
                    "suggestion": "Try a different product name or provide ingredients manually"
                }), 400

        # Analyze Product 2
        print(f"🔍 Analyzing product 2: {product_2_name}")
        if product_2_ingredients:
            print(f"✅ Using direct ingredients for: {product_2_name}")
            ingredients_2 = product_2_ingredients
            actual_name_2 = product_2_name
        else:
            groq_result_2 = get_ingredients_from_groq(
                product_2_name, product_2_category)
            if groq_result_2.get("ingredients", "").strip():
                ingredients_2 = groq_result_2.get("ingredients", "")
                actual_name_2 = groq_result_2.get(
                    "product_name", product_2_name)
                print(f"✅ Found ingredients for: {actual_name_2}")
            else:
                return jsonify({
                    "error": f"Could not find '{product_2_name}' in database",
                    "suggestion": "Try a different product name or provide ingredients manually"
                }), 400

        # Perform analysis on both
        print(f"🔬 Analyzing ingredients for both products")
        analysis_1 = analyzer.analyze(
            ingredients_1, actual_name_1, product_1_category)
        analysis_2 = analyzer.analyze(
            ingredients_2, actual_name_2, product_2_category)

        # Determine winner (higher health score is better)
        score_1 = analysis_1.get("health_score", 0)
        score_2 = analysis_2.get("health_score", 0)
        winner = "product_1" if score_1 >= score_2 else "product_2"

        print(
            f"✅ Comparison complete. Product 1: {score_1:.1f}, Product 2: {score_2:.1f}")

        return jsonify({
            "product_1": analysis_1,
            "product_2": analysis_2,
            "winner": winner,
            "score_difference": abs(score_1 - score_2)
        })

    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        return jsonify({"error": f"Comparison failed: {str(e)}"}), 500


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


@app.route("/api/analyze-diseases", methods=["POST"])
def analyze_diseases():
    """
    Analyze potential long-term diseases from food consumption
    Takes analysis result and returns potential health risks
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    ingredients_text = data.get("ingredients", "").strip()
    health_score = data.get("health_score", 3.0)
    harmful_ingredients = data.get("harmful_ingredients", [])
    product_name = data.get("product_name", "Unknown Product")

    if not ingredients_text:
        return jsonify({"error": "Ingredients text is required"}), 400

    try:
        # Analyze diseases
        diseases = analyzer.analyze_diseases(
            ingredients_text, health_score, harmful_ingredients)

        # Determine if there are diseases to warn about
        has_serious_diseases = any(
            d["risk_level"] in ["high", "medium"] for d in diseases)

        # If health score is good and no harmful ingredients, no diseases
        if health_score >= 4.0 and not any(h["risk"] == "high" for h in harmful_ingredients):
            warning_message = "✅ No serious long-term health diseases expected from regular consumption of this product!"
            disease_status = "healthy"
        elif has_serious_diseases:
            warning_message = "⚠️ Potential long-term health risks detected from regular consumption"
            disease_status = "at_risk"
        else:
            warning_message = "⚠️ Some potential health concerns over long-term consumption"
            disease_status = "warning"

        return jsonify({
            "product_name": product_name,
            "health_score": health_score,
            "diseases": diseases,
            "warning_message": warning_message,
            "disease_status": disease_status,
            "total_diseases_found": len(diseases),
            "has_serious_diseases": has_serious_diseases
        })

    except Exception as e:
        print(f"❌ Error during disease analysis: {e}")
        return jsonify({"error": f"Disease analysis failed: {str(e)}"}), 500


@app.route("/api/analyze-product-insights", methods=["POST"])
def analyze_product_insights():
    """
    Generate product-specific insights about composition and health effects
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    product_name = data.get("product_name", "Unknown Product")
    health_score = data.get("health_score", 3.0)
    harmful_ingredients = data.get("harmful_ingredients", [])
    ingredients_text = data.get("ingredients", "").strip()
    category = data.get("category", "snacks")

    if not ingredients_text:
        return jsonify({"error": "Ingredients text is required"}), 400

    try:
        # Get product insights
        insights = analyzer.get_product_insights(
            product_name, health_score, harmful_ingredients, ingredients_text, category)

        return jsonify(insights)

    except Exception as e:
        print(f"❌ Error during product insights analysis: {e}")
        return jsonify({"error": f"Product insights analysis failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
