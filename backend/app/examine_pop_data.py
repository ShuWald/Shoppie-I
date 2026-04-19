#!/usr/bin/env python3
"""
Script to examine the POP xlsx files and understand their structure
to extract family and search information dynamically.
"""

import pandas as pd
from pathlib import Path

def examine_pop_files():
    """Examine the structure of POP xlsx files."""
    pop_data_dir = Path("pop_data")
    
    # Check POP_ItemSpecMaster.xlsx
    spec_path = pop_data_dir / "POP_ItemSpecMaster.xlsx"
    if spec_path.exists():
        print("=== POP_ItemSpecMaster.xlsx ===")
        try:
            # Read all sheets to understand structure
            excel_file = pd.ExcelFile(spec_path)
            print(f"Available sheets: {excel_file.sheet_names}")
            
            for sheet_name in excel_file.sheet_names:
                print(f"\n--- Sheet: {sheet_name} ---")
                df = pd.read_excel(spec_path, sheet_name=sheet_name)
                print(f"Shape: {df.shape}")
                print(f"Columns: {list(df.columns)}")
                
                # Show first few rows
                print("Sample data:")
                print(df.head(3).to_string())
                print()
                
        except Exception as e:
            print(f"Error reading POP_ItemSpecMaster.xlsx: {e}")
    
    # Check POP_InventorySnapshot.xlsx
    inv_path = pop_data_dir / "POP_InventorySnapshot.xlsx"
    if inv_path.exists():
        print("=== POP_InventorySnapshot.xlsx ===")
        try:
            excel_file = pd.ExcelFile(inv_path)
            print(f"Available sheets: {excel_file.sheet_names}")
            
            for sheet_name in excel_file.sheet_names:
                print(f"\n--- Sheet: {sheet_name} ---")
                df = pd.read_excel(inv_path, sheet_name=sheet_name)
                print(f"Shape: {df.shape}")
                print(f"Columns: {list(df.columns)}")
                
                # Show first few rows
                print("Sample data:")
                print(df.head(3).to_string())
                print()
                
        except Exception as e:
            print(f"Error reading POP_InventorySnapshot.xlsx: {e}")

if __name__ == "__main__":
    examine_pop_files()
