import requests
import json
from pathlib import Path

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
# LOAD LOCATION HASHES
# ==========================
with open(
    "shalat_locations_clean.json",
    "r",
    encoding="utf-8"
) as f:
    LOCATIONS = json.load(f)


def get_prayer_times(
    province_slug,
    city_slug,
    month,
    year
):
    """
    Return cached prayer times if available.
    Otherwise fetch from Kemenag and cache it.
    """

    # cache path
    cache_file = Path(
        f"prayer_data/{year}/{month:02d}/{province_slug}/{city_slug}.json"
    )

    # cache hit
    if cache_file.exists():
        print("Using cache...")
        return json.loads(
            cache_file.read_text(
                encoding="utf-8"
            )
        )

    print("Fetching from Kemenag...")

    # ambil hash
    x = LOCATIONS[
        province_slug
    ]["hash"]

    y = LOCATIONS[
        province_slug
    ]["cities"][
        city_slug
    ]["hash"]

    # IMPORTANT:
    # gunakan SESSION agar cookie ikut
    session = requests.Session()

    # buka homepage dulu
    home = session.get(
        "https://bimasislam.kemenag.go.id/",
        headers=HEADERS
    )

    print("Cookies:")
    print(session.cookies.get_dict())

    # request jadwal
    r = session.post(
        f"{BASE}/getShalatbln",
        data={
            "x": x,
            "y": y,
            "bln": month,
            "thn": year
        },
        headers=HEADERS
    )

    print("Response:")
    print(r.text[:500])

    payload = r.json()

    if payload.get("status") != 1:
        raise Exception(
            f"Kemenag error: {payload}"
        )

    result = payload["data"]

    # save cache
    cache_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cache_file.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return result