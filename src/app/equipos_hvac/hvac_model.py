# hvac_model.py

import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from .hvac_rules import aplicar_reglas_hvac

MODEL_PATH = Path("src/data/equipos_hvac_model.pkl")


# ==============================
# 🧠 FEATURES (SIN LEAKAGE)
# ==============================
FEATURES = [
    "Tecnologia","Region","Estado","Tipo de HVAC",
    "Latitud","Longitud",

    "TZ","TIY1","TIY2",
    "Y1","Y2",
    "TC",

    "CtrlGSE","CambiosSP","CiclosY1","CiclosY2","AlertaTIdanado",
    "TI Offline",

    # dinámicos
    "TZ SPD 01","TZ SPD 02","TZ SP",
    "TI Y1 SPD 01","TI Y1 SPD 02","TI Y1 SP",
    "TE SPD 01","TE SPD 02","TE SP",
    "Y1 SPD 01","Y1 SPD 02",
    "Mode FAN SPD 01","Mode FAN SPD 02","Mode FAN SP",

    "hora","dia_semana"
]

TARGETS = ["SP","SPD01","SPD03","BandaY1","BandaY2"]


# ==============================
# 🚀 ENTRENAR
# ==============================
def entrenar(df: pd.DataFrame):

    df = df.copy()

    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["hora"] = df["Fecha"].dt.hour
    df["dia_semana"] = df["Fecha"].dt.dayofweek

    X = df[FEATURES].copy()
    X = pd.get_dummies(X)

    y = df[TARGETS].dropna()
    X = X.loc[y.index]

    model = RandomForestRegressor(
        n_estimators=400,
        max_depth=18,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    joblib.dump({
        "model": model,
        "columns": X.columns.tolist(),
        "targets": TARGETS
    }, MODEL_PATH)


# ==============================
# 📦 LOAD
# ==============================
def cargar():
    data = joblib.load(MODEL_PATH)
    return data["model"], data["columns"], data["targets"]


# ==============================
# 🔮 PREDICCIÓN (DUAL)
# ==============================
def predecir(model, columns, targets, data: dict):

    df = pd.DataFrame([data])

    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["hora"] = df["Fecha"].dt.hour
    df["dia_semana"] = df["Fecha"].dt.dayofweek

    df = df[FEATURES].copy()
    df = pd.get_dummies(df)
    df = df.reindex(columns=columns, fill_value=0)

    pred = model.predict(df)[0]

    raw = dict(zip(targets, pred))

    # normalización salida
    normalizado = {
        "SP": int(round(raw["SP"])),
        "SPD01": int(round(raw["SPD01"])),
        "SPD02": int(round(raw["SPD03"])),
        "BandaY1": int(round(raw["BandaY1"])),
        "BandaY2": int(round(raw["BandaY2"]))
    }

    # aplicar reglas
    ajustado = aplicar_reglas_hvac(data, normalizado)

    return {
        "normalizado": normalizado,
        "ajustado": ajustado
    }