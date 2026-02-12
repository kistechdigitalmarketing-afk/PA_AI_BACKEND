import joblib
import pandas as pd


model = joblib.load("app/model_brain.pkl")

print(" Inspection")
print("-" * 30)


print(f"Model Type: {type(model).__name__}")

print(f"Number of Estimators (Trees): {len(model.estimators_)}")
print(f"Contamination (Expected Anomaly %): {model.contamination}")
print(f"Features used: {model.n_features_in_}")


test_data = pd.DataFrame([
    [1.0, 0.0, 0.0], 
    [0.1, 0.9, 0.8]  
], columns=['completion_rate', 'overdue_rate', 'rejection_rate'])



scores = model.decision_function(test_data)

print("\n--- Testing Logic ---")
print(f"Perfect User Score: {scores[0]:.4f} (Should be Positive/Normal)")
print(f"Struggling User Score: {scores[1]:.4f} (Should be Negative/Anomaly)")