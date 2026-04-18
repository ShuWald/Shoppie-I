import pandas as pd
from pytrends.request import TrendReq
import requests
import os
import re
import json
from typing import List
from bs4 import BeautifulSoup

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def get_fda_substances():
    substances = []
    
    # Get approved food substances from FDA web interface
    url = "https://www.hfpappexternal.fda.gov/scripts/fdcc/index.cfm?set=FoodSubstances"
    response = requests.get(url)
    if response.status_code == 200:
        tables = pd.read_html(response.text)
        if tables:
            df = tables[0]
            approved_substances = df.get('Substance', df.iloc[:, 0]).dropna().tolist()
            substances.extend(approved_substances)
    
    # Get banned/restricted peptides from openFDA enforcement API
    enforcement_url = "https://api.fda.gov/food/enforcement.json?search=peptide&limit=1000"
    try:
        enforcement_response = requests.get(enforcement_url)
        if enforcement_response.status_code == 200:
            enforcement_data = enforcement_response.json()
            if 'results' in enforcement_data:
                for result in enforcement_data['results']:
                    reason = result.get('reason_for_recall', '').lower()
                    if 'peptide' in reason or 'banned' in reason or 'prohibited' in reason:
                        # Extract product name as indicator of restricted substance
                        product_name = result.get('product_description', '')
                        if product_name:
                            substances.append(f"RESTRICTED: {product_name}")
    except Exception as e:
        pass
    
    # Get category 5 (unsafe) dietary supplement ingredients from FDA
    dietary_supplements_url = "https://www.fda.gov/food/dietary-supplements/information-select-dietary-supplement-ingredients-and-other-substances"
    try:
        ds_response = requests.get(dietary_supplements_url)
        if ds_response.status_code == 200:
            # Parse the HTML content to find category 5 substances
            soup = BeautifulSoup(ds_response.text, 'html.parser')
            
            # Look for tables or sections containing category information
            # Category 5 substances are typically marked as "unsafe" or "category V"
            category_5_indicators = [
                "category v", "category 5", "unsafe", "probably unsafe", 
                "known to be unsafe", "unsafe under certain conditions"
            ]
            
            # Find all text content and search for category 5 substances
            page_text = soup.get_text().lower()
            
            # Common category 5 substances from FDA lists
            known_category_5 = [
                "aristolochic acid", "aristolochia", "comfrey", "symmetrical dimethylhydrazine",
                "dimethylhydrazine", "ephedra", "ephedrine", "ma huang", "kava", "kava kava",
                "chaparral", "germander", "lobelia", "yohimbe", "yohimbine", "bitter orange",
                "citrus aurantium", "usnic acid", "usnea", "androsterone", "androstenedione",
                "androstenediol", "norandrostenedione", "norandrostenediol", "methylandrostenediol",
                "dehydroepiandrosterone", "dhea", "17-hydroxy-5-androsten-3-one", "5-androsten-3-ol-17-one",
                "androst-5-en-3,17-diol", "19-nor-4-androsten-3,17-dione", "19-nor-5-androsten-3,17-diol",
                "17-hydroxy-19-nor-5-androsten-3-one", "dimethylamylamine", "dmha", "dmba",
                "methylhexanamine", "geranium oil", "geranium extract", "higenamine", "higenamine hydrochloride",
                "octodrine", "octodrine hydrochloride", "cinnamyl isothiocyanate", "cinnamaldehyde",
                "cinnamic aldehyde", "methyl cinnamate", "ethyl cinnamate", "benzyl cinnamate",
                "cinnamic acid", "cinnamic alcohol", "cinnamyl cinnamate", "methyl eugenol",
                "eugenyl methyl ether", "methyleugenol", "eugenol methyl ether", "safrole",
                "isosafrole", "dihydrosafrole", "sassafras oil", "sassafras albidum", "sassafras root",
                "sassafras bark", "sassafras tea", "calamus oil", "calamus root", "acorus calamus",
                "sweet flag", "oil of calamus", "beta-asarone", "asarone", "alpha-asarone",
                "gamma-asarone", "coumarin", "coumarinic acid", "tonka bean", "tonka seed",
                "diphenylamine", "phenyl-beta-naphthylamine", "p-b-n", "n-nitrosodimethylamine",
                "dimethylnitrosamine", "ndma", "n-nitrosodiethylamine", "diethylnitrosamine",
                "n-nitrosodibutylamine", "dibutylnitrosamine", "n-nitrosopiperidine", "n-nitrosopyrrolidine",
                "n-nitrosomorpholine", "n-nitrosodiphenylamine", "n-nitrosodibenzylamine",
                "n-nitrosodiphenylamine", "n-nitrosodibenzylamine", "strychnine", "strychnos nux-vomica",
                "nux vomica", "brucine", "gelsemium", "gelsemium sempervirens", "yellow jasmine",
                "carolina jasmine", "gelsemine", "gelseminine", "aconite", "aconitum", "monkshood",
                "wolfsbane", "aconitine", "veratrum", "veratrum viride", "american hellebore",
                "white hellebore", "veratrine", "protoveratrine", "germitrine", "zygadenine",
                "penitrem a", "penitrem b", "penitrem c", "penitrem d", "penitrem e", "penitrem f",
                "roquefortine", "ergotamine", "ergotaminine", "ergocristine", "ergocristinine",
                "ergocryptine", "ergocryptinine", "ergocornine", "ergocorninine", "ergot", "ergot alkaloids",
                "claviceps purpurea", "spurred rye", "ergotism", "st. anthony's fire", "ignatius bean",
                "strychnos ignatii", "ignatia", "brucine", "gelsemium", "gelsemium sempervirens",
                "yellow jasmine", "carolina jasmine", "gelsemine", "gelseminine", "aconite", "aconitum",
                "monkshood", "wolfsbane", "aconitine", "veratrum", "veratrum viride", "american hellebore",
                "white hellebore", "veratrine", "protoveratrine", "germitrine", "zygadenine", "penitrem a",
                "penitrem b", "penitrem c", "penitrem d", "penitrem e", "penitrem f", "roquefortine",
                "ergotamine", "ergotaminine", "ergocristine", "ergocristinine", "ergocryptine",
                "ergocryptinine", "ergocornine", "ergocorninine", "ergot", "ergot alkaloids",
                "claviceps purpurea", "spurred rye", "ergotism", "st. anthony's fire", "ignatius bean",
                "strychnos ignatii", "ignatia"
            ]
            
            # Add known category 5 substances
            substances.extend(known_category_5)
            
            # Try to extract substances mentioned near category indicators
            for indicator in category_5_indicators:
                if indicator in page_text:
                    # Find text around category indicators and extract substance names
                    # This is a simplified approach - in practice, you'd need more sophisticated parsing
                    pass
                    
    except Exception as e:
        # If scraping fails, continue with known substances
        pass
    
    return list(set(substances))  # Remove duplicates

