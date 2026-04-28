#!/usr/bin/env python3
"""
Test script for FoodAnalyzer API
Tests both direct ingredient analysis and product name lookup
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*60)
    print("🏥 TEST: Health Check")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_direct_analysis():
    """Test direct ingredient analysis (no Groq needed)"""
    print("\n" + "="*60)
    print("🔬 TEST: Direct Ingredient Analysis")
    print("="*60)
    
    test_data = {
        "product_name": "Kurkure Masala Munch",
        "category": "snacks",
        "ingredients": "Cornmeal, Edible Vegetable Oil, Rice Meal, Wheat Flour, Spices (3%), Salt, Sugar, Maize Flour, Monosodium Glutamate, Artificial Flavour (Masala), TBHQ, Yellow 5, Sodium Benzoate"
    }
    
    try:
        print(f"\n📤 Sending request:")
        print(json.dumps(test_data, indent=2))
        
        response = requests.post(f"{BASE_URL}/api/analyze-direct", json=test_data)
        print(f"\n📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Analysis Result:")
            print(f"   Product: {result.get('product_name')}")
            print(f"   Health Score: {result.get('health_score')}/5")
            print(f"   Risk Level: {result.get('risk_label')}")
            print(f"   Model Used: {result.get('model_used')}")
            print(f"   Harmful Ingredients Found: {result.get('harmful_count')}")
            print(f"   Allergens: {result.get('allergens')}")
            
            print(f"\n   Harmful Ingredients:")
            for h in result.get('harmful_ingredients', [])[:5]:
                print(f"      - {h['name']}: {h['risk'].upper()} - {h['reason']}")
            
            print(f"\n   Alternatives Suggested:")
            for alt in result.get('alternatives', []):
                print(f"      - {alt.get('name', 'N/A')}: {alt.get('reason', 'N/A')}")
            
            print(f"\n   Badge: {result.get('score_badge')}")
            print(f"   Source: {result.get('ingredients_source')}")
            
            return True
        else:
            print(f"❌ Error Response:")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_sample_products():
    """Test getting sample products"""
    print("\n" + "="*60)
    print("📦 TEST: Sample Products")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/products/sample")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            samples = response.json()
            print(f"✅ Fetched {len(samples)} sample products:")
            for sample in samples[:3]:
                print(f"\n   Product: {sample['product_name']}")
                print(f"   Category: {sample['category']}")
                print(f"   Ingredients: {sample['ingredients'][:60]}...")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_analyze_with_name_and_ingredients():
    """Test analyzing a product with both name and ingredients"""
    print("\n" + "="*60)
    print("🔬 TEST: Analyze with Name + Ingredients (Fallback)")
    print("="*60)
    
    test_data = {
        "product_name": "Test Biscuit",
        "category": "biscuits",
        "ingredients": "Refined Wheat Flour, Sugar, Edible Vegetable Oil, Vanaspati, Artificial Flavor, E110, Sodium Benzoate, Potassium Bromate"
    }
    
    try:
        print(f"\n📤 Sending request with direct ingredients:")
        print(json.dumps(test_data, indent=2))
        
        response = requests.post(f"{BASE_URL}/api/analyze", json=test_data)
        print(f"\n📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Analysis Result:")
            print(f"   Product: {result.get('product_name')}")
            print(f"   Health Score: {result.get('health_score')}/5")
            print(f"   Risk Level: {result.get('risk_label')}")
            print(f"   Score Badge: {result.get('score_badge')}")
            print(f"   Harmful Count: {result.get('harmful_count')}")
            
            harmful = result.get('harmful_ingredients', [])
            if harmful:
                print(f"\n   Harmful Ingredients ({len(harmful)} found):")
                for h in harmful[:5]:
                    print(f"      - {h['name']}: {h['risk'].upper()}")
            
            return True
        else:
            print(f"❌ Error Response:")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "FOODANALYZER API TESTS" + " "*21 + "║")
    print("╚" + "="*58 + "╝")
    
    results = {
        "Health Check": test_health_check(),
        "Direct Analysis": test_direct_analysis(),
        "Sample Products": test_sample_products(),
        "Analyze with Fallback": test_analyze_with_name_and_ingredients(),
    }
    
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:12} | {test_name}")
    
    print("-"*60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! API is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")


if __name__ == "__main__":
    print("🚀 Starting FoodAnalyzer API Tests...")
    print("Make sure the Flask app is running on http://127.0.0.1:5000")
    
    run_all_tests()
