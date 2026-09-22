from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "snapshot" / "cars.csv"
MODEL_PATH = ROOT / "artifacts" / "model.joblib"
METADATA_PATH = ROOT / "artifacts" / "model_metadata.json"
EVALUATION_PATH = ROOT / "reports" / "model_evaluation.json"
FIGURES_PATH = ROOT / "reports" / "figures"
EXPECTED_DATA_SHA256 = "25854afc3ef8b6c6a0349bf7f422c40dacb9bec60a8b318462737ebf9edcc5ea"
RANDOM_STATE = 113
FEATURE_NAMES = ["make", "model", "model_year", "mileage_miles", "condition"]
SOURCE_COLUMNS = ["Brand", "Model", "Year", "Mileage", "Status"]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_clean_data() -> tuple[np.ndarray, np.ndarray, pd.DataFrame, dict[str, int]]:
    actual_hash = file_sha256(DATA_PATH)
    if actual_hash != EXPECTED_DATA_SHA256:
        raise ValueError(f"Dataset checksum mismatch: {actual_hash}")

    raw = pd.read_csv(DATA_PATH, encoding="utf-16")
    counts = {"raw_rows": len(raw)}
    data = raw.loc[raw["Status"].isin(["Used", "Certified"])].copy()
    counts["used_or_certified_rows"] = len(data)
    data = data.dropna(subset=["Brand", "Model", "Year", "Mileage", "Price", "Status"])
    counts["complete_rows"] = len(data)
    data = data.drop_duplicates(subset=[*SOURCE_COLUMNS, "Price"])
    counts["deduplicated_rows"] = len(data)
    data = data.loc[
        data["Year"].between(1990, 2024)
        & data["Mileage"].between(100, 300_000)
        & data["Price"].between(1_000, 250_000)
    ].copy()
    counts["plausible_rows"] = len(data)

    features = data[SOURCE_COLUMNS].to_numpy(dtype=object)
    target = data["Price"].to_numpy(dtype=float)
    return features, target, data, counts


def make_candidates() -> dict[str, Pipeline]:
    one_hot_preprocessor = ColumnTransformer(
        [
            (
                "categories",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                [0, 1, 4],
            ),
            (
                "numbers",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                [2, 3],
            ),
        ]
    )
    ordinal_preprocessor = ColumnTransformer(
        [
            (
                "categories",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
                        ),
                    ]
                ),
                [0, 1, 4],
            ),
            ("numbers", SimpleImputer(strategy="median"), [2, 3]),
        ]
    )
    return {
        "median_baseline": Pipeline(
            [("preprocess", ordinal_preprocessor), ("regressor", DummyRegressor(strategy="median"))]
        ),
        "ridge": Pipeline(
            [("preprocess", one_hot_preprocessor), ("regressor", Ridge(alpha=10.0))]
        ),
        "hist_gradient_boosting": Pipeline(
            [
                ("preprocess", ordinal_preprocessor),
                (
                    "regressor",
                    HistGradientBoostingRegressor(
                        learning_rate=0.08,
                        max_iter=180,
                        max_leaf_nodes=31,
                        l2_regularization=1.0,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }


def metrics(target: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    return {
        "mae_usd": round(float(mean_absolute_error(target, prediction)), 2),
        "rmse_usd": round(float(mean_squared_error(target, prediction) ** 0.5), 2),
        "r2": round(float(r2_score(target, prediction)), 4),
    }


def main() -> None:
    started = time.perf_counter()
    features, target, cleaned, counts = load_clean_data()
    train_features, heldout_features, train_target, heldout_target = train_test_split(
        features, target, test_size=0.30, random_state=RANDOM_STATE
    )
    validation_features, test_features, validation_target, test_target = train_test_split(
        heldout_features, heldout_target, test_size=0.50, random_state=RANDOM_STATE
    )

    candidates = make_candidates()
    validation_results: dict[str, dict[str, float]] = {}
    for name, candidate in candidates.items():
        candidate.fit(train_features, train_target)
        validation_results[name] = metrics(
            validation_target, candidate.predict(validation_features)
        )

    selected_name = min(validation_results, key=lambda name: validation_results[name]["mae_usd"])
    selected = candidates[selected_name]
    final_train_features = np.concatenate([train_features, validation_features])
    final_train_target = np.concatenate([train_target, validation_target])
    selected.fit(final_train_features, final_train_target)
    test_prediction = selected.predict(test_features)
    test_metrics = metrics(test_target, test_prediction)

    make_values = sorted(cleaned["Brand"].astype(str).unique().tolist())
    make_model_values = sorted(
        (cleaned["Brand"].astype(str) + "::" + cleaned["Model"].astype(str)).unique().tolist()
    )
    metadata: dict[str, Any] = {
        "model_version": "2026-09-21-v1",
        "selected_model": selected_name,
        "feature_names": FEATURE_NAMES,
        "target": "advertised_listing_price_usd",
        "asking_price_is_feature": False,
        "dataset_sha256": EXPECTED_DATA_SHA256,
        "dataset_snapshot": "US Sales Cars Dataset v2 (2024-03-31)",
        "dataset_market": "United States",
        "currency": "USD",
        "mileage_unit": "miles",
        "price_semantics": "advertised listing price, not completed sale price",
        "observation_period": "not documented by publisher",
        "random_state": RANDOM_STATE,
        "row_counts": counts,
        "split_counts": {
            "train": len(train_target),
            "validation": len(validation_target),
            "test": len(test_target),
        },
        "validation_metrics": validation_results,
        "test_metrics": test_metrics,
        "supported_values": {"make": make_values, "make_model": make_model_values},
        "training_environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIGURES_PATH.mkdir(parents=True, exist_ok=True)
    joblib.dump(selected, MODEL_PATH, compress=3)
    metadata["model_sha256"] = file_sha256(MODEL_PATH)
    metadata["training_duration_seconds"] = round(time.perf_counter() - started, 3)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    EVALUATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVALUATION_PATH.write_text(
        json.dumps(
            {
                "validation_metrics": validation_results,
                "selected_model": selected_name,
                "untouched_test_metrics": test_metrics,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    plt.figure(figsize=(7, 5))
    plt.scatter(test_target, test_prediction, alpha=0.25, s=8)
    limit = float(max(test_target.max(), test_prediction.max()))
    plt.plot([0, limit], [0, limit], linestyle="--", color="black")
    plt.xlabel("Actual listing price (USD)")
    plt.ylabel("Predicted listing value (USD)")
    plt.title(f"Untouched test set: {selected_name}")
    plt.tight_layout()
    plt.savefig(FIGURES_PATH / "actual-vs-predicted.png", dpi=150)
    plt.close()

    plt.figure(figsize=(7, 5))
    plt.hist(cleaned["Price"], bins=60)
    plt.xlabel("Advertised listing price (USD)")
    plt.ylabel("Listings")
    plt.title("Filtered training population")
    plt.tight_layout()
    plt.savefig(FIGURES_PATH / "listing-price-distribution.png", dpi=150)
    plt.close()

    print(json.dumps({"selected_model": selected_name, "test_metrics": test_metrics}, indent=2))


if __name__ == "__main__":
    main()
