"""
Ingredient Analysis Engine
Core analysis logic - works with or without trained ML model
Falls back to rule-based scoring if model not available
"""

import re
import json
import os
import numpy as np

# ── Harmful Additives Database ──────────────────────────────
HARMFUL_ADDITIVES = {
    "titanium dioxide": {"risk": "high", "reason": "Possible carcinogen, banned in EU food products"},
    "potassium bromate": {"risk": "high", "reason": "Banned in 84+ countries, linked to cancer"},
    "brominated vegetable oil": {"risk": "high", "reason": "Banned in EU and Japan, linked to thyroid issues"},
    "tbhq": {"risk": "high", "reason": "Linked to vision disturbances and ADHD, banned in some countries"},
    "bha": {"risk": "high", "reason": "Possible carcinogen, classified as possibly carcinogenic to humans"},
    "bht": {"risk": "medium", "reason": "Endocrine disruptor concerns, restricted in several countries"},
    "red 40": {"risk": "medium", "reason": "Linked to hyperactivity in children, derived from petroleum"},
    "yellow 5": {"risk": "medium", "reason": "May cause allergic reactions, hyperactivity in children"},
    "yellow 6": {"risk": "medium", "reason": "May cause allergic reactions, hyperactivity in children"},
    "sodium benzoate": {"risk": "medium", "reason": "Forms benzene (carcinogen) when combined with vitamin C"},
    "aspartame": {"risk": "medium", "reason": "Controversial sweetener, some studies suggest neurological effects"},
    "acesulfame k": {"risk": "medium", "reason": "May negatively affect gut microbiome"},
    "acesulfame potassium": {"risk": "medium", "reason": "May negatively affect gut microbiome"},
    "saccharin": {"risk": "medium", "reason": "Bladder cancer concerns noted in animal studies"},
    "cyclamate": {"risk": "high", "reason": "Banned in USA, potential carcinogen"},
    "monosodium glutamate": {"risk": "low", "reason": "May cause headaches and discomfort in sensitive individuals"},
    "carrageenan": {"risk": "medium", "reason": "May cause intestinal inflammation, under review by FDA"},
    "high fructose corn syrup": {"risk": "medium", "reason": "Linked to obesity, fatty liver, and metabolic syndrome"},
    "artificial color": {"risk": "medium", "reason": "Various synthetic dyes with potential health concerns"},
    "artificial colour": {"risk": "medium", "reason": "Various synthetic dyes with potential health concerns"},
    "artificial flavor": {"risk": "low", "reason": "Unspecified synthetic chemicals, lack of transparency"},
    "artificial flavour": {"risk": "low", "reason": "Unspecified synthetic chemicals, lack of transparency"},
    "hydrogenated vegetable oil": {"risk": "high", "reason": "Trans fats - major cardiovascular risk factor"},
    "partially hydrogenated": {"risk": "high", "reason": "Trans fats - raises bad cholesterol, lowers good cholesterol"},
    "vanaspati": {"risk": "high", "reason": "Hydrogenated vegetable fat with dangerous trans fats"},
    "dalda": {"risk": "high", "reason": "Hydrogenated fat - one of the most harmful trans fat sources"},
    "refined palm oil": {"risk": "medium", "reason": "Very high in saturated fat, inflammatory"},
    "propylene glycol": {"risk": "medium", "reason": "Synthetic chemical used as humectant, potential irritant"},
    "dimethyl dicarbonate": {"risk": "medium", "reason": "Reactive chemical preservative, breaks down into methanol"},
    "sodium nitrite": {"risk": "medium", "reason": "Can form carcinogenic nitrosamines when heated"},
    "e102": {"risk": "medium", "reason": "Tartrazine - causes hyperactivity, allergic reactions"},
    "e110": {"risk": "medium", "reason": "Sunset Yellow - causes hyperactivity, banned in Norway"},
    "e122": {"risk": "medium", "reason": "Carmoisine - hyperactivity risk, banned in some countries"},
    "e124": {"risk": "medium", "reason": "Ponceau 4R - hyperactivity risk"},
    "e129": {"risk": "medium", "reason": "Allura Red - hyperactivity risk in children"},
    "e211": {"risk": "medium", "reason": "Sodium Benzoate - carcinogen risk with Vitamin C"},
    "e220": {"risk": "low", "reason": "Sulphur Dioxide - allergen, particularly for asthma sufferers"},
    "e250": {"risk": "medium", "reason": "Sodium Nitrite - possible link to colorectal cancer"},
    "e320": {"risk": "high", "reason": "BHA - possible carcinogen, listed as possibly carcinogenic"},
    "e321": {"risk": "medium", "reason": "BHT - endocrine disruptor concerns"},
    "e951": {"risk": "medium", "reason": "Aspartame - controversial, potential neurological effects"},
    "e952": {"risk": "high", "reason": "Cyclamate - banned in USA and Canada"},
    "maida": {"risk": "medium", "reason": "Refined flour - high glycemic index, stripped of nutrients"},
    "refined wheat flour": {"risk": "low", "reason": "Refined flour with reduced nutritional value"},
    "sulphur dioxide": {"risk": "low", "reason": "Allergen for asthma patients, can trigger attacks"},
    "calcium propionate": {"risk": "low", "reason": "May cause ADHD-like behavior in some children"},
    "sunset yellow": {"risk": "medium", "reason": "Synthetic dye linked to hyperactivity, allergic reactions"},
    "tartrazine": {"risk": "medium", "reason": "Yellow dye linked to hyperactivity and allergic reactions"},
    "allura red": {"risk": "medium", "reason": "Red dye linked to hyperactivity in children"},
}

