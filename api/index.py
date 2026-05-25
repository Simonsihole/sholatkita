from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import json
import requests
from pathlib import Path

app = FastAPI()

# ==========================
# CONFIG
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
# PATHS
# ==========================
BASE_DIR = Path(__file__).resolve().parent
json_path = BASE_DIR / "shalat_locations_clean.json"

with open(json_path, "r", encoding="utf-8") as f:
    LOCATIONS = json.load(f)

CACHE_ROOT = Path("/tmp/prayer_data")


# ==========================
# SERVE FRONTEND (index.html)
# ==========================
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
        return HTMLResponse(content=content)
    return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)


# ==========================
# API ROUTES
# ==========================
@app.get("/api")
def api_root():
    return {"message": "SholatKita API running"}


@app.get("/api/provinces")
def provinces():
    return {"data": list(LOCATIONS.keys())}


@app.get("/api/cities/{province}")
def cities(province: str):
    if province not in LOCATIONS:
        raise HTTPException(status_code=404, detail="Province not found")
    return {"province": province, "data": list(LOCATIONS[province]["cities"].keys())}


# ==========================
# FETCH FUNCTION
# ==========================
def get_prayer_times(province, city, month, year):
    cache_file = CACHE_ROOT / str(year) / f"{month:02d}" / province / f"{city}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    if province not in LOCATIONS:
        raise Exception("Province not found")
    if city not in LOCATIONS[province]["cities"]:
        raise Exception("City not found")

    x = LOCATIONS[province]["hash"]
    y = LOCATIONS[province]["cities"][city]["hash"]

    session = requests.Session()
    session.get("https://bimasislam.kemenag.go.id/", headers=HEADERS, timeout=20)

    r = session.post(
        f"{BASE}/getShalatbln",
        data={"x": x, "y": y, "bln": month, "thn": year},
        headers=HEADERS,
        timeout=20
    )

    payload = r.json()
    if payload.get("status") != 1:
        raise Exception(payload)

    result = payload["data"]
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result


@app.get("/api/prayer")
def prayer(province: str, city: str, month: int, year: int):
    try:
        data = get_prayer_times(province, city, month, year)
        return {
            "province": province, "city": city,
            "month": month, "year": year, "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))