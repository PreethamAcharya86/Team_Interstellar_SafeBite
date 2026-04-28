# SafeBite

## Project Overview

* AI tool that analyzes product ingredients
* Detects harmful additives and synthetic chemicals
* Compares global banned ingredient lists
* Provides a health risk score
* Allergy alert system
* Suggests healthier alternatives

## First Iteration (MVP)

### Groq AI Integration

* Integrated Groq LLama 3.1 8B Instant model
* Automatic ingredient extraction via Open Food Facts
* AI-based healthier alternative suggestions
* Fallback to manual ingredient input when Groq fails

### ML Model Integration

* Loaded models from `model_artifacts/`
* Implemented hybrid scoring system:

  * 65% rule-based
  * 35% machine learning

## Run Command
python backend/app.py
