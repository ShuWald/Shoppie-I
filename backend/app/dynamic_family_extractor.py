#!/usr/bin/env python3
"""
Dynamic family and search term extraction from POP xlsx files.
Replaces hardcoded FAMILY_RULES and INFER_RULES with data-driven extraction.
"""

import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

class DynamicFamilyExtractor:
    """Extracts product families and search terms dynamically from POP data."""
    
    def __init__(self, pop_data_dir: str = "pop_data"):
        self.pop_data_dir = Path(pop_data_dir)
        self.family_mappings = {}
        self.search_term_mappings = {}
        self.category_sources = {}
        
    def extract_families_from_descriptions(self, descriptions: List[str]) -> Dict[str, Dict]:
        """
        Extract families and search terms from product descriptions using pattern matching.
        Returns a dictionary with family information and search terms.
        """
        families = defaultdict(lambda: {"descriptions": [], "search_terms": set()})
        
        for desc in descriptions:
            if not isinstance(desc, str) or not desc.strip():
                continue
                
            family_info = self._extract_family_from_description(desc.strip())
            if family_info:
                family, search_term = family_info
                families[family]["descriptions"].append(desc)
                families[family]["search_terms"].add(search_term)
        
        return dict(families)
    
    def _extract_family_from_description(self, description: str) -> Tuple[str, str]:
        """
        Extract family and search term from a single description.
        Uses pattern matching to identify product families.
        """
        desc_upper = description.upper()
        
        # American Ginseng patterns
        if "GSG" in desc_upper and "TEA" in desc_upper:
            return "American Ginseng Tea", "American ginseng root tea"
        elif "GSG" in desc_upper and "CANDY" in desc_upper:
            return "American Ginseng Candy", "American ginseng candy"
        elif "GSG" in desc_upper and ("SLICES" in desc_upper or "SLICE" in desc_upper):
            return "American Ginseng Root", "American ginseng slices"
        elif "GSG" in desc_upper and "ROOT" in desc_upper:
            return "American Ginseng Root", "American ginseng root"
        elif "AM GSG" in desc_upper:
            return "American Ginseng Root", "American ginseng root"
        elif "AMERICAN GINSENG" in desc_upper:
            return "American Ginseng Root", "American ginseng root"
            
        # European Confections patterns
        elif "FERRERO" in desc_upper:
            return "European Confections", "Ferrero Rocher"
        elif "GAVOTTES" in desc_upper:
            return "European Confections", "Gavottes crepes dentelle"
        elif "KJELDSENS" in desc_upper:
            return "European Confections", "Kjeldsens butter cookies"
        elif "LOACKER GP" in desc_upper:
            return "Loacker", "Loacker Gran Pasticceria"
        elif "LOACKER" in desc_upper:
            return "Loacker", "Loacker wafer hazelnut"
        elif "EGGROLL" in desc_upper or "EGG ROLL" in desc_upper:
            return "European Confections", "egg rolls snack"
            
        # Ginger Chews patterns
        elif "GINGER" in desc_upper and "CHEWS" in desc_upper:
            if "ORIGINAL" in desc_upper:
                return "Ginger Chews", "Prince of Peace ginger chews original"
            elif "LEMON" in desc_upper:
                return "Ginger Chews", "Prince of Peace ginger chews lemon"
            elif "MANGO" in desc_upper:
                return "Ginger Chews", "Prince of Peace ginger chews mango"
            elif "BLOOD" in desc_upper and "ORANGE" in desc_upper:
                return "Ginger Chews", "Prince of Peace ginger chews blood orange"
            elif "LYCHEE" in desc_upper:
                return "Ginger Chews", "Prince of Peace ginger chews lychee"
            elif "PINEAPPLE" in desc_upper and "COCONUT" in desc_upper:
                return "Ginger Chews", "Prince of Peace ginger chews pineapple coconut"
            elif "ASSORTED" in desc_upper:
                return "Ginger Chews", "Prince of Peace ginger chews assorted"
            elif "PLUS" in desc_upper:
                return "Ginger Chews", "Prince of Peace ginger chews plus"
            else:
                return "Ginger Chews", "Prince of Peace ginger chews"
                
        # Ginger Honey Crystals patterns
        elif "GINGER" in desc_upper and ("HONEY" in desc_upper or "H" in desc_upper) and "CYTL" in desc_upper:
            return "Ginger Honey Crystals", "Prince of Peace ginger honey crystals"
            
        # Asian Pantry patterns
        elif "MAZOLA" in desc_upper:
            return "Asian Pantry", "Mazola corn oil"
        elif "TOTOLE" in desc_upper:
            return "Asian Pantry", "Totole chicken bouillon"
            
        # Topical Health patterns
        elif "KWAN LOONG" in desc_upper:
            return "Topical Health", "Kwan Loong oil"
        elif "TIGER BALM" in desc_upper and "PATCH" in desc_upper:
            return "Tiger Balm", "Tiger Balm patch"
        elif "TIGER BALM" in desc_upper:
            return "Tiger Balm", "Tiger Balm"
            
        # Herbal Health Teas patterns
        elif "HT" in desc_upper and "BLOOD" in desc_upper and "PRESSURE" in desc_upper:
            return "Herbal Health Teas", "blood pressure herbal tea"
        elif "HT" in desc_upper and "BLOOD" in desc_upper and "SUGAR" in desc_upper:
            return "Herbal Health Teas", "blood sugar herbal tea"
        elif "HT" in desc_upper and "CHOLESTEROL" in desc_upper:
            return "Herbal Health Teas", "cholesterol herbal tea"
        elif "JASMINE" in desc_upper and "TEA" in desc_upper:
            return "Herbal Health Teas", "Prince of Peace jasmine tea"
        elif "OOLONG" in desc_upper and "TEA" in desc_upper:
            return "Herbal Health Teas", "Prince of Peace oolong tea"
        elif "WHITE" in desc_upper and "TEA" in desc_upper:
            return "Herbal Health Teas", "Prince of Peace white tea"
        elif "GREEN" in desc_upper and "TEA" in desc_upper:
            return "Herbal Health Teas", "Prince of Peace green tea"
        elif "ORGANIC" in desc_upper and "TEA" in desc_upper:
            # Handle organic teas - determine type from other keywords
            if "JASMINE" in desc_upper:
                return "Herbal Health Teas", "Prince of Peace organic jasmine tea"
            elif "OOLONG" in desc_upper:
                return "Herbal Health Teas", "Prince of Peace organic oolong tea"
            elif "WHITE" in desc_upper:
                return "Herbal Health Teas", "Prince of Peace organic white tea"
            elif "GREEN" in desc_upper:
                return "Herbal Health Teas", "Prince of Peace organic green tea"
            else:
                return "Herbal Health Teas", "Prince of Peace organic green tea"
                
        # Default case - try to extract something meaningful
        else:
            return self._extract_generic_family(description)
    
    def _extract_generic_family(self, description: str) -> Tuple[str, str]:
        """Extract family for products that don't match specific patterns."""
        desc_upper = description.upper()
        
        # Look for key brand/product indicators
        if "PRINCE OF PEACE" in desc_upper or "POP" in desc_upper:
            # It's a Prince of Peace product, try to categorize
            if "GINSENG" in desc_upper:
                return "American Ginseng Root", "Prince of Peace American ginseng"
            elif "TEA" in desc_upper:
                return "Herbal Health Teas", "Prince of Peace tea"
            else:
                return "Herbal Health Teas", "Prince of Peace"
        
        # If no specific pattern found, return None
        return None
    
    def get_category_sources(self) -> Dict[str, Tuple[str, ...]]:
        """
        Define which data sources to use for each family category.
        'off' = Open Food Facts (packaged foods, confections, pantry staples)
        'iherb' = iHerb (herbal/supplement products, topicals)
        """
        return {
            "American Ginseng Tea": ("off", "iherb"),
            "American Ginseng Candy": ("off", "iherb"),
            "American Ginseng Root": ("off", "iherb"),
            "European Confections": ("off",),
            "Loacker": ("off",),
            "Ginger Chews": ("off", "iherb"),
            "Ginger Honey Crystals": ("off", "iherb"),
            "Asian Pantry": ("off",),
            "Topical Health": ("iherb",),
            "Tiger Balm": ("iherb",),
            "Herbal Health Teas": ("off", "iherb"),
        }
    
    def load_pop_data(self) -> pd.DataFrame:
        """Load and merge POP data from xlsx files."""
        spec_path = self.pop_data_dir / "POP_ItemSpecMaster.xlsx"
        inv_path = self.pop_data_dir / "POP_InventorySnapshot.xlsx"
        
        if not spec_path.exists():
            raise FileNotFoundError(f"Cannot find {spec_path}")
        
        # Load item specifications
        spec_df = pd.read_excel(spec_path, sheet_name="Item Spec Master")
        spec_df.columns = spec_df.columns.str.strip()
        spec_df = spec_df.rename(columns={
            "Item Number": "item_number",
            "Description": "description",
            "Country of Origin": "country_of_origin",
            "Shelf Life (Months)": "shelf_life",
            "Allergens": "allergens",
            "UPC#": "upc",
        })
        spec_df = spec_df[spec_df["description"].notna()].copy()
        spec_df["item_number"] = spec_df["item_number"].astype(str).str.strip()
        spec_df["description"] = spec_df["description"].astype(str).str.strip()
        
        # Load inventory data if available
        if inv_path.exists():
            inv_sheets = pd.read_excel(inv_path, sheet_name=None)
            site_col_map = {
                "Site 1 - SF": "inv_sf_available",
                "Site 2 - NJ": "inv_nj_available", 
                "Site 3 - LA": "inv_la_available",
            }
            
            for sheet_name, col in site_col_map.items():
                if sheet_name in inv_sheets:
                    inv_df = inv_sheets[sheet_name][["Item Number", "Available"]].copy()
                    inv_df.columns = ["item_number", col]
                    inv_df["item_number"] = inv_df["item_number"].astype(str).str.strip()
                    spec_df = spec_df.merge(inv_df, on="item_number", how="left")
                else:
                    spec_df[col] = None
        else:
            for col in ["inv_sf_available", "inv_nj_available", "inv_la_available"]:
                spec_df[col] = None
        
        return spec_df
    
    def extract_families_and_keywords(self) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
        """
        Extract families and keywords from POP data.
        Returns:
        - family_groups: {family_name: [keywords_list]}
        - category_keywords: [broad_keywords_for_related_queries]
        """
        # Load POP data
        pop_df = self.load_pop_data()
        descriptions = pop_df["description"].tolist()
        
        # Extract families
        families_data = self.extract_families_from_descriptions(descriptions)
        
        # Build family groups for Google Trends (max 5 keywords per group)
        family_groups = {}
        for family, data in families_data.items():
            keywords = list(data["search_terms"])
            if keywords:
                # Split into chunks of 5 for pytrends limit
                for i in range(0, len(keywords), 5):
                    chunk = keywords[i:i+5]
                    label = family if i == 0 else f"{family} ({i//5 + 1})"
                    family_groups[label] = chunk
        
        # Build category keywords for related queries (one broad keyword per family)
        category_keywords = []
        for family in families_data.keys():
            # Use the first/most common search term as the category keyword
            search_terms = list(families_data[family]["search_terms"])
            if search_terms:
                category_keywords.append(search_terms[0])
        
        return family_groups, category_keywords
    
    def build_products_list(self) -> List[Dict]:
        """
        Build products list for ingredients scraper.
        Returns list of dicts with name, category, off_query, iherb_query.
        """
        # Load POP data
        pop_df = self.load_pop_data()
        category_sources = self.get_category_sources()
        
        products = []
        for _, row in pop_df.iterrows():
            desc = row["description"]
            family_info = self._extract_family_from_description(desc)
            
            if family_info:
                family, base_keyword = family_info
                sources = category_sources.get(family, ("off",))
                
                # Build specific search query with size/flavor info
                search_query = self._build_search_query(desc, base_keyword)
                
                products.append({
                    "name": desc,
                    "category": family,
                    "off_query": search_query if "off" in sources else None,
                    "iherb_query": search_query if "iherb" in sources else None,
                })
        
        return products
    
    def _build_search_query(self, description: str, base_keyword: str) -> str:
        """
        Build specific search query by adding size/flavor info to base keyword.
        """
        desc_lower = description.lower()
        
        # Extract size information
        size_patterns = [
            r'(\d+(?:\.\d+)?\s*(?:oz|lb|g|bags?|pcs?|ct))',
            r'(\d+\s*(?:oz|lb|g|bags?|pcs?|ct))',
        ]
        size = ""
        for pattern in size_patterns:
            match = re.search(pattern, desc_lower)
            if match:
                size = match.group(1).strip()
                break
        
        # Extract flavor information
        flavor_keywords = [
            "original", "lemon", "mango", "lychee", "pineapple", "coconut",
            "blood orange", "assorted", "turmeric", "jasmine", "oolong",
            "white", "green", "extra strength", "ultra strength",
            "hazelnut", "cappuccino", "dark", "noisette", "orange"
        ]
        flavor = ""
        for flavor_kw in flavor_keywords:
            if flavor_kw in desc_lower and flavor_kw not in base_keyword.lower():
                flavor = flavor_kw
                break
        
        # Build query
        parts = [base_keyword]
        if flavor:
            parts.append(flavor)
        if size:
            parts.append(size)
        
        return " ".join(parts)

def test_dynamic_extraction():
    """Test the dynamic family extraction."""
    extractor = DynamicFamilyExtractor()
    
    print("=== Testing Dynamic Family Extraction ===")
    
    try:
        # Load POP data
        pop_df = extractor.load_pop_data()
        print(f"Loaded {len(pop_df)} products from POP data")
        
        # Extract families and keywords
        family_groups, category_keywords = extractor.extract_families_and_keywords()
        
        print(f"\nExtracted {len(family_groups)} family groups:")
        for family, keywords in family_groups.items():
            print(f"  {family}: {keywords}")
        
        print(f"\nCategory keywords for related queries:")
        for keyword in category_keywords:
            print(f"  {keyword}")
        
        # Build products list
        products = extractor.build_products_list()
        print(f"\nBuilt {len(products)} products for ingredients scraper")
        
        # Show sample products
        print("\nSample products:")
        for i, product in enumerate(products[:5]):
            print(f"  {i+1}. {product['name']}")
            print(f"     Category: {product['category']}")
            print(f"     OFF Query: {product.get('off_query', 'None')}")
            print(f"     iHerb Query: {product.get('iherb_query', 'None')}")
            print()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dynamic_extraction()
