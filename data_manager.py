import json
from datetime import datetime
import config
# Шляхи до файлів
SITES_FILE = "saved_sites.json"
POINTS_FILE = "autoparse_points.json"
PARSED_DATA_FILE = "parsed_results.json"

# --- Збереження ---

def save_sites():
    with open(SITES_FILE, "w", encoding="utf-8") as f:
        json.dump(config.saved_sites, f, ensure_ascii=False, indent=2)

def save_points():
    with open(POINTS_FILE, "w", encoding="utf-8") as f:
        json.dump(config.autoparse_points, f, ensure_ascii=False, indent=2)

def save_parsed_result(results):
    try:
        with open(PARSED_DATA_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    for url, title in results:
        existing.append({"datetime": now_str, "url": url, "result": title})

    with open(PARSED_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

def load_data():
    try:
        with open(SITES_FILE, "r", encoding="utf-8") as f:
            config.saved_sites[:] = json.load(f)
    except Exception:
        config.saved_sites = []

    try:
        with open(POINTS_FILE, "r", encoding="utf-8") as f:
            config.autoparse_points[:] = json.load(f)
    except Exception:
        config.autoparse_points = []

def delete_site(site):
    if site in config.saved_sites:
        config.saved_sites.remove(site)
        save_sites()

def delete_point(point):
    if point in config.autoparse_points:
        config.autoparse_points.remove(point)
        save_points()
