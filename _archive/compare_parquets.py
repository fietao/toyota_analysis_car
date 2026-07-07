import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

df_m = pd.read_parquet('backend/test_model_cleaned.parquet')
df_f = pd.read_parquet('backend/test_fuel_cleaned.parquet')

m_grp = df_m.groupby(['ปี', 'เดือน', 'ประเภทรถ', 'ชนิดเชื้อเพลิง'])['จำนวนรถ'].sum().reset_index()
f_grp = df_f.groupby(['ปี', 'เดือน', 'ประเภทรถ', 'ชนิดเชื้อเพลิง'])['จำนวนรถ'].sum().reset_index()

merged = pd.merge(m_grp, f_grp, on=['ปี', 'เดือน', 'ประเภทรถ', 'ชนิดเชื้อเพลิง'], suffixes=('_m', '_f'), how='outer').fillna(0)
merged['diff'] = merged['จำนวนรถ_m'] - merged['จำนวนรถ_f']
diffs = merged[merged['diff'] != 0]

print("Differences between model and fuel parquets:")
print(diffs.sort_values('diff', ascending=False).head(20).to_string())

# Now compare to Excel totals, total is ~ 14,601,983
m_total = df_m['จำนวนรถ'].sum()
f_total = df_f['จำนวนรถ'].sum()
print(f"Model Total: {m_total:,}")
print(f"Fuel Total:  {f_total:,}")
print(f"Excel Total: 14,601,983")
print(f"Diff (Excel - Model): {14601983 - m_total:,}")
