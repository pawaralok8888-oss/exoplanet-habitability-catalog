import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report
import pickle

# ---------------------------------------------------------
# 1. Load Module B's feature-engineered dataset
# ---------------------------------------------------------
INPUT_FILE = "data/processed/exoplanets_features.csv"
df = pd.read_csv(INPUT_FILE)

# ---------------------------------------------------------
# 2. Build the target column
# P_HABITABLE: 0 = not habitable, 1 = habitable, 2 = maybe habitable
# We collapse 1 and 2 into a single "potentially habitable" class
# so this becomes clean binary classification.
# ---------------------------------------------------------
df["target"] = df["P_HABITABLE"].apply(lambda x: 1 if x in [1, 2] else 0)

print("Target class balance:")
print(df["target"].value_counts())
print()

# ---------------------------------------------------------
# 3. Choose features
# Using a mix of Module B's engineered features + core planetary/stellar columns
# ---------------------------------------------------------
feature_columns = [
    "esi_score",
    "habitable_zone_flag",
    "P_RADIUS",
    "P_MASS",
    "P_TEMP_EQUIL",
    "P_PERIOD",
    "P_FLUX",
    "S_TEMPERATURE",
    "S_RADIUS",
    "S_MASS",
]

X = df[feature_columns]
y = df["target"]

# ---------------------------------------------------------
# 4. Handle missing values
# Many rows have NaN esi_score / other fields — impute with median
# rather than dropping, since dropping would lose most habitable-zone
# planets that don't have a full esi_score.
# ---------------------------------------------------------
X = X.fillna(X.median(numeric_only=True))

# ---------------------------------------------------------
# 5. Train/test split
# stratify=y keeps the same habitable/not-habitable ratio in both
# train and test sets — important given how imbalanced this is.
# ---------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ---------------------------------------------------------
# 6. Train Random Forest
# class_weight="balanced" tells the model to pay more attention to
# the rare habitable class instead of ignoring it.
# ---------------------------------------------------------
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
)
model.fit(X_train, y_train)

# ---------------------------------------------------------
# 7. Evaluate honestly
# ---------------------------------------------------------
preds = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, preds))
print("Precision:", precision_score(y_test, preds, zero_division=0))
print("Recall:", recall_score(y_test, preds, zero_division=0))
print()
print("Full report:")
print(classification_report(y_test, preds, zero_division=0))

# ---------------------------------------------------------
# 8. Feature importance (good for your report/demo)
# ---------------------------------------------------------
importances = pd.Series(model.feature_importances_, index=feature_columns)
print("Feature importance:")
print(importances.sort_values(ascending=False))

# ---------------------------------------------------------
# 9. Save the trained model
# ---------------------------------------------------------
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print()
print("Model saved as model.pkl")