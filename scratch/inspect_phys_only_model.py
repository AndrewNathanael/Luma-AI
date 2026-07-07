from rppg_stress.ml import load_model_bundle

bundle = load_model_bundle("models/stress_model_s51_s56_physiology_only.joblib")
print("Model Name:", bundle.model_name)
print("Labels:", bundle.labels)
print("\nExpected Feature Columns:")
for i, col in enumerate(bundle.feature_columns):
    print(f"  {i+1}. {col}")
