from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
import uuid
import requests
import httpx
from .models import ChatMessage
import threading
import time
from django.db.models import Max
import math
import os
import re
from io import BytesIO
from time import time as now_ts

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None



def warm_up_ollama():
    try:
        time.sleep(2)  # wait for server start
        requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": "Hello",
                "stream": False,
                "options": {"num_predict": 1}
            },
            timeout=10
        )
        print("Ollama model warmed up")
    except Exception:
        print("Ollama warm-up failed")

threading.Thread(target=warm_up_ollama, daemon=True).start()
# -----------------------------
# Dashboard / KPI
# -----------------------------
@api_view(["POST"])
def dashboard_data(request):
    business_type = request.data.get("businessType")

    return Response({
        "growth_score": 85,
        "demand_level": "High",
        "risk_level": "Low",
        "strategy": "High service demand near residential and office zones"
    })


@api_view(["GET"])
def kpi_data(request):
    business_type = request.GET.get("businessType")

    return Response({
        "growthScore": 85,
        "demandLevel": "High",
        "riskLevel": "Low",
        "insight": "High demand for this two-wheeler business type"
    })


# -----------------------------
# Business Types
# -----------------------------
@api_view(["GET"])
def business_types(request):
    return Response([
        {"id": "showroom", "name": "Two-Wheeler Showroom"},
        {"id": "service", "name": "Two-Wheeler Service Centre"},
        {"id": "spares", "name": "Two-Wheeler Spare Parts"},
    ])


# -----------------------------
# Chatbot
# -----------------------------

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3.2"   # or mistral

# -----------------------------
# Real location data (OSM)
# -----------------------------
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
]
OSM_USER_AGENT = os.getenv(
    "OSM_USER_AGENT",
    "AI-Growth-Planner/1.0 (contact: local-dev)"
)
OSM_EMAIL = os.getenv("OSM_EMAIL")

BUSINESS_TAGS = {
    "showroom": [
        ("shop", "motorcycle"),
        ("shop", "bicycle"),
    ],
    "service": [
        ("shop", "car_repair"),
        ("amenity", "car_repair"),
        ("shop", "motorcycle"),
    ],
    "spares": [
        ("shop", "car_parts"),
        ("shop", "motorcycle"),
        ("shop", "bicycle"),
    ],
}

DEFAULT_AREA = "Saidapet, Chennai"
MIN_DISTANCE_KM = 0.5
CENTER_LAT = 13.022
CENTER_LON = 80.224
MAX_RADIUS_KM = 0.75
LOCK_AREA_TO_SAIDAPET = True
CACHE_TTL_SECONDS = 600
LOCATION_CACHE = {}

def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c

def _extract_area(message: str, fallback: str) -> str:
    if not message:
        return fallback
    msg = message.lower()
    if "saidapet" in msg:
        return DEFAULT_AREA
    quoted = re.findall(r"[\"'“”]([^\"'“”]+)[\"'“”]", message)
    if quoted:
        area = quoted[-1].strip()
        area = re.split(r"\b(give|location|loc|lovation|suggest|please|for|to|my|open|place|start|set)\b", area, flags=re.IGNORECASE)[0].strip()
        return area or fallback
    m = re.findall(r"\b(in|near|around|at)\s+([A-Za-z0-9\s,.-]+)", message, re.IGNORECASE)
    if m:
        area = m[-1][1].strip()
        area = re.split(r"\b(give|location|loc|lovation|suggest|please|for|to|my|open|place|start|set)\b", area, flags=re.IGNORECASE)[0].strip()
        return area or fallback
    return fallback

def _extract_lat_lng(message: str):
    if not message:
        return None
    # Match patterns like "13.0213, 80.2231" or "lat 13.0213 lon 80.2231"
    pair = re.findall(r"(-?\d{1,3}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)", message)
    if pair:
        lat, lon = pair[-1]
        return float(lat), float(lon)
    lat_match = re.findall(r"lat(?:itude)?\s*[:=]?\s*(-?\d{1,3}\.\d+)", message, re.IGNORECASE)
    lon_match = re.findall(r"lon(?:gitude)?\s*[:=]?\s*(-?\d{1,3}\.\d+)", message, re.IGNORECASE)
    if lat_match and lon_match:
        return float(lat_match[-1]), float(lon_match[-1])
    return None

def _within_bbox(area_info, lat, lon):
    bbox = area_info.get("bbox")
    if not bbox:
        return True
    south, north, west, east = bbox
    return south <= lat <= north and west <= lon <= east

def _within_bbox(area_info, lat, lon):
    bbox = area_info.get("bbox")
    if not bbox:
        return True
    south, north, west, east = bbox
    return south <= lat <= north and west <= lon <= east

def _normalize_business_type(text: str, default_type: str = "") -> str:
    t = (text or "").lower()
    if "showroom" in t or "dealer" in t or "dealership" in t or "sales" in t:
        return "showroom"
    if "spare" in t or "parts" in t or "spares" in t:
        return "spares"
    if "service" in t or "mechanic" in t or "repair" in t or "workshop" in t:
        return "service"
    return default_type

BUSINESS_TYPE_KEYWORDS = {
    "showroom": [
        "showroom",
        "sales",
        "dealer",
        "dealership",
        "display",
        "franchise",
        "brand",
    ],
    "service": [
        "service",
        "servicing",
        "repair",
        "mechanic",
        "workshop",
        "maintenance",
        "garage",
        "balancer",
        "scanner",
        "compressor",
        "ramp",
        "tyre",
        "washer",
    ],
    "spares": [
        "spare",
        "spares",
        "parts",
        "inventory",
        "stock",
        "accessories",
    ],
}

def _infer_business_type(message: str, explicit: str = "") -> str:
    explicit = _normalize_business_type(explicit, "")
    t = (message or "").lower()
    scores = {k: 0 for k in BUSINESS_TYPE_KEYWORDS.keys()}
    for bt, kws in BUSINESS_TYPE_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                scores[bt] += 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return explicit
    top = [k for k, v in scores.items() if v == scores[best]]
    if len(top) > 1:
        return explicit
    return best

