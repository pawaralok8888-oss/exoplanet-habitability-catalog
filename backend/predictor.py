"""Load and call the trained preprocessing-plus-classifier pipeline."""

import json
import os
import pickle
from functools import lru_cache

import pandas as pd
from model.feature_contract import FEATURE_COLUMNS, FEATURE_CONTRACT_VERSION


MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model.pkl"))
MODEL_METADATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "model", "metadata.json")
)


@lru_cache(maxsize=1)
def _load_model():
    try:
        with open(MODEL_METADATA_PATH, encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)

        with open(MODEL_PATH, "rb") as model_file:
            model = pickle.load(model_file)
    except (OSError, pickle.PickleError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "The model or its metadata is unavailable; train the model first"
        ) from exc

    if metadata.get("feature_contract_version") != FEATURE_CONTRACT_VERSION:
        raise RuntimeError(
            "The model uses a different feature contract; retrain it"
        )

    if metadata.get("feature_columns") != FEATURE_COLUMNS:
        raise RuntimeError(
            "The model feature list does not match the application; retrain it"
        )

    return model

def predict_habitability(feature_row):
    model = _load_model()
    if not hasattr(model, "predict_proba"):
        raise RuntimeError("The saved model is incompatible; retrain it using model/train_model.py")
    try:
        frame = pd.DataFrame([feature_row], columns=FEATURE_COLUMNS)
        probability = model.predict_proba(frame)[0][1]
    except Exception as exc:
        raise RuntimeError("Model prediction failed; verify the saved model and feature contract") from exc
    return float(probability)
