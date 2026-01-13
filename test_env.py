import os
from dotenv import load_dotenv

load_dotenv()
print("GOOGLE key loaded?", bool(os.getenv("GOOGLE_API_KEY")))
print("YELP key loaded?", bool(os.getenv("YELP_API_KEY")))
print("FOURSQUARE key loaded?", bool(os.getenv("FOURSQUARE_API_KEY")))