def _is_count_query(message: str) -> bool:
    t = (message or "").lower()
    return "how many" in t or "count" in t or "number of" in t

def _is_location_query(message: str) -> bool:
    t = (message or "").lower()
    triggers = [
        "location",
        "where to open",
        "where should i open",
        "where should i place",
        "where can i open",
        "where can i place",
        "best location",
        "suggest",
        "suggest location",
        "location suggestion",
        "select a place",
        "place for me",
        "place my",
        "open my",
        "start my",
        "set up",
    ]
    if any(k in t for k in triggers):
        return True
    return "where" in t and ("showroom" in t or "service" in t or "spare" in t or "mechanic" in t)

def _is_greeting_only(message: str) -> bool:
    t = (message or "").strip().lower()
    if not t:
        return False
    greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
    return t in greetings

def _httpx_get(url, params=None, timeout=20):
    headers = {"User-Agent": OSM_USER_AGENT}
    with httpx.Client(trust_env=False, timeout=timeout, headers=headers) as client:
        return client.get(url, params=params)

def _httpx_post(url, data=None, timeout=20):
    headers = {"User-Agent": OSM_USER_AGENT}
    with httpx.Client(trust_env=False, timeout=timeout, headers=headers) as client:
        return client.post(url, data=data)

def _ollama_ready():
    try:
        with httpx.Client(trust_env=False, timeout=5) as client:
            r = client.get("http://127.0.0.1:11434/api/tags")
            return r.status_code == 200
    except Exception:
        return False

def _geocode_area(place: str):
    params = {
        "q": place,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    if OSM_EMAIL:
        params["email"] = OSM_EMAIL
    try:
        resp = _httpx_get(NOMINATIM_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        hit = data[0]
        bbox = [float(x) for x in hit.get("boundingbox", [])] if hit.get("boundingbox") else None
        return {
            "lat": float(hit["lat"]),
            "lon": float(hit["lon"]),
            "bbox": bbox,  # [south, north, west, east]
            "osm_type": hit.get("osm_type"),
            "osm_id": int(hit.get("osm_id")) if hit.get("osm_id") else None,
            "display_name": hit.get("display_name") or place,
        }
    except Exception:
        return None

def _area_id_from_osm(osm_type, osm_id):
    if osm_type == "relation":
        return 3600000000 + osm_id
    if osm_type == "way":
        return 2400000000 + osm_id
    return None

def _overpass_fetch(tags, area_info):
    area_id = _area_id_from_osm(area_info.get("osm_type"), area_info.get("osm_id"))
    bbox = area_info.get("bbox")
    clauses = []
    for key, val in tags:
        if area_id:
            clauses.append(f'node["{key}"="{val}"](area.searchArea);')
            clauses.append(f'way["{key}"="{val}"](area.searchArea);')
            clauses.append(f'relation["{key}"="{val}"](area.searchArea);')
        elif bbox:
            south, north, west, east = bbox
            clauses.append(f'node["{key}"="{val}"]({south},{west},{north},{east});')
            clauses.append(f'way["{key}"="{val}"]({south},{west},{north},{east});')
            clauses.append(f'relation["{key}"="{val}"]({south},{west},{north},{east});')

    if not clauses:
        return []

    if area_id:
        query = f"""
[out:json][timeout:25];
area({area_id})->.searchArea;
(
{''.join(clauses)}
);
out center tags;
"""
    else:
        query = f"""
[out:json][timeout:25];
(
{''.join(clauses)}
);
out center tags;
"""

    for url in OVERPASS_URLS:
        try:
            r = _httpx_post(url, data=query, timeout=15)
            r.raise_for_status()
            return r.json().get("elements", [])
        except Exception as exc:
            continue
    return []

def _get_cached_locations(area_key: str, business_type: str):
    key = (area_key.lower(), business_type)
    cached = LOCATION_CACHE.get(key)
    if not cached:
        return None
    if now_ts() - cached["ts"] > CACHE_TTL_SECONDS:
        return None
    return cached["data"]

def _set_cached_locations(area_key: str, business_type: str, data):
    key = (area_key.lower(), business_type)
    LOCATION_CACHE[key] = {"ts": now_ts(), "data": data}

def _extract_place_name(tags, fallback):
    if not tags:
        return fallback
    return (
        tags.get("name")
        or tags.get("brand")
        or tags.get("operator")
        or fallback
    )

def _fetch_places(area_info, business_type: str):
    tags = BUSINESS_TAGS.get(business_type, [])
    elements = _overpass_fetch(tags, area_info)
    seen = set()
    places = []
    for el in elements:
        key = f"{el.get('type')}:{el.get('id')}"
        if key in seen:
            continue
        seen.add(key)
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        name = _extract_place_name(el.get("tags", {}), "Unnamed place")
        places.append({
            "id": key,
            "name": name,
            "latitude": float(lat),
            "longitude": float(lon),
        })
    return places

def _fetch_candidate_places(area_info):
    tags = [
        ("place", "neighbourhood"),
        ("place", "suburb"),
        ("place", "locality"),
        ("amenity", "marketplace"),
    ]
    elements = _overpass_fetch(tags, area_info)
    seen = set()
    candidates = []
    for el in elements:
        key = f"{el.get('type')}:{el.get('id')}"
        if key in seen:
            continue
        seen.add(key)
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        name = _extract_place_name(el.get("tags", {}), "Suggested area")
        candidates.append({
            "id": key,
            "name": name,
            "latitude": float(lat),
            "longitude": float(lon),
        })
    return candidates

def _recommend_locations(
    area_info,
    business_type: str,
    min_distance_km: float = MIN_DISTANCE_KM,
    limit: int = 5,
    center_lat: float = CENTER_LAT,
    center_lon: float = CENTER_LON,
):
    mechanic_shops = _fetch_places(area_info, "service")
    candidates = _fetch_candidate_places(area_info)
    if not candidates:
        candidates = _fetch_places(area_info, business_type)

    results = []
    for c in candidates:
        # Hard filter to Saidapet center radius
        center_dist = _haversine_km(center_lat, center_lon, c["latitude"], c["longitude"])
        if center_dist > MAX_RADIUS_KM:
            continue
        if not _within_bbox(area_info, c["latitude"], c["longitude"]):
            continue
        if mechanic_shops:
            nearest = min(
                _haversine_km(c["latitude"], c["longitude"], m["latitude"], m["longitude"])
                for m in mechanic_shops
            )
        else:
            nearest = 999.0
        if nearest < min_distance_km:
            continue
        results.append({
            **c,
            "distanceKm": round(nearest, 2),
            "insights": f"Approx. {round(nearest, 2)} km from nearest service centre.",
            "mapUrl": f"https://www.google.com/maps/search/?api=1&query={c['latitude']},{c['longitude']}",
        })

    results.sort(key=lambda r: r["distanceKm"], reverse=True)
    return results[:limit]

def _count_businesses(area_info, business_type: str):
    places = _fetch_places(area_info, business_type)
    return len(places)

# ---- Project Essentials (PDF-derived) ----

PROJECT_ESSENTIALS_CANDIDATE_PATHS = [
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "project_essentials_source.txt")
    ),
]
_PROJECT_ESSENTIALS_TEXT = None
_PROJECT_ESSENTIALS_SECTIONS = None
_PROJECT_ESSENTIALS_SOURCE = None

