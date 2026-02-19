from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIG_DIR = DATA_DIR / "figures"

DB_PATH = RAW_DIR / "restaurants_google_places.sqlite"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

ENRICHED_CSV_PATH = PROCESSED_DIR / "restaurants_enriched.csv"