# ── Allergens Database ───────────────────────────────────────
ALLERGENS = {
    "milk/dairy": ["milk", "dairy", "lactose", "whey", "casein", "butter", "cream", "cheese", "ghee", "paneer"],
    "tree nuts": ["almond", "cashew", "walnut", "pistachio", "hazelnut", "pecan", "macadamia", "pine nut"],
    "peanuts": ["peanut", "groundnut", "monkey nut"],
    "gluten/wheat": ["wheat", "barley", "rye", "gluten", "maida", "atta", "semolina", "suji", "sooji", "wheat starch"],
    "soy": ["soy", "soya", "soybean", "tofu", "tempeh"],
    "eggs": ["egg", "albumin", "mayonnaise", "lecithin"],
    "sesame": ["sesame", "til", "tahini", "gingelly"],
    "sulphites": ["sulphur", "sulfite", "e220", "e221", "e222", "e223", "e224", "sulphur dioxide"],
    "mustard": ["mustard", "sarson", "mustard seed", "mustard oil"],
    "fish": ["fish", "anchovy", "tuna", "salmon", "sardine"],
}

# ── Healthier Alternatives ────────────────────────────────────
ALTERNATIVES = {
    "snacks": [
        {"name": "Makhana (Fox Nuts)", "brand": "None / Local", "reason": "High protein, low fat, zero artificial additives, naturally crunchy"},
        {"name": "Roasted Chana", "brand": "Haldiram / Local", "reason": "Natural protein source, high fiber, no preservatives"},
        {"name": "Too Yumm! Multigrain", "brand": "Too Yumm", "reason": "Baked not fried, multigrain, fewer additives"},
        {"name": "Cornitos Nacho Chips", "brand": "Cornitos", "reason": "Simpler ingredient list, no MSG"},
        {"name": "Dried Fruits & Nuts Mix", "brand": "Happilo / Any", "reason": "Completely natural, nutrient-dense, no processing"},
    ],
    "biscuits": [
        {"name": "McVities Digestive", "brand": "McVities", "reason": "Whole wheat base, lower sugar, no artificial colors"},
        {"name": "Britannia NutriChoice", "brand": "Britannia", "reason": "Multigrain, high fiber, better nutritional profile"},
        {"name": "Homemade Atta Biscuits", "brand": "Homemade", "reason": "Complete control over ingredients, no preservatives"},
        {"name": "Annas Ginger Thins", "brand": "Anna's", "reason": "Simple ingredients, natural ginger flavor"},
    ],
    "juice": [
        {"name": "Paper Boat Aam Panna", "brand": "Paper Boat", "reason": "Traditional Indian recipe, natural spices, minimal additives"},
        {"name": "Raw Pressery Cold Press", "brand": "Raw Pressery", "reason": "No added sugar, no preservatives, high vitamin content"},
        {"name": "Fresh Squeezed Juice", "brand": "Home / Juice Bar", "reason": "Maximum nutrition, zero additives, completely natural"},
        {"name": "B Natural Mixed Fruit", "brand": "B Natural", "reason": "No artificial color/preservatives, better than most packaged juices"},
        {"name": "Coconut Water", "brand": "Any brand / Fresh", "reason": "Natural electrolytes, no sugar added, extremely healthy"},
    ]
}