SECTION_TITLES = {
    "showroom": r"1\.\s*Two-Wheeler Showroom\s*\(Sales\)",
    "service": r"2\.\s*Service Centre",
    "spares": r"3\.\s*Spare Parts Shop",
}

SECTION_LABELS = [
    "Equipment Needed",
    "Documents Needed",
    "Procedure",
    "Price Details",
]

QUERY_STOPWORDS = {
    "a", "an", "and", "are", "at", "can", "centre", "center", "cost", "details",
    "do", "for", "give", "how", "i", "in", "is", "me", "much", "need", "of",
    "on", "price", "project", "service", "shop", "showroom", "spare", "spares",
    "tell", "the", "this", "to", "two", "type", "types", "vehicle", "wheeler",
    "what", "which"
}

def _load_project_essentials_text():
    global _PROJECT_ESSENTIALS_TEXT, _PROJECT_ESSENTIALS_SECTIONS, _PROJECT_ESSENTIALS_SOURCE
    if _PROJECT_ESSENTIALS_TEXT is not None and _PROJECT_ESSENTIALS_SECTIONS is not None:
        return _PROJECT_ESSENTIALS_TEXT, _PROJECT_ESSENTIALS_SECTIONS

    text = ""
    for candidate_path in PROJECT_ESSENTIALS_CANDIDATE_PATHS:
        if not os.path.exists(candidate_path):
            continue
        text = _read_project_essentials_file(candidate_path)
        if text.strip():
            _PROJECT_ESSENTIALS_SOURCE = candidate_path
            break
    text = _clean_project_text(text)
    if _PROJECT_ESSENTIALS_SOURCE:
        print(f"PROJECT_ESSENTIALS_SOURCE={_PROJECT_ESSENTIALS_SOURCE}")

    _PROJECT_ESSENTIALS_TEXT = text
    _PROJECT_ESSENTIALS_SECTIONS = _split_project_sections(text) if text else {}
    return _PROJECT_ESSENTIALS_TEXT, _PROJECT_ESSENTIALS_SECTIONS

def _read_project_essentials_file(path: str):
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError:
        return ""

    if raw.startswith(b"%PDF"):
        return _extract_pdf_text(raw)

    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")

def _extract_pdf_text(raw_pdf: bytes):
    if PdfReader is None:
        return ""
    try:
        reader = PdfReader(BytesIO(raw_pdf))
        page_text = []
        for page in reader.pages:
            extracted = page.extract_text() or ""
            if extracted.strip():
                page_text.append(extracted)
        return "\n".join(page_text)
    except Exception:
        return ""

def _split_project_sections(text: str):
    if not text:
        return {}
    indices = {}
    for key, pattern in SECTION_TITLES.items():
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            indices[key] = m.start()
    ordered = sorted(indices.items(), key=lambda x: x[1])
    sections = {}
    for i, (key, start) in enumerate(ordered):
        end = ordered[i + 1][1] if i + 1 < len(ordered) else len(text)
        sections[key] = text[start:end].strip()
    return sections

def _clean_project_text(text: str):
    if not text:
        return ""
    replacements = {
        "â€¢": "•",
        "â‚¹": "₹",
        "Ã¢â€šÂ¹": "₹",
        "â€“": "-",
        "â€”": "-",
        "â€˜": "'",
        "â€™": "'",
        "\t": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    cleaned_lines = []
    for ln in text.splitlines():
        stripped = ln.strip()
        if not stripped:
            continue
        if stripped.lower().startswith("--- page"):
            continue
        if stripped == "-":
            continue
        stripped = stripped.replace("�", "")
        cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines)

