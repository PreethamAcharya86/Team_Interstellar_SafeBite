# SafeBite

## Project Overview

SafeBite is an intelligent food product analysis application that leverages artificial intelligence to assess ingredient safety and provide comprehensive health insights. The application integrates with the Open Food Facts database and uses the Groq API for advanced ingredient analysis and alternative product recommendations.

## Description

SafeBite is designed to help consumers make informed dietary choices by:

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

1. Clone or navigate to the SafeBite project directory:

```bash
cd Team_Interstellar_SafeBite
```

2. Install required dependencies:

```bash
pip install -r requirements.txt
```


## Project Structure

```
Team_Interstellar_SafeBite/
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

From the main Team_Interstellar_SafeBite directory:

```bash
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
- Compare two Food Products 

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

###  Product Comparison
- Compares two food products side-by-side
- Highlights differences in sugar, fat, sodium, and additives
- Shows which product is healthier overall
- Gives a quick “Better Choice” recommendation