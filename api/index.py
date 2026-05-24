from fastapi import FastAPI, HTTPException
import json
import os
import requests
from pathlib import Path

app = FastAPI()

# ==========================
# CONFIG (dari prayer_cache)
# ==========================
BASE = "https://bimasislam.kemenag.go.id/ajax"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://bimasislam.kemenag.go.id/",
    "Origin": "https://bimasislam.kemenag.go.id",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}

# ==========================
# LOAD LOCATION HASHES
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

json_path = os.path.join(PROJECT_ROOT, "shalat_locations_clean.json")
if not os.path.exists(json_path):
    json_path = os.path.join(BASE_DIR, "shalat_locations_clean.json")

with open(json_path, "r", encoding="utf-8") as f:
    LOCATIONS = json.load(f)

# ==========================
# PRAYER CACHE FUNCTIONS
# ==========================
def get_prayer_times(province_slug, city_slug, month, year):
    cache_file = Path(f"prayer_data/{year}/{month:02d}/{province_slug}/{city_slug}.json")
    
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    
    session = requests.Session()
    session.get("https://bimasislam.kemenag.go.id/", headers=HEADERS)
    
    x = LOCATIONS[province_slug]["hash"]
    y = LOCATIONS[province_slug]["cities"][city_slug]["hash"]
    
    r = session.post(
        f"{BASE}/getShalatbln",
        data={"x": x, "y": y, "bln": month, "thn": year},
        headers=HEADERS
    )
    
    payload = r.json()
    if payload.get("status") != 1:
        raise Exception(f"Kemenag error: {payload}")
    
    result = payload["data"]
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    
    return result

# ==========================
# FASTAPI ROUTES
# ==========================
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
    return {"province": province, "data": list(LOCATIONS[province]["cities"].keys())}

@app.get("/prayer")
def prayer(province: str, city: str, month: int, year: int):
    try:
        data = get_prayer_times(province, city, month, year)
        return {"province": province, "city": city, "month": month, "year": year, "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))