def _extract_labeled_block(section_text: str, label: str):
    pattern = re.compile(
        r"^\s*[•\-\u2022]?\s*" + re.escape(label) + r"\s*:\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(section_text)
    if not match:
        return None
    start = match.end()
    next_match = None
    for next_label in SECTION_LABELS:
        if next_label.lower() == label.lower():
            continue
        nm = re.search(
            r"^\s*[•\-\u2022]?\s*" + re.escape(next_label) + r"\s*:\s*$",
            section_text[start:],
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if nm:
            absolute = start + nm.start()
            if next_match is None or absolute < next_match:
                next_match = absolute
    end = next_match if next_match is not None else len(section_text)
    return section_text[match.start():end].strip()
    pattern = re.compile(
        r"^\s*[•\-\u2022]?\s*" + re.escape(label) + r"\s*:\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(section_text)
    if not match:
        return None
    start = match.end()
    next_match = None
    for next_label in SECTION_LABELS:
        if next_label.lower() == label.lower():
            continue
        nm = re.search(
            r"^\s*[•\-\u2022]?\s*" + re.escape(next_label) + r"\s*:\s*$",
            section_text[start:],
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if nm:
            absolute = start + nm.start()
            if next_match is None or absolute < next_match:
                next_match = absolute
    end = next_match if next_match is not None else len(section_text)
    return section_text[match.start():end].strip()

def _project_context_for(business_type: str, message: str):
    text, sections = _load_project_essentials_text()
    if not text:
        return ""
    section_text = sections.get(business_type, text)

    t = (message or "").lower()
    desired = []
    if any(k in t for k in ["document", "license", "licence", "permit", "registration"]):
        desired += ["Documents Needed", "Procedure"]
    if any(k in t for k in ["equipment", "tools", "machinery", "setup", "infrastructure", "infra"]):
        desired += ["Equipment Needed", "Price Details"]
    if any(k in t for k in ["procedure", "process", "steps", "how to", "apply"]):
        desired += ["Procedure"]
    if any(k in t for k in ["price", "cost", "budget", "investment", "capital"]):
        desired += ["Price Details"]
    if business_type == "spares" and any(k in t for k in ["inventory", "stock", "spares", "parts"]):
        desired += ["Price Details"]

    desired = [d for i, d in enumerate(desired) if d not in desired[:i]]
    blocks = []
    for label in desired:
        block = _extract_labeled_block(section_text, label)
        if block:
            blocks.append(block)

    context = "\n\n".join(blocks) if blocks else section_text
    max_chars = 4000
    if len(context) > max_chars:
        context = context[:max_chars].rsplit("\n", 1)[0].strip()
    return context

def _is_price_query(message: str) -> bool:
    t = (message or "").lower()
    return any(word in t for word in ["price", "cost", "rate", "amount"])

def _looks_like_price_line(line: str) -> bool:
    return bool(
        re.search(
            r"(₹|inr|lakh|\b\d{1,3}(?:,\d{3})+\b|\b\d+\s*each\b)",
            line,
            flags=re.IGNORECASE,
        )
    )
    return bool(
        re.search(
            r"(₹|â‚¹|inr|lakh|\b\d{1,3}(?:,\d{3})+\b|\b\d+\s*each\b)",
            line,
            flags=re.IGNORECASE,
        )
    )

def _normalize_query_tokens(text: str):
    normalized = re.sub(r"[^a-z0-9]+", " ", (text or "").lower())
    tokens = []
    for token in normalized.split():
        if token in QUERY_STOPWORDS:
            continue
        if token.endswith("s") and len(token) > 3:
            token = token[:-1]
        tokens.append(token)
    return tokens

def _clean_response_line(line: str):
    line = (line or "").strip()
    line = re.sub(r"^[•\-\u2022]+\s*", "", line)
    line = re.sub(r"^o\s+", "", line)
    return line.strip()
    line = (line or "").strip()
    line = re.sub(r"^[â€¢•\-\u2022]\s*", "", line)
    line = re.sub(r"^o\s+", "", line)
    return line.strip()

def _strict_section_response(business_type: str, message: str):
    text, sections = _load_project_essentials_text()
    if not text:
        return None

    section_text = sections.get(business_type, text)
    t = (message or "").lower()
    labels = []
    if any(k in t for k in ["equipment", "tool", "machinery", "setup", "infrastructure", "machine"]):
        labels.append("Equipment Needed")
    if any(k in t for k in ["document", "license", "licence", "permit", "registration"]):
        labels.append("Documents Needed")
    if any(k in t for k in ["procedure", "process", "steps", "how to", "apply"]):
        labels.append("Procedure")

    if not labels:
        return None

    blocks = []
    for label in labels:
        block = _extract_labeled_block(section_text, label)
        if not block:
            continue
        lines = []
        for raw_line in block.splitlines():
            line = _clean_response_line(raw_line)
            if line:
                lines.append(f"- {line}")
        if lines:
            blocks.append("\n".join(lines[:12]))
    return "\n\n".join(blocks) if blocks else None

def _strict_line_response(business_type: str, message: str):
    text, sections = _load_project_essentials_text()
    if not text:
        return None

    section_text = sections.get(business_type, text)
    keywords = set(_normalize_query_tokens(message))
    if not keywords:
        return None

    candidates = []
    for raw_line in section_text.splitlines():
        line = _clean_response_line(raw_line)
        if not line or len(line) < 3:
            continue
        line_tokens = set(_normalize_query_tokens(line))
        overlap = keywords & line_tokens
        if not overlap:
            continue
        score = len(overlap)
        if all(token in line_tokens for token in keywords):
            score += 5
        candidates.append((score, len(line), line))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], item[1]))
    best_score = candidates[0][0]
    best_lines = [line for score, _, line in candidates if score == best_score][:5]
    return "\n".join(f"- {line}" for line in best_lines)

def _strict_source_response(business_type: str, message: str):
    price_reply = _strict_price_response(business_type, message)
    if price_reply:
        return price_reply

    section_reply = _strict_section_response(business_type, message)
    if section_reply:
        return section_reply

    line_reply = _strict_line_response(business_type, message)
    if line_reply:
        return line_reply

    return None

def _strict_price_response(business_type: str, message: str):
    if not _is_price_query(message):
        return None

    text, sections = _load_project_essentials_text()
    if not text:
        return None

    keywords = set(_normalize_query_tokens(message))
    if not keywords:
        return None

    message_lower = (message or "").lower()
    requested_type = _infer_business_type(message, business_type)
    candidates = []
    for section_key, section_text in sections.items():
        price_block = _extract_labeled_block(section_text, "Price Details") or section_text
        for raw_line in price_block.splitlines():
            line = _clean_response_line(raw_line)
            if not line:
                continue
            if not _looks_like_price_line(line):
                continue

            line_tokens = set(_normalize_query_tokens(line))
            overlap = keywords & line_tokens
            if not overlap:
                continue

            score = len(overlap)
            if all(token in line_tokens for token in keywords):
                score += 5
            if section_key == requested_type:
                score += 3
            elif any(keyword in message_lower for keyword in BUSINESS_TYPE_KEYWORDS.get(section_key, [])):
                score += 2
            candidates.append((score, len(line), line, section_key))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], item[1]))
    best_score = candidates[0][0]
    best_lines = [line for score, _, line, _ in candidates if score == best_score][:3]
    return "\n".join(f"- {line}" for line in best_lines)

