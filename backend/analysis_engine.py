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
        {"name": "Makhana (Fox Nuts)", "brand": "None / Local",
         "reason": "High protein, low fat, zero artificial additives, naturally crunchy"},
        {"name": "Roasted Chana", "brand": "Haldiram / Local",
            "reason": "Natural protein source, high fiber, no preservatives"},
        {"name": "Too Yumm! Multigrain", "brand": "Too Yumm",
            "reason": "Baked not fried, multigrain, fewer additives"},
        {"name": "Cornitos Nacho Chips", "brand": "Cornitos",
            "reason": "Simpler ingredient list, no MSG"},
        {"name": "Dried Fruits & Nuts Mix", "brand": "Happilo / Any",
            "reason": "Completely natural, nutrient-dense, no processing"},
    ],
    "biscuits": [
        {"name": "McVities Digestive", "brand": "McVities",
            "reason": "Whole wheat base, lower sugar, no artificial colors"},
        {"name": "Britannia NutriChoice", "brand": "Britannia",
            "reason": "Multigrain, high fiber, better nutritional profile"},
        {"name": "Homemade Atta Biscuits", "brand": "Homemade",
            "reason": "Complete control over ingredients, no preservatives"},
        {"name": "Annas Ginger Thins", "brand": "Anna's",
            "reason": "Simple ingredients, natural ginger flavor"},
    ],
    "juice": [
        {"name": "Paper Boat Aam Panna", "brand": "Paper Boat",
            "reason": "Traditional Indian recipe, natural spices, minimal additives"},
        {"name": "Raw Pressery Cold Press", "brand": "Raw Pressery",
            "reason": "No added sugar, no preservatives, high vitamin content"},
        {"name": "Fresh Squeezed Juice", "brand": "Home / Juice Bar",
            "reason": "Maximum nutrition, zero additives, completely natural"},
        {"name": "B Natural Mixed Fruit", "brand": "B Natural",
            "reason": "No artificial color/preservatives, better than most packaged juices"},
        {"name": "Coconut Water", "brand": "Any brand / Fresh",
            "reason": "Natural electrolytes, no sugar added, extremely healthy"},
    ]
}

# ── Long-term Health Diseases Database ──────────────────────
INGREDIENT_DISEASE_MAP = {
    # Trans Fats
    "hydrogenated vegetable oil": ["cardiovascular disease", "heart disease", "high cholesterol"],
    "partially hydrogenated": ["cardiovascular disease", "heart disease", "high cholesterol"],
    "vanaspati": ["cardiovascular disease", "heart disease", "high cholesterol"],
    "dalda": ["cardiovascular disease", "heart disease", "high cholesterol"],
    "trans fat": ["cardiovascular disease", "heart disease", "high cholesterol"],

    # High Sugar Content
    "high fructose corn syrup": ["obesity", "type 2 diabetes", "fatty liver disease", "metabolic syndrome"],
    "sugar": ["obesity", "type 2 diabetes", "dental problems", "metabolic syndrome"],
    "corn syrup": ["obesity", "type 2 diabetes", "metabolic syndrome"],

    # Artificial Additives
    "sodium benzoate": ["hyperactivity in children", "asthma", "allergic reactions"],
    "monosodium glutamate": ["migraines", "headaches", "allergic reactions"],
    "msg": ["migraines", "headaches", "allergic reactions"],
    "aspartame": ["headaches", "neurological concerns", "metabolic issues"],
    "artificial color": ["hyperactivity in children", "allergic reactions", "asthma"],
    "red 40": ["hyperactivity in children", "allergic reactions"],
    "yellow 5": ["hyperactivity in children", "allergic reactions"],
    "yellow 6": ["hyperactivity in children", "allergic reactions"],
    "e110": ["hyperactivity in children", "allergic reactions"],
    "e102": ["hyperactivity in children", "allergic reactions"],

    # Preservatives
    "sodium nitrite": ["colorectal cancer risk", "stomach cancer risk"],
    "sodium nitrate": ["colorectal cancer risk", "stomach cancer risk"],
    "e211": ["asthma", "allergic reactions"],
    "e220": ["asthma", "respiratory issues"],
    "sulphur dioxide": ["asthma", "respiratory issues"],

    # Banned/Harmful Substances
    "tbhq": ["vision disturbances", "adhd-like symptoms", "neurological issues"],
    "bha": ["cancer risk", "liver damage", "endocrine disruption"],
    "bht": ["cancer risk", "liver damage", "endocrine disruption"],
    "potassium bromate": ["cancer risk", "kidney damage"],
    "titanium dioxide": ["cancer risk", "inflammation"],

    # Refined Products
    "refined wheat flour": ["type 2 diabetes", "obesity", "heart disease"],
    "maida": ["type 2 diabetes", "obesity", "heart disease"],
    "refined flour": ["type 2 diabetes", "obesity", "heart disease"],

    # Oils & Fats
    "refined palm oil": ["heart disease", "high cholesterol", "cardiovascular disease"],
    "palm oil": ["heart disease", "high cholesterol", "cardiovascular disease"],
}