class IngredientAnalyzer:
    def __init__(self):
        self.model_loaded = False
        self.risk_model = None
        self.score_model = None
        self.tfidf = None
        self.le_risk = None
        self.feature_cols = None
        self._try_load_models()

    def _try_load_models(self):
        """Try to load trained ML models, fall back to rule-based if not found"""
        model_dir = os.path.join(os.path.dirname(__file__), "../model_artifacts")
        
        print(f"🔍 Looking for models in: {model_dir}")
        print(f"📁 Directory exists: {os.path.exists(model_dir)}")
        
        if os.path.exists(model_dir):
            print(f"📋 Files found: {os.listdir(model_dir)}")
        
        try:
            import joblib
            
            # Check if all required files exist
            required_files = [
                "risk_classifier.pkl",
                "score_regressor.pkl", 
                "tfidf_vectorizer.pkl",
                "label_encoder_risk.pkl",
                "feature_cols.json"
            ]
            
            missing_files = [f for f in required_files if not os.path.exists(os.path.join(model_dir, f))]
            if missing_files:
                raise FileNotFoundError(f"Missing model files: {missing_files}")
            
            print("✅ All model files found, loading...")
            self.risk_model = joblib.load(os.path.join(model_dir, "risk_classifier.pkl"))
            self.score_model = joblib.load(os.path.join(model_dir, "score_regressor.pkl"))
            self.tfidf = joblib.load(os.path.join(model_dir, "tfidf_vectorizer.pkl"))
            self.le_risk = joblib.load(os.path.join(model_dir, "label_encoder_risk.pkl"))
            with open(os.path.join(model_dir, "feature_cols.json")) as f:
                self.feature_cols = json.load(f)
            self.model_loaded = True
            print("✅ ML models loaded successfully!")
            print(f"   - Risk Classifier: {type(self.risk_model).__name__}")
            print(f"   - Score Regressor: {type(self.score_model).__name__}")
            print(f"   - TF-IDF Features: {len(self.tfidf.get_feature_names_out())} terms")
            print(f"   - Risk Classes: {self.le_risk.classes_}")
            
        except FileNotFoundError as e:
            print(f"⚠️  Model files not found: {e}")
            self.model_loaded = False
        except ImportError as e:
            print(f"⚠️  joblib not installed: {e}")
            print("   Install with: pip install joblib scikit-learn")
            self.model_loaded = False
        except Exception as e:
            print(f"⚠️  ML models not found, using rule-based analysis")
            print(f"   Error: {e}")
            self.model_loaded = False

    def clean_ingredients(self, text):
        text = str(text).lower()
        text = re.sub(r'\([^)]*\)', ' ', text)
        text = re.sub(r'\d+\.?\d*\s*%', '', text)
        text = re.sub(r'[^\w\s,]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def detect_harmful(self, clean_text):
        found = []
        for additive, info in HARMFUL_ADDITIVES.items():
            if additive in clean_text:
                found.append({
                    "name": additive.title(),
                    "key": additive,
                    "risk": info["risk"],
                    "reason": info["reason"]
                })
        return found

    def detect_allergens(self, clean_text):
        found = []
        for allergen, keywords in ALLERGENS.items():
            if any(kw in clean_text for kw in keywords):
                found.append(allergen)
        return found

    def compute_rule_score(self, harmful_list):
        score = 5.0
        for item in harmful_list:
            if item["risk"] == "high":
                score -= 1.5
            elif item["risk"] == "medium":
                score -= 0.75
            elif item["risk"] == "low":
                score -= 0.25
        return max(0.0, min(5.0, round(score, 1)))

    def _build_numeric_features(self, clean_text, harmful, allergens, category):
        num = {
            "harmful_count": len(harmful),
            "high_risk_count": sum(1 for h in harmful if h["risk"] == "high"),
            "medium_risk_count": sum(1 for h in harmful if h["risk"] == "medium"),
            "low_risk_count": sum(1 for h in harmful if h["risk"] == "low"),
            "allergen_count": len(allergens),
            "ingredient_length": len(clean_text),
            "ingredient_word_count": len(clean_text.split()),
            "high_risk_ratio": sum(1 for h in harmful if h["risk"] == "high") / (len(harmful) + 1),
            "has_artificial_color": int(bool(re.search(r"artificial colo[ur]|e1[0-9][0-9]", clean_text))),
            "has_preservatives": int(bool(re.search(r"preserv|benzoate|sorbate|nitrite", clean_text))),
            "has_trans_fat": int(bool(re.search(r"hydrogenated|vanaspati|dalda", clean_text))),
            "has_msg": int(bool(re.search(r"monosodium glutamate|msg", clean_text))),
            "has_artificial_sweetener": int(bool(re.search(r"aspartame|saccharin|acesulfame|sucralose", clean_text))),
            "has_maida": int(bool(re.search(r"maida|refined wheat flour", clean_text))),
            "has_whole_grain": int(bool(re.search(r"whole wheat|multigrain|oat|millet|ragi|jowar|bajra", clean_text))),
            "has_natural": int(bool(re.search(r"\bnatural\b|\borganic\b|\bfresh\b", clean_text))),
            "cat_biscuits": int(category == "biscuits"),
            "cat_juice": int(category == "juice"),
            "cat_snacks": int(category == "snacks"),
        }
        return num

    def get_ingredient_risks(self, clean_text):
        """Return per-ingredient risk levels"""
        parts = [i.strip() for i in re.split(r'[,;]', clean_text) if len(i.strip()) > 2]
        result = []
        for ing in parts[:25]:
            risk_level = "safe"
            matched_reason = ""
            for key, info in HARMFUL_ADDITIVES.items():
                if key in ing.lower():
                    risk_level = info["risk"]
                    matched_reason = info["reason"]
                    break
            result.append({
                "name": ing.strip().title(),
                "risk": risk_level,
                "reason": matched_reason
            })
        return result

    def get_risk_label(self, score):
        if score >= 4.0:
            return "safe"
        elif score >= 2.5:
            return "moderate"
        else:
            return "risky"

    def analyze(self, ingredients_text, product_name, category):
        clean = self.clean_ingredients(ingredients_text)
        harmful = self.detect_harmful(clean)
        allergens = self.detect_allergens(clean)
        rule_score = self.compute_rule_score(harmful)
        ingredient_risks = self.get_ingredient_risks(clean)

        # ML prediction if available
        ml_score = rule_score
        ml_risk = self.get_risk_label(rule_score)
        
        if self.model_loaded:
            try:
                text_feat = self.tfidf.transform([clean]).toarray()
                num_feat = self._build_numeric_features(clean, harmful, allergens, category)
                num_arr = np.array([[num_feat.get(col, 0) for col in self.feature_cols]])
                X = np.hstack([text_feat, num_arr])
                ml_risk = self.le_risk.inverse_transform(self.risk_model.predict(X))[0]
                ml_score_raw = float(self.score_model.predict(X)[0])
                ml_score = float(np.clip(ml_score_raw, 0, 5))
            except Exception:
                pass  # Fall back to rule-based

        # Blend scores
        final_score = round(0.65 * rule_score + 0.35 * ml_score, 1)
        final_risk = self.get_risk_label(final_score) if not self.model_loaded else ml_risk

        # Risk distribution counts
        risk_counts = {
            "safe": sum(1 for i in ingredient_risks if i["risk"] == "safe"),
            "low": sum(1 for i in ingredient_risks if i["risk"] == "low"),
            "medium": sum(1 for i in ingredient_risks if i["risk"] == "medium"),
            "high": sum(1 for i in ingredient_risks if i["risk"] == "high"),
        }

        # Suggestion
        alts = ALTERNATIVES.get(category, [])
        # Prefer cleaner alternatives if high-risk ingredients found
        high_risk_found = any(h["risk"] == "high" for h in harmful)
        if high_risk_found:
            alts = [a for a in alts if "no" in a["reason"].lower() or "natural" in a["reason"].lower() or "homemade" in a["name"].lower()][:3]
        alts = alts[:3]

        # Score badge
        if final_score >= 4.0:
            score_badge = "🟢 Excellent"
            score_color = "green"
        elif final_score >= 3.0:
            score_badge = "🟡 Good"
            score_color = "yellow"
        elif final_score >= 2.0:
            score_badge = "🟠 Moderate"
            score_color = "orange"
        else:
            score_badge = "🔴 Poor"
            score_color = "red"

        return {
            "product_name": product_name,
            "category": category,
            "health_score": final_score,
            "risk_label": final_risk,
            "score_badge": score_badge,
            "score_color": score_color,
            "harmful_ingredients": harmful,
            "allergens": allergens,
            "ingredient_risks": ingredient_risks,
            "risk_counts": risk_counts,
            "alternatives": alts,
            "model_used": "ML + Rule-based" if self.model_loaded else "Rule-based",
            "total_ingredients": len(ingredient_risks),
            "harmful_count": len(harmful),
            "high_risk_count": sum(1 for h in harmful if h["risk"] == "high"),
        }
