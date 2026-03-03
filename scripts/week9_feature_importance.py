import sqlite3
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
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

    # Get feature names after preprocessing
    feature_names = model.named_steps["preprocessor"].get_feature_names_out()

    importances = model.named_steps["classifier"].feature_importances_

    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances
    }).sort_values(by="importance", ascending=False)

    print("\nTop 15 Feature Importances:")
    print(importance_df.head(15))


if __name__ == "__main__":
    main()