def _fallback_from_context(context: str):
    if not context:
        return None
    lines = [ln.strip() for ln in context.splitlines() if ln.strip()]
    bullet_lines = []
    for ln in lines:
        if ln.lower().startswith("--- page"):
            continue
        if ln == "-":
            continue
        if ln.startswith(("•", "o ", "o\t", "-", "–")):
            bullet_lines.append(ln)
        elif re.match(r"^\d+\.", ln):
            bullet_lines.append(ln)
    selected = bullet_lines[:5] if bullet_lines else lines[:5]
    cleaned = []
    for ln in selected:
        ln = re.sub(r"^[•\-\u2022]\s*", "", ln)
        ln = re.sub(r"^o\s+", "", ln)
        ln = re.sub(r"^\d+\.\s*", "", ln)
        cleaned.append(f"- {ln}")
    return "\n".join(cleaned) if cleaned else None

# ---- Prompts (UNCHANGED) ----

SHOWROOM_PROMPT = """
You are a two-wheeler showroom business advisor in Saidapet, Chennai.
Guide new showroom owners.
Focus on sales, EMI, offers, walk-ins, and customer trust.
Respond with short bullet points.
Maximum 5 bullets.
"""

SERVICE_PROMPT = """
You are a two-wheeler service center business advisor in Saidapet, Chennai.
Guide new service center owners.
Focus on service quality, repeat customers, pricing, and turnaround time.
Give practical, actionable steps.
Maximum 5 bullets.
"""

SPARES_PROMPT = """
You are a two-wheeler spare parts shop advisor in Saidapet, Chennai.
Guide new spare parts business owners.
Focus on fast-moving parts, supplier choice, pricing, and stock planning.
Respond briefly using bullet points.
"""

DEFAULT_PROMPT = """
You are a local two-wheeler business advisor in Saidapet, Chennai.
Give clear, business-focused answers.
Use bullet points only.
Maximum 5 bullets.
"""

# ---- Business-type FAQ (Tuned Content) ----

SHOWROOM_REQUIREMENTS_RESPONSE = """
- Typical total investment: INR 40 lakhs to INR 1.5 crores (brand dependent; includes interiors, initial stock, workshop tools).
- Showroom area: 1,000 to 2,400 sq. ft. display space.
- Workshop area: 2,000 to 2,500 sq. ft. for servicing.
- Location: main road frontage with high visibility and easy parking.
- Documents: business incorporation, GST, PAN, property proof, GCC trade license, Shops & Establishment registration.
"""

SHOWROOM_PROCEDURE_RESPONSE = """
- Engage a registered architect and prepare plans as per Tamil Nadu Combined Development and Building Rules.
- Submit the plan online via Tamil Nadu Single Window Portal (GIS scrutiny + Auto-DCR).
- Obtain NOCs: Fire & Rescue, TNPCB (for workshop), and CMRL if near metro alignment.
- GCC site inspection (Assistant Executive Engineer) verifies boundaries and road width.
- Pay development charges and scrutiny fees to receive the final Building Permit.
"""

SHOWROOM_INVESTMENT_RESPONSE = """
- Brand deposit: INR 5 to 15 lakhs
- Initial vehicle stock (20 to 30 units): INR 25 to 50 lakhs
- Spare parts inventory: INR 5 to 10 lakhs
- Showroom interior and branding: INR 15 to 25 lakhs
- Workshop machinery and tools: INR 8 to 12 lakhs
- Working capital (3 to 6 months): INR 10 to 15 lakhs
- Total estimate: INR 68 lakhs to INR 1.25 crores (excludes land purchase or rental advance).
"""

SHOWROOM_DOCUMENTS_STEPS_RESPONSE = """
- Step 1: Register business entity (Private Ltd/LLP/Partnership) and obtain GST.
- Step 2: Apply for dealership and get LOI from the brand.
- Step 3: Apply for GCC trade license (attach rental deed, property tax receipt, LOI).
- Step 4: Register under Shops & Establishment Act via TN Labour portal.
- Step 5: Fire NOC (TNFRS) and TNPCB Consent to Establish for the workshop.
- Step 6: RTO trade certificate for vehicle sales/registration.
"""

SHOWROOM_DOCS_DETAILED_RESPONSE = """
- Business entity (Private Ltd/LLP/Partnership): register on MCA portal; obtain PAN and incorporation certificate.
- GST registration: apply on GST portal; upload PAN, incorporation, address proof, bank details.
- Dealership LOI: apply on brand website; submit KYC, property details, financials; receive LOI.
- GCC Trade License: apply on GCC portal; submit rental deed/sale deed, property tax receipt, LOI; schedule inspection.
- Shops & Establishment: apply on TN Labour portal; declare staff count, working hours; receive registration.
- Fire NOC (TNFRS): apply on TNFRS portal; install extinguishers, mark exits; pass site inspection.
- TNPCB CTE: apply on OCMMS; submit waste oil handling plan, wash bay details; receive consent.
- RTO Trade Certificate: apply at RTO; provide storage proof and GCC license; receive trade certificate.
"""

SERVICE_TOOLS_RESPONSE = """
- Hydraulic ramps (3 to 4 units), air compressor (3 to 5 HP), pneumatic tool kit.
- Battery charger/tester, wheel balancer/aligner, digital engine scanner (BS6).
- General tool trolleys and pressure washer.
- Washing bay with drainage and oil trap.
- Oil storage and used oil disposal system.
- Customer lounge and safe vehicle storage.
- Estimated setup (tools + infra): INR 12 to 18 lakhs (excludes building rent/construction).
"""

SPARES_INVENTORY_RESPONSE = """
- Consumables: engine oils, brake fluids, coolants, grease.
- Braking: pads, liners, shoes, cables.
- Electricals: batteries, spark plugs, bulbs, indicators.
- Transmission: chain sprocket kits, drive belts (scooters).
- Filters: air, oil, fuel filters.
- Tyres/tubes: common 10 to 12 in scooters, 17 to 18 in bikes.
- Estimated initial spares investment: INR 6.3 to 9.7 lakhs.
"""

