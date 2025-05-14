import json
from datetime import datetime
import config
# Шляхи до файлів
SITES_FILE = "saved_sites.json"
POINTS_FILE = "autoparse_points.json"
PARSED_DATA_FILE = "parsed_results.json"

# --- Збереження ---

def load_sites():
    try:
        with open(SITES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_sites(sites):
    with open(SITES_FILE, "w", encoding="utf-8") as f:
        json.dump(sites, f, ensure_ascii=False, indent=2)

def add_site(site):
    sites = load_sites()
    if site not in sites:
        sites.append(site)
        save_sites(sites)

def remove_site(site):
    sites = load_sites()
    if site in sites:
        sites.remove(site)
        save_sites(sites)


def load_points():
    try:
        with open(POINTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_points(points):
    with open(POINTS_FILE, "w", encoding="utf-8") as f:
        json.dump(points, f, ensure_ascii=False, indent=2)

def add_point(point):
    points = load_points()
    if point not in points:
        points.append(point)
        save_points(points)

def delete_point(point):
    points = load_points()
    if point in points:
        points.remove(point)
        save_points(points)


def save_parsed_result(results):
    try:
        with open(PARSED_DATA_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    for url, title in results:
        # Якщо title випадково включає URL, обрізай
        if title.startswith(url + " → "):
            title = title[len(url) + 3:]
        existing.append({"datetime": now_str, "url": url, "result": title})

    with open(PARSED_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
