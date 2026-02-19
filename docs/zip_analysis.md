# ZIP-Level Restaurant & Demographic Analysis  
**Week 7 – Census Data Integration and Contextual Enrichment**

---

## 1. Objective

This phase of the project integrates U.S. Census demographic data (ACS 5-Year Estimates) at the ZIP Code Tabulation Area (ZCTA) level with previously collected Google Places restaurant data.

The goal is to examine whether neighborhood-level socioeconomic characteristics — specifically:

- Median household income  
- Median age  
- Population  

are associated with:

- Average restaurant price level  
- Average restaurant rating  
- Restaurant density (restaurants per 1,000 residents)

This analysis moves beyond city-level aggregation and focuses on intra-city variation at the ZIP level.

---

## 2. Data Preparation

### 2.1 Restaurant Data

Restaurant data was collected via the Google Places API and stored in SQLite.

Each restaurant record includes:

- Rating  
- User rating count  
- Price level (0–4 scale)  
- Address (used to derive ZIP code)  
- City  

ZIP codes were extracted using the Google Place Details API and standardized to 5-digit format.

---

### 2.2 Census Data Integration

Demographic variables were retrieved from the American Community Survey (ACS) via the Census API at the ZCTA level.

Variables used:

- `B19013_001E` – Median household income  
- `S0101` – Median age  
- Total population  

Invalid Census placeholder values (e.g., negative codes such as `-666666666`) were removed during preprocessing.

**Final dataset used for analysis:**

- 777 ZIP codes  
- All with valid population and income data  

---

## 3. Derived ZIP-Level Metrics

For each ZIP code, the following metrics were computed:

- **Average price level** (mean of `price_level`)  
- **Average rating**  
- **Restaurant density** (restaurants per 1,000 residents)  
- Median household income  
- Median age  

---

## 4. Correlation Analysis

Pearson correlation matrix:

| Relationship | Correlation (r) |
|--------------|----------------|
| Income ↔ Avg Price Level | 0.47 |
| Income ↔ Avg Rating | 0.33 |
| Income ↔ Restaurant Density | 0.11 |
| Income ↔ Median Age | 0.32 |
| Price Level ↔ Rating | 0.31 |

---

## 5. Key Findings

### 5.1 Income and Restaurant Price

A moderate positive correlation (r = 0.47) exists between median household income and average restaurant price level.

**Interpretation:**

> Higher-income ZIP codes tend to have more expensive restaurants.

This aligns with economic expectations that pricing structures reflect neighborhood purchasing power.

---

### 5.2 Income and Restaurant Rating

Income also shows a moderate positive relationship with average restaurant rating (r = 0.33).

Possible explanations include:

- Higher-income neighborhoods attracting higher-quality establishments  
- Differences in consumer expectations or rating behavior  
- Higher-priced restaurants investing more in service quality  

---

### 5.3 Income and Restaurant Density

Restaurant density shows minimal correlation with income (r = 0.11).

This indicates:

> Restaurant quantity is not strongly driven by neighborhood income.

Instead, density likely reflects commercial zoning, mixed-use areas, and business district clustering rather than residential wealth.

---

### 5.4 Age and Restaurant Density

Median age shows weak association with restaurant density.

This suggests that demographic age composition alone does not strongly determine restaurant concentration.

---

## 6. Structural Interpretation

The results reveal two distinct mechanisms shaping the restaurant ecosystem:

### Mechanism 1: Economic Purchasing Power

Income influences:

- Restaurant price level  
- Restaurant ratings (moderately)  

### Mechanism 2: Urban Spatial Structure

Restaurant density appears to reflect:

- Commercial clustering  
- Zoning patterns  
- Central business districts  

Rather than household income levels.

This distinction highlights the importance of separating **economic demand effects** from **urban spatial effects** when analyzing local business distribution.

---

## 7. Limitations

- Google Places coverage may vary by region.  
- Price level is categorical (0–4) and relatively coarse.  
- Census ZCTA boundaries may not perfectly align with perceived neighborhoods.  
- City-specific structural differences were pooled in this phase.  

---

## 8. Conclusion

ZIP-level demographic enrichment significantly improved interpretability compared to city-level aggregation.

**Key conclusions:**

1. Income moderately predicts restaurant price level.  
2. Income moderately predicts restaurant ratings.  
3. Restaurant density is largely independent of income.  
4. Urban commercial structure likely explains density patterns more than socioeconomic factors.  

This enriched dataset establishes a foundation for deeper analysis, including:

- City-specific modeling  
- Income quartile comparisons  
- Regression-based modeling  
- Spatial clustering analysis  

---