SERVICE_SPARES_PERMITS_RESPONSE = """
- Mandatory documents: GST, business incorporation, PAN/Aadhaar, property deed or rental agreement, latest property tax receipt.
- GCC Trade License: apply online; local zonal inspection is required.
- Shops & Establishment Act: register staff and working hours (TN Labour portal).
- TNPCB Consent to Establish: required for used oil/wash bay handling.
- Fire Safety NOC: TN Fire & Rescue Services compliance certificate.
- Professional Tax registration once employees are hired.
"""

SERVICE_DOCS_DETAILED_RESPONSE = """
- Business entity and PAN: register firm (proprietorship/partnership/LLP); keep PAN and incorporation.
- GST registration: apply on GST portal with PAN, address proof, bank details.
- Property documents: rental deed or sale deed + latest property tax receipt.
- GCC Trade License: apply on GCC portal; submit property documents and GST; pass zonal inspection.
- Shops & Establishment: register staff count and working hours on TN Labour portal.
- TNPCB CTE: apply on OCMMS with oil trap, waste oil disposal plan, wash bay layout.
- Fire NOC (TNFRS): apply online; install fire equipment; pass safety inspection.
- Professional Tax: register after hiring employees (GCC).
"""

SPARES_DOCS_DETAILED_RESPONSE = """
- Business entity and PAN: register firm (proprietorship/partnership/LLP); keep PAN and incorporation.
- GST registration: apply on GST portal with PAN, address proof, bank details.
- Property documents: rental deed or sale deed + latest property tax receipt.
- GCC Trade License: apply on GCC portal; submit property documents and GST; pass zonal inspection.
- Shops & Establishment: register staff count and working hours on TN Labour portal.
- Fire NOC (TNFRS): apply online; install fire equipment; pass safety inspection.
- Professional Tax: register after hiring employees (GCC).
"""

SHOWROOM_SAIDAPET_LOCATIONS_RESPONSE = """
- T. Nagar High Street, Saidapet.
- Anna Salai, Saidapet.
- Poonia Road, Saidapet.
- Velachery Road, Saidapet.
- Velur Main Road, Saidapet.
"""

OTHER_DOCUMENTS_RESPONSE = """
- Optional / situational documents: Power connection approval (EB), rental NOC from owner, signage permission, public liability insurance, waste oil disposal agreement, fire equipment maintenance certificate.
- If you want steps for any specific document, tell me the name (example: "Fire NOC steps").
"""

BATTERY_CHARGING_PRICE_RESPONSE = """
- Average battery charging price: INR 200 to 300.
- Pricing depends on battery type and condition, labor time, and shop overhead.
- Typical turnaround time: 1 to 2 hours.
- Optional: offer a short warranty on charging to build trust.
"""

DOC_STEPS = {
    "gst": "- GST registration: apply on GST portal; upload PAN, incorporation, address proof, bank details.",
    "trade license": "- GCC Trade License: apply on GCC portal; submit property documents and GST; pass zonal inspection.",
    "shops": "- Shops & Establishment: apply on TN Labour portal; declare staff count and working hours; receive registration.",
    "fire": "- Fire NOC (TNFRS): apply on TNFRS portal; install extinguishers, mark exits; pass site inspection.",
    "tnpcb": "- TNPCB CTE: apply on OCMMS; submit waste oil handling plan, wash bay details; receive consent.",
    "rto": "- RTO Trade Certificate: apply at RTO; provide storage proof and GCC license; receive trade certificate.",
    "loi": "- Dealership LOI: apply on brand website; submit KYC, property details, financials; receive LOI.",
}

def _faq_response(business_type: str, message: str):
    t = (message or "").lower()
    bt = (business_type or "").lower()

    if any(k in t for k in ["any other documents", "other documents", "extra documents", "additional documents"]):
        return OTHER_DOCUMENTS_RESPONSE.strip()

    for key, resp in DOC_STEPS.items():
        if key in t and ("document" in t or "steps" in t or "apply" in t):
            return resp

    if "battery" in t and ("charging" in t or "charge" in t or "battery charging" in t):
        return BATTERY_CHARGING_PRICE_RESPONSE.strip()

    # Showroom
    if bt == "showroom":
        if any(k in t for k in ["hero", "franchise", "dealership"]) and any(
            k in t for k in ["location", "where", "place", "open", "saidapet"]
        ):
            return SHOWROOM_SAIDAPET_LOCATIONS_RESPONSE.strip()
        if any(k in t for k in ["investment", "cost", "capital", "initial", "budget"]):
            return "\n".join([
                SHOWROOM_INVESTMENT_RESPONSE.strip(),
                SHOWROOM_DOCUMENTS_STEPS_RESPONSE.strip(),
            ])
        if any(k in t for k in ["each document", "document wise", "document-wise", "step for each document"]):
            return SHOWROOM_DOCS_DETAILED_RESPONSE.strip()
        if any(k in t for k in ["documents", "license", "licence", "permit", "apply", "steps"]):
            return SHOWROOM_DOCUMENTS_STEPS_RESPONSE.strip()
        if any(k in t for k in ["requirements", "procedure", "construction", "build", "cmda", "gcc", "tnpcb", "noc"]):
            return "\n".join([
                SHOWROOM_REQUIREMENTS_RESPONSE.strip(),
                SHOWROOM_PROCEDURE_RESPONSE.strip(),
            ])

    # Service centre
    if bt == "service":
        if any(k in t for k in ["each document", "document wise", "document-wise", "step for each document"]):
            return SERVICE_DOCS_DETAILED_RESPONSE.strip()
        if any(k in t for k in ["tools", "equipment", "machinery", "setup", "service centre", "service center"]):
            return "\n".join([
                SERVICE_TOOLS_RESPONSE.strip(),
                SPARES_INVENTORY_RESPONSE.strip(),
            ])
        if any(k in t for k in ["documents", "license", "licence", "permit", "apply", "registration"]):
            return SERVICE_DOCS_DETAILED_RESPONSE.strip()

    # Spare parts
    if bt == "spares":
        if any(k in t for k in ["each document", "document wise", "document-wise", "step for each document"]):
            return SPARES_DOCS_DETAILED_RESPONSE.strip()
        if any(k in t for k in ["tools", "equipment", "machinery", "setup", "inventory", "stock", "spares", "parts"]):
            return SPARES_INVENTORY_RESPONSE.strip()
        if any(k in t for k in ["documents", "license", "licence", "permit", "apply", "registration"]):
            return SPARES_DOCS_DETAILED_RESPONSE.strip()

    return None

