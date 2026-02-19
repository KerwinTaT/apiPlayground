import sqlite3
import pandas as pd
import numpy as np
import statsmodels.api as sm
from src.config import DB_PATH

def main():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql("""
        SELECT *
        FROM zip_analysis
        WHERE population_total IS NOT NULL
          AND median_household_income IS NOT NULL
    """, conn)

    conn.close()

    # Clean invalid income
    df = df[df["median_household_income"] > 0]

    # Log transform income
    df["log_income"] = np.log(df["median_household_income"])

    # ----- Model 1: Price ~ log(Income) -----
    X1 = sm.add_constant(df["log_income"])
    y1 = df["avg_price_level"]

    model1 = sm.OLS(y1, X1).fit()

    print("\n=== Model 1: Price ~ log(Income) ===\n")
    print(model1.summary())

    # ----- Model 2: log(Price) ~ log(Income) -----
    df = df[df["avg_price_level"] > 0]
    df["log_price"] = np.log(df["avg_price_level"])

    X2 = sm.add_constant(df["log_income"])
    y2 = df["log_price"]

    model2 = sm.OLS(y2, X2).fit()

    print("\n=== Model 2: log(Price) ~ log(Income) ===\n")
    print(model2.summary())


if __name__ == "__main__":
    main()
