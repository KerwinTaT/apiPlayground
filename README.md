# Google Places Restaurant Data Pipeline

A production-oriented data ingestion and export pipeline for restaurant metadata using the Google Places API and SQLite.

This project implements a structured, repeatable workflow for geographic data collection, deduplication, storage optimization, and downstream analytics preparation.

---

## 1. System Overview

This pipeline is designed to:

- Collect restaurant metadata across multiple metropolitan regions
- Optimize API usage via geographic grid sampling
- Prevent duplicate entries using primary-key upsert logic
- Improve write performance through SQLite WAL configuration
- Export structured datasets for analytics and modeling

The system prioritizes:

- API efficiency
- Data integrity
- Reproducibility
- Scalability within API constraints

---

## 2. Architecture

### Data Flow

Google Places API
↓
Grid-based Query Engine
↓
Plateau Detection Logic
↓
Deduplication (place_id upsert)
↓
SQLite (WAL mode)
↓
Structured Export (CSV / JSON)

---

## 3. Data Collection Strategy

### 3.1 Geographic Coverage

- City-level bounding boxes
- Configurable search radius
- Systematic grid iteration for spatial completeness

### 3.2 Plateau Detection

To avoid excessive API calls in low-density regions, the pipeline:

- Tracks rolling averages of new entities discovered
- Stops querying regions once yield falls below threshold
- Reduces redundant API usage

### 3.3 Deduplication Strategy

- `place_id` is enforced as PRIMARY KEY
- INSERT OR IGNORE / upsert logic ensures idempotency
- Prevents duplicate records across overlapping search grids

---

## 4. Database Design

### Core Fields

- `place_id` (Primary Key)
- `name`
- `address`
- `city`
- `latitude`
- `longitude`
- `rating`
- `user_ratings_total`
- `price_level`
- `api_fetch_timestamp`

### Performance Configuration

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

WAL mode enables:

- Improved concurrent read/write performance
- Reduced write lock contention
- Higher insertion throughput during bulk ingestion

Generated files:

- restaurants_google_places.sqlite
- restaurants_google_places.sqlite-wal
- restaurants_google_places.sqlite-shm

These are expected when WAL mode is enabled.

---

## 5. Repository Structure

project-root/
│
├── fetch_google_places_plateau.py     # Data ingestion pipeline
├── export_google_places_plateau.py    # Structured data export
├── config/                            # City bounding boxes and parameters
├── data/                              # Generated outputs (not tracked)
├── .env                               # API credentials (not tracked)
└── README.md

---

## 6. Database File Not Included

The file:

`restaurants_google_places.sqlite`

is intentionally excluded from version control for the following reasons:

- The file size exceeds GitHub's recommended limits.
- Redistribution may conflict with Google Places API Terms of Service.
- The database is dynamically generated through API ingestion and can be reproduced locally.

This repository includes the full ingestion pipeline to regenerate the dataset.

---

## 7. Reproducibility Guide

### Step 1 — Obtain Google Places API Key

1. Enable **Google Places API** in Google Cloud Console.
2. Generate an API key.
3. Create a `.env` file in the project root:

```bash
GOOGLE_API_KEY=your_api_key_here
```

### Step 2 - Run Data Ingestion Pipeline

```bash
python fetch_google_places_plateau.py
```

Expected runtime:

- Several hours depending on geographic coverage
- Subject to API quota and rate limits

The script will generate:

- restaurants_google_places.sqlite
- restaurants_google_places.sqlite-wal
- restaurants_google_places.sqlite-shm

### Step 3 - Export Structured Dataset

```bash
python export_google_places_plateau.py
```

Exports structured data in CSV or JSON format for downstream analytics and modeling workflows.

---

## 8. Operational Constraints

- Subject to Google Places API rate limits and quota restrictions
- Dataset represents a time-specific snapshot
- Geographic completeness depends on grid density configuration
- Not designed for real-time streaming ingestion

---

## 9. Potential Extensions

Future enhancements may include:

- Parallelized ingestion engine
- Migration to PostgreSQL for large-scale persistence
- Cloud deployment (GCP / AWS)
- Automated scheduled refresh
- Integrated ML pipelines (rating prediction, clustering)

---

## 10. Intended Use

This system was developed for:

- Large-scale exploratory data analysis
- Machine learning dataset preparation
- Geographic pattern modeling
- Internship-level data engineering applications