# ---- Chatbot API ----

@api_view(["POST"])
def chatbot(request):
    message = request.data.get("message", "").strip()
    business_type = request.data.get("businessType", "").lower()
    session_id = request.data.get("sessionId")

    # Create session if not provided
    if not session_id:
        session_id = uuid.uuid4()

    if not message:
        return Response({
            "content": "Please ask a question.",
            "sessionId": session_id
        })

    # Real location queries (override AI)
    inferred_type = _infer_business_type(message, business_type)
    area = _extract_area(message, DEFAULT_AREA)
    center_override = _extract_lat_lng(message)
    if LOCK_AREA_TO_SAIDAPET:
        area = DEFAULT_AREA

    if _is_count_query(message) and inferred_type:
        try:
            area_info = _geocode_area(area)
            if not area_info:
                count_text = f"I couldn't find '{area}'. Please try a nearby area name."
                response_payload = {"content": count_text, "sessionId": session_id}
            else:
                count = _count_businesses(area_info, inferred_type)
                count_text = f"Found {count} {inferred_type} businesses in {area_info['display_name']}."
                response_payload = {"content": count_text, "sessionId": session_id}

            ChatMessage.objects.create(
                session_id=session_id,
                business_type=business_type,
                role="assistant",
                content=response_payload["content"],
                locations=[]
            )
            return Response(response_payload)
        except Exception:
            return Response({
                "content": "Location search error. Please try again.",
                "sessionId": session_id
            })

    if _is_location_query(message) and inferred_type:
        area_info = _geocode_area(area)
        if not area_info:
            reply_text = f"I couldn't find '{area}'. Please try a nearby area name."
            response_payload = {"content": reply_text, "sessionId": session_id, "locations": []}
        else:
            cached = _get_cached_locations(area, inferred_type)
            if center_override:
                suggestions = _recommend_locations(
                    area_info,
                    inferred_type,
                    MIN_DISTANCE_KM,
                    limit=5,
                    center_lat=center_override[0],
                    center_lon=center_override[1],
                )
            else:
                suggestions = _recommend_locations(area_info, inferred_type, MIN_DISTANCE_KM, limit=5)
            if not suggestions and cached:
                suggestions = cached
            if suggestions:
                _set_cached_locations(area, inferred_type, suggestions)
                lines = [f"Suggested locations for {inferred_type} (>= {MIN_DISTANCE_KM} km from service centres):"]
                for s in suggestions:
                    lines.append(
                        f"• {s['name']} ({s['distanceKm']} km) "
                        f"- lat {s['latitude']}, lon {s['longitude']}"
                    )
                reply_text = "\n".join(lines)
            else:
                reply_text = "No suitable locations found right now. Please try again."
            response_payload = {
                "content": reply_text,
                "sessionId": session_id,
                "locations": suggestions
            }

        ChatMessage.objects.create(
            session_id=session_id,
            business_type=business_type,
            role="assistant",
            content=response_payload["content"],
            locations=response_payload.get("locations", [])
        )
        return Response(response_payload)

    # If no clear business type, ask a clarification question
    target_type = inferred_type or business_type
    if not target_type:
        clarification = (
            "Which business type are you asking about?\n"
            "- Two-Wheeler Showroom (Sales)\n"
            "- Two-Wheeler Service Centre\n"
            "- Two-Wheeler Spare Parts Shop"
        )
        ChatMessage.objects.create(
            session_id=session_id,
            business_type=business_type,
            role="assistant",
            content=clarification,
            locations=[]
        )
        return Response({
            "content": clarification,
            "sessionId": session_id,
            "locations": []
        })

    greeting_reply = (
        "I'm your local business growth advisor for two-wheeler businesses in Saidapet, Chennai.\n"
        "How can I help you today?"
    )
    if _is_greeting_only(message):
        ChatMessage.objects.create(
            session_id=session_id,
            business_type=target_type,
            role="assistant",
            content=greeting_reply,
            locations=[]
        )
        return Response({
            "content": greeting_reply,
            "sessionId": session_id,
            "locations": []
        })

    exact_price_reply = _strict_price_response(target_type, message)
    if exact_price_reply:
        print(f"STRICT_PRICE_MATCH business_type={target_type} message={message!r} reply={exact_price_reply!r}")
        ChatMessage.objects.create(
            session_id=session_id,
            business_type=target_type,
            role="assistant",
            content=exact_price_reply,
            locations=[]
        )
        return Response({
            "content": exact_price_reply,
            "sessionId": session_id,
            "locations": []
        })

    # Select business-specific prompt
    if target_type == "showroom":
        system_prompt = SHOWROOM_PROMPT
    elif target_type == "service":
        system_prompt = SERVICE_PROMPT
    elif target_type == "spares":
        system_prompt = SPARES_PROMPT
    else:
        system_prompt = DEFAULT_PROMPT

    pdf_context = _project_context_for(target_type, message)
    final_prompt = f"""
{system_prompt}

IMPORTANT PRIORITY RULE (MANDATORY):
- If the user message contains ANY of these keywords:
  "give location", "location", "place my showroom", "where to open", "best location"

  THEN:
  - No greeting
  - No introduction
  - Directly give location advice

GREETING RULE:
- If the user sends ONLY a greeting like:
  hi, hello, hey, good morning

  THEN respond with ONLY:
  "I’m your local business growth advisor for two-wheeler businesses in Saidapet, Chennai.
   How can I help you today?"

STRICT LOCATION RULES:
- Suggest locations ONLY inside Saidapet, Chennai
- Do NOT mention other areas
- If unsure, say: "within the main commercial areas of Saidapet"

RESPONSE STYLE:
- Bullet points only
- Max 5 bullets
- No greetings unless greeting-only message
- No explanations unless asked
- No generic advice

CONTEXT FROM PROJECT ESSENTIALS (USE THIS FIRST WHEN RELEVANT):
{pdf_context}

If the user asks about an item, document, tool, part, or price covered in the context, stay consistent with the context.
If the context does not cover the question, answer normally as a helpful business assistant.

User question:
{message}
"""

    # ---- Save USER message ----
    ChatMessage.objects.create(
        session_id=session_id,
        business_type=business_type,
        role="user",
        content=message,
        locations=[]
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": final_prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 200,
            "top_p": 0.9
        }
    }

    try:
        if not _ollama_ready():
            fallback_text = _fallback_from_context(pdf_context)
            if fallback_text:
                ChatMessage.objects.create(
                    session_id=session_id,
                    business_type=target_type,
                    role="assistant",
                    content=fallback_text,
                    locations=[]
                )
                return Response({
                    "content": fallback_text,
                    "sessionId": session_id,
                    "locations": []
                })
            raise RuntimeError("ollama_unavailable")

        with httpx.Client(trust_env=False, timeout=45) as client:
            r = client.post(OLLAMA_URL, json=payload)
            ai_text = r.json().get("response", "").strip()

        # ---- Save AI response ----
        ChatMessage.objects.create(
            session_id=session_id,
            business_type=target_type,
            role="assistant",
            content=ai_text,
            locations=[]
        )

        return Response({
            "content": ai_text,
            "sessionId": session_id,
            "locations": []
        })

    except httpx.ReadTimeout:
        fallback_text = _fallback_from_context(pdf_context)
        if fallback_text:
            ChatMessage.objects.create(
                session_id=session_id,
                business_type=target_type,
                role="assistant",
                content=fallback_text,
                locations=[]
            )
            return Response({
                "content": fallback_text,
                "sessionId": session_id,
                "locations": []
            })
        return Response({
            "content": "The AI is taking longer than usual. Please try again.",
            "sessionId": session_id
        })

    except Exception:
        fallback = _fallback_from_context(pdf_context) or _faq_response(inferred_type or business_type, message)
        if fallback:
            ChatMessage.objects.create(
                session_id=session_id,
                business_type=target_type,
                role="assistant",
                content=fallback,
                locations=[]
            )
            return Response({
                "content": fallback,
                "sessionId": session_id,
                "locations": []
            })

        return Response({
            "content": "AI service error. Ensure Ollama is running and the model is available.",
            "sessionId": session_id
        })