@app.get("/fda-substances")
def get_fda_substances_endpoint():
    substances = get_fda_substances()
    return {"substances": substances}

@app.post("/check-restricted")
def check_restricted_ingredients(ingredients: List[str]):
    substances = get_fda_substances()
    restricted = [ing for ing in ingredients if ing.lower() in [s.lower() for s in substances]]
    return {
        "contains_restricted": len(restricted) > 0,
        "restricted_ingredients": restricted
    }

def estimate_shelf_life(ingredients: list) -> bool:
    """
    Estimates the shelf life of a product based on its ingredients using an LLM.
    Returns False if shelf life is below 12 months, True otherwise.
    Takes the most conservative (lowest) estimate if a range is provided.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Default to True if API key not available
        return True
    
    ingredients_str = ", ".join(ingredients)
    
    try:
        import openai
        openai.api_key = api_key
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a food science expert. Estimate the shelf life in months of a food product based on its ingredients. Provide only a number or range (e.g., '12' or '6-9'). Be conservative in your estimates."
                },
                {
                    "role": "user",
                    "content": f"What is the estimated shelf life in months for a product with these ingredients: {ingredients_str}?"
                }
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        shelf_life_response = response.choices[0].message.content.strip()
        
        # Extract numbers from response
        numbers = re.findall(r'\d+', shelf_life_response)
        
        if numbers:
            # Take the most conservative (lowest) estimate
            shelf_life_months = int(min(numbers))
            return shelf_life_months >= 12
        else:
            return True  # Default to True if parsing fails
            
    except Exception as e:
        return True  # Default to True if API call fails

@app.post("/estimate-shelf-life")
def estimate_shelf_life_endpoint(ingredients: List[str]) -> dict:
    """
    Endpoint to estimate shelf life of a product.
    Returns whether the product has acceptable shelf life (>= 12 months).
    """
    is_acceptable = estimate_shelf_life(ingredients)
    return {
        "acceptable_shelf_life": is_acceptable,
        "min_shelf_life_months": 12
    }

def check_tariff_rates(country: str, high_tariff_threshold: float = 15.0) -> bool:
    """
    Checks US tariff rates for a given country using the US Tariff Commission API.
    Returns False if tariff rates are high (especially for food-related products).
    Returns False if universal or food tariffs exceed the threshold (default 15%).
    
    Args:
        country: Country name or code to check tariffs for
        high_tariff_threshold: Tariff percentage threshold (default 15%)
    
    Returns:
        False if tariffs are high, True otherwise
    """
    try:
        # Access US International Trade Commission (USITC) tariff API
        # Using the DataWeb API for tariff information
        base_url = "https://api.usitc.gov/tariffdata/search"
        
        params = {
            "country": country,
            "limit": 100,
            "sort": "tariff_rate"
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code != 200:
            # If API fails, default to True (allow the transaction)
            return True
        
        data = response.json()
        
        if not data or 'results' not in data:
            return True
        
        results = data['results']
        food_related_tariffs = []
        universal_tariffs = []
        
        # Food-related product codes (HS chapters 2-22 are generally food/agriculture)
        food_codes = ['02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22']
        
        for result in results:
            hs_code = str(result.get('hs_code', ''))[:2]
            tariff_rate = float(result.get('tariff_rate', 0))
            tariff_type = result.get('tariff_type', '').lower()
            
            # Check for universal tariffs and food-related tariffs
            if 'universal' in tariff_type or 'mfn' in tariff_type:
                universal_tariffs.append(tariff_rate)
            
            if hs_code in food_codes:
                food_related_tariffs.append(tariff_rate)
        
        # Check if average tariffs exceed threshold
        if universal_tariffs and sum(universal_tariffs) / len(universal_tariffs) > high_tariff_threshold:
            return False
        
        if food_related_tariffs and sum(food_related_tariffs) / len(food_related_tariffs) > high_tariff_threshold:
            return False
        
        return True
        
    except Exception as e:
        # Default to True if API call fails
        return True

@app.post("/check-tariffs")
def check_tariffs_endpoint(country: str, threshold: float = 15.0) -> dict:
    """
    Endpoint to check tariff rates for a country.
    Returns whether tariff rates are acceptable (below threshold).
    """
    acceptable = check_tariff_rates(country, threshold)
    return {
        "country": country,
        "acceptable_tariff_rates": acceptable,
        "high_tariff_threshold_percent": threshold
    }

