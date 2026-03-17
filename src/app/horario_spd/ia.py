from ...api.gse import get_reglas_horario_spd
import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from .mapsca import temporada_map, tipo_clima_map, area_map
from .utils import minutes_to_time, reglas_to_dataset

MODEL_PATH = Path("src/data/horario_spd_model.pkl")

# ----------------------------------
# CREAR DATASET
# ----------------------------------
def crear_dataset():
    reglas_horario = get_reglas_horario_spd()

    df = reglas_to_dataset(reglas_horario)
    return df

# ----------------------------------
# ENTRENAR MODELO
# ----------------------------------
def entrenar_modelo():
    df = crear_dataset()
    # eliminar filas con targets incompletos
    df = df.dropna(subset=[
        "spd1_inicio",
        "spd1_fin",
        "spd2_inicio",
        "spd2_fin"
    ])

    X = df[
        [
            "temporada",
            "tipo_clima",
            "area",
            "temp_min",
            "temp_max",
            "spd1_fin_evento",
            "spd2_fin_evento"
        ]
    ].fillna(0)

    y = df[
        [
            "spd1_inicio",
            "spd1_fin",
            "spd2_inicio",
            "spd2_fin"
        ]
    ]

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=10,
        random_state=42
    )

    model.fit(X, y)

    guardar_modelo(model)

# ----------------------------------
# GUARDAR MODELO
# ----------------------------------
def guardar_modelo(modelo):
    joblib.dump(modelo, MODEL_PATH)

# ----------------------------------
# CARGAR MODELO
# ----------------------------------
def cargar_modelo():
    return joblib.load(MODEL_PATH)

# ----------------------------------
# PREDICCION
# ----------------------------------
def predecir_spd(model, temporada, tipo_clima, area, temperatura):

    X = pd.DataFrame([{
        "temporada": temporada_map().get(temporada),
        "tipo_clima": tipo_clima_map().get(tipo_clima),
        "area": area_map().get(area),
        "temp_min": temperatura,
        "temp_max": temperatura,
        "spd1_fin_evento": 0,
        "spd2_fin_evento": 0
    }])

    pred = model.predict(X)[0]

    return {
        "spd1_inicio": minutes_to_time(pred[0]),
        "spd1_fin": minutes_to_time(pred[1]),
        "spd2_inicio": minutes_to_time(pred[2]),
        "spd2_fin": minutes_to_time(pred[3]),
    }