DISEASE_DESCRIPTIONS = {
    "cardiovascular disease": "Increased risk of heart disease and stroke",
    "heart disease": "Coronary artery disease and related heart conditions",
    "high cholesterol": "Elevated LDL cholesterol levels",
    "obesity": "Excessive weight gain and metabolic complications",
    "type 2 diabetes": "Insulin resistance and blood sugar control issues",
    "fatty liver disease": "Fat accumulation in liver cells",
    "metabolic syndrome": "Cluster of conditions including high blood pressure and blood sugar",
    "hyperactivity in children": "ADHD-like symptoms and behavioral issues in children",
    "asthma": "Respiratory inflammation and breathing difficulties",
    "allergic reactions": "Immune system overresponse",
    "migraines": "Severe headaches with potential nausea",
    "headaches": "Mild to moderate head pain",
    "neurological concerns": "Potential brain and nervous system effects",
    "neurological issues": "Brain and nervous system complications",
    "metabolic issues": "Disrupted metabolism and hormonal balance",
    "colorectal cancer risk": "Increased risk of colon cancer",
    "stomach cancer risk": "Increased risk of gastric cancer",
    "cancer risk": "Potential carcinogenic effects",
    "respiratory issues": "Breathing and lung complications",
    "vision disturbances": "Eye problems and vision changes",
    "adhd-like symptoms": "Attention and hyperactivity symptoms",
    "liver damage": "Hepatic function impairment",
    "kidney damage": "Renal function impairment",
    "endocrine disruption": "Hormonal system disruption",
    "inflammation": "Systemic inflammatory response",
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
        model_dir = os.path.join(os.path.dirname(
            __file__), "../model_artifacts")

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

            missing_files = [f for f in required_files if not os.path.exists(
                os.path.join(model_dir, f))]
            if missing_files:
                raise FileNotFoundError(
                    f"Missing model files: {missing_files}")

            print("✅ All model files found, loading...")
            self.risk_model = joblib.load(
                os.path.join(model_dir, "risk_classifier.pkl"))
            self.score_model = joblib.load(
                os.path.join(model_dir, "score_regressor.pkl"))
            self.tfidf = joblib.load(os.path.join(
                model_dir, "tfidf_vectorizer.pkl"))
            self.le_risk = joblib.load(os.path.join(
                model_dir, "label_encoder_risk.pkl"))
            with open(os.path.join(model_dir, "feature_cols.json")) as f:
                self.feature_cols = json.load(f)
            self.model_loaded = True
            print("✅ ML models loaded successfully!")
            print(f"   - Risk Classifier: {type(self.risk_model).__name__}")
            print(f"   - Score Regressor: {type(self.score_model).__name__}")
            print(
                f"   - TF-IDF Features: {len(self.tfidf.get_feature_names_out())} terms")
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
        parts = [i.strip()
                 for i in re.split(r'[,;]', clean_text) if len(i.strip()) > 2]
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
                num_feat = self._build_numeric_features(
                    clean, harmful, allergens, category)
                num_arr = np.array([[num_feat.get(col, 0)
                                   for col in self.feature_cols]])
                X = np.hstack([text_feat, num_arr])
                ml_risk = self.le_risk.inverse_transform(
                    self.risk_model.predict(X))[0]
                ml_score_raw = float(self.score_model.predict(X)[0])
                ml_score = float(np.clip(ml_score_raw, 0, 5))
            except Exception:
                pass  # Fall back to rule-based

        # Blend scores
        final_score = round(0.65 * rule_score + 0.35 * ml_score, 1)
        final_risk = self.get_risk_label(
            final_score) if not self.model_loaded else ml_risk

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
            alts = [a for a in alts if "no" in a["reason"].lower(
            ) or "natural" in a["reason"].lower() or "homemade" in a["name"].lower()][:3]
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

    def analyze_diseases(self, ingredients_text, health_score, harmful_ingredients):
        """
        Analyze potential long-term health diseases based on ingredients and health score
        Returns a list of diseases with risk levels and descriptions
        """
        clean = self.clean_ingredients(ingredients_text)
        clean_lower = clean.lower()

        diseases = {}
        disease_risk_map = {}  # Track how many high-risk ingredients link to each disease

        # Map ingredients to potential diseases
        for ingredient_name, ingredient_diseases in INGREDIENT_DISEASE_MAP.items():
            if ingredient_name.lower() in clean_lower:
                for disease in ingredient_diseases:
                    if disease not in diseases:
                        diseases[disease] = {"count": 0, "severity": "low"}
                        disease_risk_map[disease] = 0
                    diseases[disease]["count"] += 1

                    # Check if this ingredient is in the harmful list
                    for harmful in harmful_ingredients:
                        if ingredient_name.lower() in harmful["name"].lower():
                            if harmful["risk"] == "high":
                                disease_risk_map[disease] = max(
                                    disease_risk_map[disease], 2)
                            elif harmful["risk"] == "medium":
                                disease_risk_map[disease] = max(
                                    disease_risk_map[disease], 1)

        # Determine disease risk level based on health score and ingredient count
        disease_list = []

        for disease, info in diseases.items():
            # Determine severity based on health score and frequency
            if health_score >= 4.0:
                # Healthy product - minimal disease risk
                if info["count"] >= 3:  # Only if multiple harmful ingredients present
                    severity = "low"
                else:
                    continue
            elif health_score >= 2.5:
                # Moderate product
                if disease_risk_map.get(disease, 0) >= 2:
                    severity = "medium"
                elif info["count"] >= 2:
                    severity = "low"
                else:
                    severity = "low"
            else:
                # Poor product
                if disease_risk_map.get(disease, 0) >= 2:
                    severity = "high"
                elif info["count"] >= 2:
                    severity = "medium"
                else:
                    severity = "low"

            description = DISEASE_DESCRIPTIONS.get(
                disease, f"Long-term health condition related to {disease}")

            disease_list.append({
                "disease": disease.replace("_", " ").title(),
                "risk_level": severity,
                "description": description,
                "ingredient_count": info["count"]
            })

        # Sort by risk level (high > medium > low)
        risk_order = {"high": 0, "medium": 1, "low": 2}
        disease_list.sort(key=lambda x: (risk_order.get(
            x["risk_level"], 3), -x["ingredient_count"]))

        return disease_list

    def get_product_insights(self, product_name, health_score, harmful_ingredients, ingredients_text, category):
        """
        Generate product-specific insights about what's in the product and potential health effects
        Returns structured insights about the product's composition and risks
        """
        clean = self.clean_ingredients(ingredients_text)
        insights = {
            "product_name": product_name,
            "health_score": health_score,
            "main_concerns": [],
            "risk_summary": "",
            "recommendation": "",
            "key_issues": []
        }

        # Analyze what's in the product
        high_risk_ingredients = [h for h in harmful_ingredients if h["risk"] == "high"]
        medium_risk_ingredients = [h for h in harmful_ingredients if h["risk"] == "medium"]

        # Check for specific patterns
        has_trans_fat = any(ing in clean for ing in ["hydrogenated", "vanaspati", "dalda", "trans fat"])
        has_high_sugar = any(ing in clean for ing in ["sugar", "corn syrup", "high fructose"])
        has_msg = any(ing in clean for ing in ["monosodium glutamate", "msg"])
        has_artificial_colors = any(ing in clean for ing in ["artificial color", "e102", "e110", "e122", "e124", "e129", "red 40", "yellow 5", "yellow 6"])
        has_preservatives = any(ing in clean for ing in ["benzoate", "sorbate", "nitrite", "e211", "e220"])
        has_refined_flour = any(ing in clean for ing in ["maida", "refined wheat flour"])

        # Generate main concerns
        if has_trans_fat:
            insights["main_concerns"].append({
                "concern": "⚠️ HIGH: Contains Trans Fats",
                "impact": "Trans fats significantly increase cardiovascular disease risk and raise bad cholesterol",
                "found_in": [h["name"] for h in high_risk_ingredients if "hydrogenated" in h["key"].lower() or "trans" in h["key"].lower()]
            })
            
        if has_high_sugar and category == "juice":
            insights["main_concerns"].append({
                "concern": "⚠️ HIGH: Contains High Sugar",
                "impact": "High sugar content increases risk of Type 2 Diabetes, obesity, and metabolic syndrome",
                "found_in": ["Sugar", "Corn Syrup"]
            })

        if has_msg:
            insights["main_concerns"].append({
                "concern": "🟡 MEDIUM: Contains MSG (Monosodium Glutamate)",
                "impact": "May cause migraines, headaches, and allergic reactions in sensitive individuals",
                "found_in": ["Monosodium Glutamate (MSG)"]
            })

        if has_artificial_colors:
            insights["main_concerns"].append({
                "concern": "🟡 MEDIUM: Contains Artificial Colors",
                "impact": "Linked to hyperactivity in children and allergic reactions",
                "found_in": [h["name"] for h in harmful_ingredients if h["risk"] == "medium" and "color" in h["name"].lower()]
            })

        if has_preservatives:
            insights["main_concerns"].append({
                "concern": "🟡 MEDIUM: Contains Synthetic Preservatives",
                "impact": "May cause asthma, allergic reactions, or other health issues",
                "found_in": [h["name"] for h in harmful_ingredients if "preserv" in h["name"].lower() or "benzoate" in h["key"].lower()]
            })

        # Summary based on health score
        if health_score >= 4.0:
            insights["risk_summary"] = "✅ This product has a healthy composition with minimal harmful ingredients."
        elif health_score >= 3.0:
            insights["risk_summary"] = "🟡 This product is moderately safe but contains some additives. Occasional consumption is okay, but not recommended as a regular staple."
        elif health_score >= 2.0:
            insights["risk_summary"] = "🔴 This product contains concerning levels of harmful ingredients and should be avoided or consumed very rarely."
        else:
            insights["risk_summary"] = "🚫 This product is unsafe for regular consumption due to high levels of harmful additives and unhealthy components."

        # Specific recommendations
        if health_score >= 4.0:
            insights["recommendation"] = "This product is safe for regular consumption. Keep enjoying it, but maintain a balanced diet."
        elif has_trans_fat:
            insights["recommendation"] = "❌ AVOID: This product contains dangerous trans fats. Look for healthier alternatives with vegetable oil instead of hydrogenated oils."
        elif has_high_sugar and health_score < 3.0:
            insights["recommendation"] = "⚠️ LIMIT: This product has high sugar content. Consume sparingly and prefer natural juice or water alternatives."
        elif len(high_risk_ingredients) > 0:
            insights["recommendation"] = f"⚠️ CAUTION: This product contains {len(high_risk_ingredients)} high-risk ingredient(s). Consider healthier alternatives or consume occasionally."
        else:
            insights["recommendation"] = "🤔 Consider healthier options with fewer artificial additives for optimal health."

        # Key issues summary
        if has_trans_fat:
            insights["key_issues"].append("Contains dangerous trans fats")
        if has_high_sugar:
            insights["key_issues"].append("High sugar content")
        if has_msg:
            insights["key_issues"].append("Contains MSG")
        if has_artificial_colors:
            insights["key_issues"].append("Contains artificial colors/dyes")
        if has_preservatives:
            insights["key_issues"].append("Contains chemical preservatives")
        if has_refined_flour:
            insights["key_issues"].append("Made with refined flour")
        if len(high_risk_ingredients) > 0:
            insights["key_issues"].append(f"{len(high_risk_ingredients)} high-risk ingredient(s)")

        return insights
