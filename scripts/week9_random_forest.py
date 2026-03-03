import sqlite3
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report
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

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features)
        ]
    )

    return preprocessor


def main():
    print("Loading data...")
    df = load_data()

    print("Preparing data...")
    X, y = prepare_data(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    preprocessor = build_preprocessor()

    rf_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(
                n_estimators=200,
                class_weight="balanced",
                random_state=42
            ))
        ]
    )

    print("Training Random Forest...")
    rf_pipeline.fit(X_train, y_train)

    y_pred = rf_pipeline.predict(X_test)

    print("\n===== Random Forest Evaluation =====")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("Precision:", precision_score(y_test, y_pred))
    print("Recall:", recall_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))


if __name__ == "__main__":
    main()