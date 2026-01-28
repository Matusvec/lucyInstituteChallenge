"""
Quick Dataset Explorer
Scans all CSV/Excel files and shows a summary of each
"""
import os
import pandas as pd
from pathlib import Path

datasets_path = Path("Datasets")

def explore_file(filepath):
    print(f"\n{'='*80}")
    print(f"📁 {filepath}")
    print('='*80)
    
    try:
        # Read file based on extension
        if filepath.suffix.lower() == '.csv':
            df = pd.read_csv(filepath, nrows=5, encoding='utf-8', on_bad_lines='skip')
            df_full = pd.read_csv(filepath, encoding='utf-8', on_bad_lines='skip', low_memory=False)
        elif filepath.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath, nrows=5)
            df_full = pd.read_excel(filepath)
        else:
            print("Unsupported file type")
            return
        
        # Basic info
        print(f"\n📊 Shape: {df_full.shape[0]:,} rows × {df_full.shape[1]} columns")
        print(f"💾 File size: {filepath.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Columns
        print(f"\n📋 Columns ({len(df_full.columns)}):")
        for i, col in enumerate(df_full.columns[:20]):  # Show first 20 columns
            dtype = df_full[col].dtype
            non_null = df_full[col].notna().sum()
            print(f"   {i+1}. {col} ({dtype}) - {non_null:,} non-null")
        if len(df_full.columns) > 20:
            print(f"   ... and {len(df_full.columns) - 20} more columns")
        
        # Sample data
        print(f"\n🔍 First 3 rows:")
        print(df.head(3).to_string())
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")

# Find all data files
print("🔎 Scanning for datasets...\n")
data_files = list(datasets_path.rglob("*.csv")) + list(datasets_path.rglob("*.xlsx")) + list(datasets_path.rglob("*.xls"))

print(f"Found {len(data_files)} data files:")
for f in data_files:
    print(f"  - {f}")

# Explore each file
for filepath in data_files:
    explore_file(filepath)

print("\n" + "="*80)
print("✅ Exploration complete!")
