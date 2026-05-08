import pandas as pd
import numpy as np
import requests
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================
# ⚙️ CONFIG
# =========================
CACHE_FILE = Path("src/data/cache_openmeteo.pkl")
MAX_WORKERS = 4
REQUEST_DELAY = 0.2
ROUND_DECIMALS = 2

session = requests.Session()

# =========================
# 🧊 CACHE INSTANCE GLOBAL
# =========================
from ..persistentLRUCache import PersistentLRUCache

cache = PersistentLRUCache(CACHE_FILE, max_size=20000)


# =========================
# 🔧 NORMALIZACIÓN SEGURA
# =========================
def norm(x):
    return f"{float(x):.{ROUND_DECIMALS}f}"


# =========================
# 🌐 FETCH API
# =========================
def fetch_weather(lat, lon, fecha_str, retries=3):
    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={fecha_str}&end_date={fecha_str}"
        "&daily=temperature_2m_max,temperature_2m_min"
        "&timezone=auto"
    )

    for attempt in range(retries):
        try:
            res = session.get(url, timeout=10)

            if res.status_code == 200:
                data = res.json()

                if "daily" not in data:
                    return None

                return {
                    "tmax": data["daily"]["temperature_2m_max"][0],
                    "tmin": data["daily"]["temperature_2m_min"][0]
                }

            time.sleep(1.5 * (attempt + 1))

        except Exception:
            time.sleep(1.5 * (attempt + 1))

    return None


# =========================
# ⚡ WORKER
# =========================
def worker(query):
    lat, lon, fecha = query
    key = (lat, lon, fecha)

    # 🔍 CACHE HIT
    cached = cache.get(key)
    if cached:
        return key, cached, True

    # 🌐 API
    data = fetch_weather(float(lat), float(lon), fecha)

    if data:
        cache.set(key, data)
        return key, data, False

    return key, None, False


# =========================
# 🚀 PIPELINE
# =========================
def cargar_temperatura(registros):

    df = pd.DataFrame(registros)

    if df.empty:
        return registros

    print("📊 Total registros:", len(df))

    df["Latitud"] = pd.to_numeric(df["Latitud"], errors="coerce")
    df["Longitud"] = pd.to_numeric(df["Longitud"], errors="coerce")
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    df = df.dropna(subset=["Latitud", "Longitud", "Fecha"])

    print("✅ Registros válidos:", len(df))

    # 🔥 NORMALIZACIÓN CONSISTENTE
    df["_lat"] = df["Latitud"].apply(norm)
    df["_lon"] = df["Longitud"].apply(norm)
    df["_fecha"] = df["Fecha"].dt.strftime("%Y-%m-%d")

    queries = (
        df[["_lat", "_lon", "_fecha"]]
        .drop_duplicates()
        .to_records(index=False)
    )

    queries = [(q[0], q[1], q[2]) for q in queries]

    print(f"🌐 Consultas únicas: {len(queries)}")

    results = {}
    hits = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []

        for q in queries:
            futures.append(executor.submit(worker, q))
            time.sleep(REQUEST_DELAY)

        for f in as_completed(futures):
            key, data, from_cache = f.result()

            if from_cache:
                hits += 1

            if data:
                results[key] = data

    print(f"🧠 Cache hit: {hits}/{len(queries)}")

    # =========================
    # 🔗 RECONSTRUCCIÓN
    # =========================
    clima_df = pd.DataFrame([
        {
            "_lat": k[0],
            "_lon": k[1],
            "_fecha": k[2],
            "TE Maxima": v["tmax"],
            "TE Minima": v["tmin"]
        }
        for k, v in results.items()
    ])

    if clima_df.empty:
        df["TE Maxima"] = np.nan
        df["TE Minima"] = np.nan
        return df.to_dict("records")

    df = df.merge(
        clima_df,
        on=["_lat", "_lon", "_fecha"],
        how="left"
    )

    return df.to_dict("records")


# =========================
# 💾 GUARDADO FINAL
# =========================
def cerrar_cache():
    cache.save()