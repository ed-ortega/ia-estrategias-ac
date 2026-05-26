from dotenv import load_dotenv
from pathlib import Path
import pickle
import time
import requests
import pandas as pd
import os

load_dotenv()

# ====================================
# CONFIG
# ====================================
CACHE_FILE = Path("src/data/cache_clima.pkl")

CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

CACHE_TTL = 60 * 60  # 1 hora

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# ====================================
# LOAD CACHE
# ====================================
if CACHE_FILE.exists():

    try:

        with open(CACHE_FILE, "rb") as f:
            CLIMA_CACHE = pickle.load(f)

    except Exception:

        CLIMA_CACHE = {}

else:

    CLIMA_CACHE = {}

# ====================================
# SAVE CACHE
# ====================================
def guardar_cache():

    with open(CACHE_FILE, "wb") as f:
        pickle.dump(CLIMA_CACHE, f)

# ====================================
# PROVIDERS
# ====================================
def obtener_clima_openmeteo(lat, lon):

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&hourly=apparent_temperature"
        f"&temperature_unit=fahrenheit"
        f"&timezone=auto"
    )

    resp = requests.get(url, timeout=10)

    resp.raise_for_status()

    return resp.json()


def obtener_clima_weatherapi(lat, lon):

    url = (
        f"https://api.weatherapi.com/v1/forecast.json"
        f"?key={WEATHER_API_KEY}"
        f"&q={lat},{lon}"
        f"&days=1"
    )

    resp = requests.get(url, timeout=10)

    resp.raise_for_status()

    data = resp.json()

    # ====================================
    # TRANSFORMAR A FORMATO OPENMETEO
    # ====================================
    horas = []
    temperaturas = []

    forecast_hours = data["forecast"]["forecastday"][0]["hour"]

    for hour_data in forecast_hours:

        horas.append(hour_data["time"])

        temperaturas.append(hour_data["feelslike_f"])

    clima = {
        "hourly": {
            "time": horas,
            "apparent_temperature": temperaturas
        }
    }

    return clima

# ====================================
# GET CLIMA
# ====================================
def obtener_clima(
    lat,
    lon,
    provider="openmeteo"
):

    cache_key = (
        f"{provider}_"
        f"{round(lat, 2)}_"
        f"{round(lon, 2)}"
    )

    ahora = time.time()

    # ====================================
    # CACHE HIT
    # ====================================
    if cache_key in CLIMA_CACHE:

        cache_data = CLIMA_CACHE[cache_key]

        if ahora - cache_data["timestamp"] < CACHE_TTL:

            print(f"CACHE HIT -> {provider}")

            return cache_data["data"]

    # ====================================
    # PROVIDERS
    # ====================================
    if provider == "openmeteo":

        clima = obtener_clima_openmeteo(
            lat,
            lon
        )

    elif provider == "weatherapi":

        clima = obtener_clima_weatherapi(
            lat,
            lon
        )

    else:

        raise ValueError(
            f"Provider no soportado: {provider}"
        )

    # ====================================
    # SAVE CACHE MEMORY
    # ====================================
    CLIMA_CACHE[cache_key] = {
        "timestamp": ahora,
        "data": clima
    }

    # ====================================
    # SAVE CACHE FILE
    # ====================================
    guardar_cache()

    print(f"API REQUEST -> {provider}")

    return clima