# Restaurant Clustering Analysis (Week 8 Advanced Project)

## Overview

This analysis applies K-means clustering to an enriched restaurant dataset combining:

- Restaurant attributes (rating, price level)
- ZIP-level socioeconomic indicators (median household income, population)

The goal is to identify structural patterns in restaurant ecosystems across different socioeconomic contexts.

---

## Dataset

Source table: `restaurants_enriched_zip`

Filtered conditions:

- rating IS NOT NULL
- price_level IS NOT NULL
- median_household_income > 0
- population_total > 1000

Final dataset size:

### 20,271 restaurants

Clustering features:

- rating
- price_level
- median_household_income
- population_total

All features were standardized before clustering.

Number of clusters: **k = 4**

---

## Cluster Distribution

| Cluster | Count | Approx. Share |
| --------- | ------- | ------------- |
| 0 | 4,628 | ~23% |
| 1 | 8,872 | ~44% |
| 2 | 776 | ~4% |
| 3 | 5,995 | ~29% |

---

## Cluster Characteristics

### Cluster 0 — Budget / Lower-Rating Cluster

- Average rating: ~3.97  
- Average price level: ~1.30  
- Median household income: ~$79k  
- Population: ~39k  

This cluster represents lower-priced restaurants with comparatively lower ratings, typically located in moderate-income neighborhoods.

---

### Cluster 1 — Affluent High-Quality Cluster

- Average rating: ~4.47  
- Average price level: ~1.83  
- Median household income: ~$120k  
- Population: ~30k  

This is the largest cluster and reflects higher-income ZIP codes with consistently high-rated restaurants at mid-range pricing levels.

---

### Cluster 2 — Premium Fine Dining Cluster

- Average rating: ~4.45  
- Average price level: ~3.19  
- Median household income: ~$127k  
- Population: ~33k  

This small cluster represents premium dining environments. These restaurants are located in the highest-income ZIP codes and exhibit the highest price levels while maintaining high ratings.

---

### Cluster 3 — Dense Urban Affordable Cluster

- Average rating: ~4.41  
- Average price level: ~1.65  
- Median household income: ~$72k  
- Population: ~69k  

This cluster represents densely populated urban areas with relatively lower income levels and more affordable restaurant options.

---

## Key Findings

### 1. Income–Price Relationship

Higher median household income is strongly associated with higher restaurant price levels.

Premium dining clusters are concentrated in wealthier ZIP codes.

---

### 2. Population Density and Affordability

ZIP codes with higher population totals tend to host more affordable restaurants.

This likely reflects increased competition and demand elasticity in dense urban environments.

---

### 3. Ratings Remain Consistently High

Across all clusters, average ratings remain above 3.9, suggesting limited variance in perceived restaurant quality within the Google review system.

---

## Conclusion

The clustering analysis reveals clear socioeconomic stratification in restaurant ecosystems.  
Income level influences pricing tiers, while population density shapes affordability patterns.  

This project demonstrates how combining geospatial business data with demographic indicators can uncover structural differences in local food markets.
