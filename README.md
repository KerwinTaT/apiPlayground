# API Playground

# Google Places Restaurant Data Export

This project provides a lightweight data export pipeline for restaurant data collected from the Google Places API and stored in a SQLite database.  
It is designed for exploratory analysis, visualization, and research-oriented data processing.

## 📌 Project Overview

The goal of this project is to extract and organize restaurant-related data from a local SQLite database generated using Google Places API queries.  
The exported data can be used for downstream tasks such as geographic analysis, rating distribution analysis, or integration with visualization and data science workflows.

This project focuses on **data extraction and structuring**, rather than real-time data collection or large-scale system deployment.

## 🗄️ Data Source & Description

The dataset is derived from the **Google Places API** and stored locally using SQLite.

Typical fields in the database include:
- Restaurant name
- Address and geographic location
- Google Place ID
- Rating and review-related metadata (when available)

The database operates in **WAL (Write-Ahead Logging) mode**, which results in the presence of:
- `.sqlite-wal`: write-ahead log file
- `.sqlite-shm`: shared memory file

These files are normal and required for SQLite consistency during read/write operations.

## ⚙️ Environment & Dependencies

- Python 3.x
- Built-in Python libraries:
  - `sqlite3`
  - `csv` and/or `json`
  - `os`

No external Python packages are required.

## ▶️ How to Run

Ensure that the Python script and SQLite database files are located in the same directory.

Run the export script using:

```bash
python export_google_places_plateau.py

## 📤 Output

The script exports restaurant data from the SQLite database into a structured file format (such as CSV or JSON).

Typical exported fields may include:
- Restaurant name
- Address
- Latitude and longitude
- Google Place ID
- Rating and review count (if available)

The exported files are intended to be easily consumed by data analysis and visualization tools, including Python, R, Tableau, or GIS software.

The exact output format, file name, and export location are defined within `export_google_places_plateau.py`.

## 🧪 Intended Use

This project is intended for:
- Educational purposes
- Research and exploratory data analysis
- Prototyping data pipelines and visualization workflows

It is not designed to function as a production-level or real-time data ingestion system.

## 🚧 Limitations

- The dataset represents a snapshot in time and does not include real-time updates.
- Data completeness and coverage depend on Google Places API query parameters and rate limits.
- The project focuses on data extraction and export; no automated data cleaning, validation, or deduplication is performed.
- API usage policies may restrict redistribution or commercial use of the data.

## 👤 Author

Kerwin Tu

## 📄 License & Data Usage

This project is provided for educational and research purposes.

Users are responsible for ensuring compliance with the Google Places API Terms of Service when using, sharing, or analyzing the data.
