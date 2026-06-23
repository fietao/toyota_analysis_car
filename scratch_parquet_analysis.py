"""Analyze parquet totals by dimension."""
import sys, io, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

fuel = pd.read_parquet(r'backend/test_fuel_cleaned.parquet')
model = pd.read_parquet(r'backend/test_model_cleaned.parquet')

print('=== test_fuel_cleaned.parquet ===')
print(f'Total rows: {len(fuel):,}')
print(f'Columns: {list(fuel.columns)}')
print(f'Grand Total: {fuel["jumnuan"].sum() if "jumnuan" in fuel.columns else fuel["จำนวนรถ"].sum():,}')
print()
print('By year:')
year_col = [c for c in fuel.columns if 'ปี' in c or 'year' in c.lower() or 'pi' in c.lower()]
print(f'  year-like columns: {year_col}')
for col in year_col:
    print(fuel.groupby(col)['จำนวนรถ'].sum().to_string())

print()
print('By month:')
month_col = [c for c in fuel.columns if 'เดือน' in c or 'month' in c.lower()]
print(f'  month-like columns: {month_col}')
for col in month_col:
    print(fuel.groupby(col)['จำนวนรถ'].sum().sort_values(ascending=False).to_string())

print()
print('By vehicle type:')
ry_col = [c for c in fuel.columns if 'ประเภทรถ' in c or 'type' in c.lower()]
print(f'  type-like columns: {ry_col}')
for col in ry_col:
    print(fuel.groupby(col)['จำนวนรถ'].sum().sort_values(ascending=False).to_string())

print()
print('By fuel type:')
fuel_col = [c for c in fuel.columns if 'เชื้อเพลิง' in c or 'fuel' in c.lower()]
print(f'  fuel-like columns: {fuel_col}')
for col in fuel_col:
    print(fuel.groupby(col)['จำนวนรถ'].sum().sort_values(ascending=False).to_string())

print()
print('By Powertrain (if present):')
pt_col = [c for c in fuel.columns if 'owertrain' in c or c == 'PT']
for col in pt_col:
    print(fuel.groupby(col)['จำนวนรถ'].sum().sort_values(ascending=False).to_string())

print()
print('='*60)
print('=== test_model_cleaned.parquet ===')
print(f'Total rows: {len(model):,}')
print(f'Columns: {list(model.columns)}')
print(f'Grand Total: {model["จำนวนรถ"].sum():,}')
print()
print('By year:')
year_col_m = [c for c in model.columns if 'ปี' in c or 'year' in c.lower()]
for col in year_col_m:
    print(model.groupby(col)['จำนวนรถ'].sum().to_string())

print()
print('By vehicle type:')
ry_col_m = [c for c in model.columns if 'ประเภทรถ' in c]
for col in ry_col_m:
    print(model.groupby(col)['จำนวนรถ'].sum().sort_values(ascending=False).to_string())

print()
print('By fuel:')
fuel_col_m = [c for c in model.columns if 'เชื้อเพลิง' in c]
for col in fuel_col_m:
    print(model.groupby(col)['จำนวนรถ'].sum().sort_values(ascending=False).to_string())

print()
print('By Powertrain:')
pt_col_m = [c for c in model.columns if 'owertrain' in c or c == 'PT']
for col in pt_col_m:
    print(model.groupby(col)['จำนวนรถ'].sum().sort_values(ascending=False).to_string())
