import sqlite3
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

from src.config import DB_PATH

TABLE = "restaurants_enriched_zip"


def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM {TABLE};", conn)
    conn.close()
    return df


def prepare_data(df):
    df = df[df["rating"].notna()].copy()

    df["high_rated"] = (df["rating"] >= 4.6).astype(int)
    df["log_reviews"] = np.log1p(df["user_ratings_total"])

    features = [
        "log_reviews",
        "price_level",
        "population_total",
        "median_age",
        "pct_under_18",
        "pct_65_plus",
        "median_household_income",
        "city"
    ]

    X = df[features]
    y = df["high_rated"]
    return X, y


def build_preprocessor():
    numeric_features = [
        "log_reviews",
        "price_level",
        "population_total",
        "median_age",
        "pct_under_18",
        "pct_65_plus",
        "median_household_income"
    ]
    categorical_features = ["city"]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore"))
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features)
        ]
    )


def eval_at_threshold(y_true, y_prob, threshold):
    y_pred = (y_prob >= threshold).astype(int)
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    return acc, prec, rec, y_pred


def main():
    df = load_data()
    X, y = prepare_data(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    preprocessor = build_preprocessor()

    rf = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", rf)
        ]
    )

    print("Training Random Forest...")
    model.fit(X_train, y_train)

    # Probabilities for class 1
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n=== Threshold sweep (class 1) ===")
    thresholds = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
    rows = []
    for t in thresholds:
        acc, prec, rec, _ = eval_at_threshold(y_test, y_prob, t)
        rows.append((t, acc, prec, rec))

    # Pretty print
    print(f"{'thr':>6}  {'acc':>8}  {'prec':>8}  {'rec':>8}")
    for t, acc, prec, rec in rows:
        print(f"{t:>6.2f}  {acc:>8.3f}  {prec:>8.3f}  {rec:>8.3f}")

    # Pick a threshold targeting recall (example: closest to recall >= 0.55)
    target_recall = 0.55
    best = None
    for t, acc, prec, rec in rows:
        if rec >= target_recall:
            # among those, pick highest precision
            if (best is None) or (prec > best[2]):
                best = (t, acc, prec, rec)

    if best is None:
        # fallback: pick max F1 if nothing hits target recall
        best = max(rows, key=lambda r: (2*r[2]*r[3]/(r[2]+r[3]+1e-9)))

    best_t = best[0]
    print(f"\nSelected threshold: {best_t:.2f} (acc={best[1]:.3f}, prec={best[2]:.3f}, rec={best[3]:.3f})")

    # Final report at chosen threshold
    _, _, _, y_pred_best = eval_at_threshold(y_test, y_prob, best_t)

    print("\nConfusion Matrix (selected threshold):")
    print(confusion_matrix(y_test, y_pred_best))

    print("\nClassification Report (selected threshold):")
    print(classification_report(y_test, y_pred_best))


if __name__ == "__main__":
    main()