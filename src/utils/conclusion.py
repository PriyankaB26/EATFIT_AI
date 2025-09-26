import pandas as pd
import os
import re
import logging
from flask import g

# Set up logging
logger = logging.getLogger(__name__)

# Load nutrients dataset with the exact filename
try:
    df_nutrients = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "nutrients-dataset.csv"), encoding="utf-8-sig")
    logger.info("Successfully loaded nutrients dataset")
except Exception as e:
    logger.error(f"Error loading nutrients dataset: {str(e)}")
    df_nutrients = None

def get_age_column(age):
    """Determine age group column based on age"""
    if 0 <= age <= 6:
        return "0-6 years"
    elif 7 <= age <= 12:
        return "7-12 years"
    elif 13 <= age <= 18:
        return "13-18 years"
    else:
        return "Adults"

def extract_numeric(value):
    """Extract numeric value from string"""
    try:
        return float(re.sub(r"[^\d.]", "", str(value)))
    except ValueError:
        return 0

def check_product_safety(nutrition_data, user_health):
    """
    Check if a product is safe for a person based on their health data.
    Returns warnings and safe components.
    """
    warnings = []
    safe_nutrients = []
    conclusion = " This product appears suitable for your health profile. Enjoy in moderation as part of a balanced diet."
    
    if not user_health:
        return {
            "conclusion": "Log in and update your health profile for personalized recommendations.",
            "warnings": [],
            "safe_nutrients": []
        }
    
    age_column = get_age_column(user_health["age"])
    
    for nutrient, value in nutrition_data.items():
        row = df_nutrients[df_nutrients["Nutrient/chemicals to avoid"].str.lower() == nutrient.replace("_", " ")]
        if not row.empty:
            limit_str = str(row[age_column].values[0]).strip()
            
            if "avoid" in limit_str.lower() or limit_str == "0" or re.match(r"0\s*[gmg]*", limit_str, re.IGNORECASE):
                limit = 0
            else:
                if "-" in limit_str:
                    parts = limit_str.split("-")
                    lower_bound = extract_numeric(parts[0])
                    upper_bound = extract_numeric(parts[1]) if len(parts) > 1 else lower_bound
                    limit = upper_bound
                else:
                    limit = extract_numeric(limit_str)
            
            if limit_str.startswith("≤") or limit == 0:
                if value > limit:
                    warnings.append(f"{nutrient} exceeds limit ({value}g > {limit}g), hence this product is not recommended for you.")
            elif limit_str.startswith("≥"):
                if value < limit:
                    warnings.append(f"{nutrient} is below recommended ({value}g < {limit}g).")
    
    if not warnings:
        return {"conclusion": "All nutrients are within safe limits.", "warnings": [], "safe_nutrients": safe_nutrients}
    
    return {"conclusion": " Some nutrients exceed recommended limits.", "warnings": warnings, "safe_nutrients": safe_nutrients}
