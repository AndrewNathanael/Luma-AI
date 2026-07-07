from rppg_stress.ml import load_model_bundle, random_forest_feature_importance

bundle = load_model_bundle("models/stress_model_s51_s56.joblib")
imp = random_forest_feature_importance(bundle)
print(imp.to_string())
