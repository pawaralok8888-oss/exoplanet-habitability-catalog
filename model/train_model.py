"""Train and save the complete preprocessing + classifier pipeline."""
import json
from datetime import datetime, timezone
from pathlib import Path
import pickle

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from feature_contract import FEATURE_COLUMNS, FEATURE_CONTRACT_VERSION

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "exoplanets_features.csv"
MODEL_FILE = PROJECT_ROOT / "model.pkl"
MODEL_VERSION = "1.0.0"
MODEL_METADATA_FILE = PROJECT_ROOT / "model" / "metadata.json"


def main():
    df = pd.read_csv(INPUT_FILE)
    df["target"] = df["P_HABITABLE"].isin([1, 2]).astype(int)
    X = df[FEATURE_COLUMNS]
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("classifier", RandomForestClassifier(
            n_estimators=200, random_state=42, class_weight="balanced"
        )),
    ])
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, predictions))
    print("Precision:", precision_score(y_test, predictions, zero_division=0))
    print("Recall:", recall_score(y_test, predictions, zero_division=0))
    print(classification_report(y_test, predictions, zero_division=0))

    with MODEL_FILE.open("wb") as model_file:
        pickle.dump(pipeline, model_file)
    print(f"Saved full prediction pipeline to {MODEL_FILE}")

    metadata = {
        "model_version": MODEL_VERSION,
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "feature_columns": FEATURE_COLUMNS,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    with MODEL_METADATA_FILE.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2)
        metadata_file.write("\n")

if __name__ == "__main__":
    main()
