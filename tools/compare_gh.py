import pandas as pd

# File paths
refer_file_path = 'C:/dev/ai-reading-car-analysis/refer/202605_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569 - Model.xlsx'
test_file_path = 'C:/dev/ai-reading-car-analysis/test_model_1.xlsx'

# Load data from both files
refer_df = pd.read_excel(refer_file_path, sheet_name='Data', header=6)
test_df = pd.read_excel(test_file_path, sheet_name='Data')

# Select relevant columns (G and H)
refer_col_h = refer_df.iloc[:, 7]  # Column G is index 6, Column H is index 7
test_col_h = test_df['รุ่นรถ2']  # Column H

# Find differences
missing_in_test = refer_col_h[~refer_col_h.isin(test_col_h)]
extra_in_test = test_col_h[~test_col_h.isin(refer_col_h)]

# Print results
print("Values in reference file but not in test file:")
print(missing_in_test.head(30))

print("\nValues in test file but not in reference file:")
print(extra_in_test.head(30))

# Summary
print(f"\nSummary:")
print(f"Total unique values in reference file: {refer_col_h.nunique()}")
print(f"Total unique values in test file: {test_col_h.nunique()}")
print(f"Values only in reference file: {missing_in_test.count()}")
print(f"Values only in test file: {extra_in_test.count()}")
