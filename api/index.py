from fastapi import FastAPI, HTTPException
from prayer_cache import get_prayer_times
import json
import os

app = FastAPI()

# Path ke shalat_locations_clean.json (di root project)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

with open(
    os.path.join(PROJECT_ROOT, "shalat_locations_clean.json"),
    "r",
    encoding="utf-8"
) as f:
    LOCATIONS = json.load(f)


@app.get("/")
def root():
    return {"message": "SholatKita API running"}


@app.get("/provinces")
def provinces():
    return {"data": list(LOCATIONS.keys())}


@app.get("/cities/{province}")
def cities(province: str):
    if province not in LOCATIONS:
        raise HTTPException(status_code=404, detail="Province not found")
    return {
        "province": province,
        "data": list(LOCATIONS[province]["cities"].keys())
    }


@app.get("/prayer")
def prayer(province: str, city: str, month: int, year: int):
    try:
        data = get_prayer_times(province, city, month, year)
        return {
            "province": province,
            "city": city,
            "month": month,
            "year": year,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))