@api_view(["POST"])
def strategy_data(request):
    business_type = request.data.get("businessType")
    location = request.data.get("location")

    return Response({
        "id": "strategy-1",
        "title": "One-Time Business Strategy",
        "description": f"Recommended strategy for {business_type}",
        "recommendations": [
            "Focus on high-demand services",
            "Choose locations near residential areas",
            "Maintain competitive pricing",
        ],
    })

@api_view(["GET"])
def analytics_data(request):
    business_type = request.GET.get("businessType")

    # Dummy but realistic analytics data
    categories = [
        "Footfall",
        "Customer Retention",
        "Monthly Revenue",
        "Service Demand",
        "Market Growth"
    ]

    demand = [70, 65, 80, 90, 75]
    growth = [60, 55, 75, 85, 70]

    return Response({
        "categories": categories,
        "demand": demand,
        "growth": growth
    })

SAIDAPET_LOCATIONS = [
    {
        "id": "saidapet-east",
        "name": "Saidapet East",
        "latitude": 13.0213,
        "longitude": 80.2231,
        "insights": "High residential density with consistent two-wheeler usage.",
        "demandScore": 85,
    },
    {
        "id": "saidapet-west",
        "name": "Saidapet West",
        "latitude": 13.0189,
        "longitude": 80.2104,
        "insights": "Good commercial activity near main roads and bus routes.",
        "demandScore": 78,
    },
    {
        "id": "saidapet-station",
        "name": "Saidapet Railway Station Area",
        "latitude": 13.0216,
        "longitude": 80.2270,
        "insights": "Very high footfall; ideal for service centers and spare parts.",
        "demandScore": 92,
    },
]

@api_view(["GET"])
def locations_list(request):
    business_type = request.GET.get("businessType", "")
    area = request.GET.get("area", DEFAULT_AREA)
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    business_type = _normalize_business_type(business_type, "showroom")
    if LOCK_AREA_TO_SAIDAPET:
        area = DEFAULT_AREA

    try:
        area_info = _geocode_area(area)
        if not area_info:
            return Response([])
        if lat and lon:
            try:
                center_lat = float(lat)
                center_lon = float(lon)
                suggestions = _recommend_locations(
                    area_info,
                    business_type,
                    MIN_DISTANCE_KM,
                    limit=5,
                    center_lat=center_lat,
                    center_lon=center_lon,
                )
            except ValueError:
                suggestions = _recommend_locations(area_info, business_type, MIN_DISTANCE_KM, limit=5)
        else:
            suggestions = _recommend_locations(area_info, business_type, MIN_DISTANCE_KM, limit=5)
        return Response(suggestions)
    except Exception:
        return Response([], status=200)

@api_view(["GET"])
def location_detail(request, location_id):
    return Response({"error": "Location not found"}, status=404)

@api_view(["GET"])
def chat_history(request):
    session_id = request.GET.get("sessionId")
    if not session_id:
        return Response([])
    messages = (
        ChatMessage.objects
        .filter(session_id=session_id)
        .order_by("created_at")
    )
    return Response([
        {
            "role": m.role,
            "content": m.content,
            "timestamp": m.created_at.isoformat(),
            "locations": m.locations or []
        }
        for m in messages
    ])

@api_view(["DELETE"])
def delete_chat_session(request, session_id):
    ChatMessage.objects.filter(session_id=session_id).delete()
    return Response({"deleted": True, "sessionId": session_id})

@api_view(["GET"])
def chat_sessions(request):
    sessions = (
        ChatMessage.objects
        .values("session_id")
        .annotate(last_time=Max("created_at"))
        .order_by("-last_time")
    )

    return Response([
        {
            "sessionId": s["session_id"],
            "lastMessageTime": s["last_time"]
        }
        for s in sessions
    ])
