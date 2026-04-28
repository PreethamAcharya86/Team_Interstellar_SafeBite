# FoodAnalyzer

## Project Overview

FoodAnalyzer is an intelligent food product analysis application that leverages artificial intelligence to assess ingredient safety and provide comprehensive health insights. The application integrates with the Open Food Facts database and uses the Groq API for advanced ingredient analysis and alternative product recommendations.

## Description

FoodAnalyzer is designed to help consumers make informed dietary choices by:

- Analyzing product ingredients for potential health risks
- Detecting harmful additives, synthetic chemicals, and artificial preservatives
- Comparing ingredients against globally banned substance lists
- Generating a comprehensive health risk assessment score
- Identifying potential allergens and food sensitivities
- Recommending healthier alternative products available in Indian markets
- Providing detailed ingredient breakdowns and nutritional insights

The application features a user-friendly web interface that accepts product names or direct ingredient lists and delivers detailed analysis results within seconds.

## Technology Stack

- Backend: Flask (Python)
- Frontend: HTML5, CSS3, JavaScript
- AI Integration: Groq API (LLaMA 3.1 8B)
- Database: Open Food Facts API
- Machine Learning: scikit-learn, NumPy, pandas
- Environment Management: python-dotenv

## Installation

### Prerequisites

- Python 3.10
- pip (Python package manager)
- Git

### Setup Instructions

1. Clone or navigate to the FoodAnalyzer project directory:

```bash
cd FoodAnalyzer
```

2. Create a Python virtual environment:

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install required dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables:

Create a `.env` file in the main FoodAnalyzer folder (if not already present) with the following content:

```
GROQ_API_KEY=your_groq_api_key_here
```

To obtain a Groq API key:

- Visit https://console.groq.com
- Sign up for a free account
- Generate an API key from the dashboard
- Copy the API key and paste it in the `.env` file

## Project Structure

```
FoodAnalyzer/
├── backend/                    # Flask backend server
│   ├── app.py                 # Main application entry point
│   ├── analysis_engine.py     # Ingredient analysis logic
│   ├── groq_integration.py    # Groq API integration
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Web interface files
│   ├── static/                # CSS and JavaScript assets
│   └── index.html             # Main HTML template
├── model_artifacts/           # Pre-trained ML models
├── templates/                 # Flask template files
├── .env                       # Environment configuration (contains API keys)
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Project dependencies
└── README.md                  # This file
```

## How to Run

### 1. Start the Backend Server

From the main FoodAnalyzer directory:

```bash
# Ensure virtual environment is activated
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Navigate to backend directory and run the application
cd backend
python app.py
```

The backend server will start on `http://localhost:5000`

You should see output similar to:

```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### 2. Access the Application

Open your web browser and navigate to:

```
http://localhost:5000
```

### 3. Using the Application

- Enter a product name (e.g., "Parle-G", "Bournvita")
- Select a category (Snacks, Biscuits, or Juice)
- Optionally provide ingredients directly
- Click "Analyze" to get results
- View detailed ingredient analysis, health score, and healthier alternatives

## Features

### Ingredient Analysis

- Fetches real product data from Open Food Facts database
- Extracts and parses ingredient lists
- Identifies harmful additives and preservatives

### Health Risk Assessment

- Calculates overall health risk score (0-100)
- Categorizes ingredients as safe, warning, or harmful
- Provides detailed breakdown of identified risks

### Allergen Detection

- Identifies common allergens (nuts, dairy, gluten, soy)
- Highlights potential cross-contamination risks
- Provides allergen severity information

### Alternative Suggestions

- Recommends healthier product alternatives
- Focuses on products with fewer artificial additives
- Includes budget-friendly options
- All suggestions are for real products available in Indian markets

### Fallback System

- If a product is not found in Open Food Facts, supports direct ingredient input
- Manual ingredient analysis when API lookup fails
- Ensures consistent functionality regardless of data availability

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
