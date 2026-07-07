import pandas as pd

df = pd.read_csv("data/features_s51_s56_pos.csv")
print("Columns:")
print(df.columns.tolist())
print("\nShape:", df.shape)
print("\nFirst row values:")
print(df.iloc[0].to_dict())
