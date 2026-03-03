# Week 9: Predictive Modeling – High-Rated Restaurant Classification

## 1. Objective

The objective of Week 9 was to build and evaluate a supervised machine learning model to predict whether a restaurant is considered “high-rated.”

A binary classification task was defined:

- **High-rated restaurant** = Rating ≥ 4.6  
- **Low-rated restaurant** = Rating < 4.6  

The dataset used was the cleaned and enriched table `restaurants_enriched_zip`, which integrates:

- Restaurant metadata (rating, review count, price level)
- ZIP-level demographic information (income, population, age distribution)
- City labels

---

## 2. Dataset Overview

After filtering out rows without ratings:

- Total samples: **25,357**
- Test set size: 5,072 (20% stratified split)
- High-rated proportion: ~29%

Key features used:

- `log_reviews` (log-transformed review count)
- `price_level`
- `population_total`
- `median_age`
- `pct_under_18`
- `pct_65_plus`
- `median_household_income`
- `city` (one-hot encoded)

Missing values were handled using median imputation for numeric features and most-frequent imputation for categorical features.

---

## 3. Baseline Model – Logistic Regression

To address class imbalance, `class_weight="balanced"` was applied.

### Performance

- Accuracy: **0.61**
- Precision (high-rated): **0.39**
- Recall (high-rated): **0.58**
- F1-score (high-rated): **0.46**

The baseline model demonstrated moderate ability to detect high-rated restaurants, with improved recall compared to an unbalanced logistic model.

---

## 4. Advanced Model – Random Forest

A Random Forest classifier (300 trees, balanced class weights) was trained to capture potential nonlinear relationships.

### Default Threshold (0.50)

- Accuracy: **0.67**
- Precision: **0.43**
- Recall: **0.38**
- F1-score: **0.40**

While overall accuracy improved, recall for high-rated restaurants decreased significantly. This indicates the model became more conservative in predicting the minority class.

---

## 5. Threshold Tuning Experiment

Because classification threshold directly affects precision-recall tradeoffs, probability threshold tuning was performed.

A sweep from 0.20 to 0.60 was evaluated.

### Selected Threshold: 0.35

At threshold = 0.35:

- Accuracy: **0.59**
- Precision: **0.38**
- Recall: **0.65**
- F1-score: **0.48**

This configuration achieved the highest F1-score among tested models and significantly improved recall.

### Key Insight

Adjusting the decision threshold proved more effective than changing model architecture.

This demonstrates that probability calibration is critical in imbalanced classification problems.

---

## 6. Feature Importance Analysis

Feature importance was extracted from the Random Forest model.

### Top Contributors

1. `log_reviews` (~53%)
2. `median_household_income` (~16%)
3. `population_total` (~15%)
4. `price_level` (~5%)
5. Demographic age features (~2–3% each)
6. City indicators (<1%)

### Interpretation

- Review engagement (number of reviews) is the dominant predictor of high ratings.
- Socioeconomic variables (income and population) provide substantial additional signal.
- Price level has limited predictive power.
- City-level effects are minimal compared to ZIP-level demographic context.

This confirms that demographic enrichment meaningfully improves predictive modeling beyond raw restaurant metadata.

---

## 7. Model Comparison Summary

| Model | Accuracy | Precision | Recall | F1 |
| --------- | ---------- | ----------- | --------- | ---- |
| Logistic (balanced) | 0.61 | 0.39 | 0.58 | 0.46 |
| Random Forest (0.50 threshold) | 0.67 | 0.43 | 0.38 | 0.40 |
| Random Forest (0.35 threshold) | 0.59 | 0.38 | 0.65 | **0.48** |

The best-performing configuration was:

> **Random Forest with threshold = 0.35**

This model achieved the best balance between precision and recall for detecting high-rated restaurants.

---

## 8. Conclusions

This week demonstrated a complete supervised learning workflow:

- Feature engineering (log transform)
- Handling class imbalance
- Model comparison (linear vs nonlinear)
- Decision threshold tuning
- Feature importance analysis

Key findings:

- Engagement metrics (review count) strongly predict high ratings.
- ZIP-level demographic variables contribute meaningful predictive signal.
- Threshold tuning significantly improves minority-class detection.
- Model selection should consider task objectives (recall vs precision).

---

## 9. Future Improvements

Potential next steps include:

- ROC curve and AUC evaluation
- Cross-validation for robustness
- Permutation importance analysis
- SHAP value interpretation
- Incorporating additional restaurant-level features (e.g., cuisine type)

---

**Status:** Week 9 Milestone Completed  
**Model Type:** Binary Classification  
**Framework:** scikit-learn  
**Best Configuration:** Random Forest (threshold = 0.35)
