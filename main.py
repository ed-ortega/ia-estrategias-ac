#!/usr/bin/env python3 

from src.app.equipos_hvac.ia import entrenar_modelo, cargar_modelo, predecir_hvac
import json

# =====================================
# 🧠 COMPLETAR PROMPT (EVITA ERRORES)
# =====================================
def completar_prompt(data):
    defaults = {
        "CtrlGSE": 0,
        "CambiosSP": 0,
        "CiclosY1": 0,
        "CiclosY2": 0,
        "AlertaTIdanado": 0,
        "TI Offline": 0,

        # valores críticos del modelo
        "Y1 SP": 0,
        "TE SP": 0
    }

    for k, v in defaults.items():
        if k not in data or data[k] is None:
            data[k] = v

    return data


if __name__ == "__main__":

    # =====================================
    # 🚀 1. ENTRENAMIENTO
    # =====================================
    print("🚀 Entrenando modelo HVAC...")
    entrenar_modelo()
    print("✅ Modelo entrenado\n")

    # =====================================
    # 📦 2. CARGAR MODELO
    # =====================================
    modelo, target_columns = cargar_modelo()
    print("📦 Modelo cargado\n")

    # =====================================
    # 🧾 3. INPUT (PROMPT)
    # =====================================
    prompt = {
        "Tecnologia": "Salus",
        "Region": "Nuevo León",
        "Estado": "Nuevo León",
        "Tipo de HVAC": "HVAC 01",
        "Latitud": 25.326873,
        "Longitud": -100.063793,
        "Fecha": "2026-03-18",

        "TZ": 78.64,
        "TIY1": 57.77,
        "TIY2": 0,

        "CtrlGSE": 1,
        "CambiosSP": 2,
        "CiclosY1": 1,
        "CiclosY2": 0,
        "AlertaTIdanado": 0,
        "TI Offline": 0,

        "TZ SPD 01": 74.77,
        "TZ SPD 02": 77.5,
        "TZ SP": 76.87,

        "TI Y1 SPD 01": 49.87,
        "TI Y1 SPD 02": 53.58,
        "TI Y1 SP": 53.54,

        "TI Y2 SPD 01": 0,
        "TI Y2 SPD 02": 0,
        "TI Y2 SP": 0,

        "TE SPD 01": 77.82,
        "TE SPD 02": 86.44,
        "TE SP": 84.33,

        "Y1 SPD 01": 5.11,
        "Y1 SPD 02": 4.48,

        "Y2 SPD 01": 0,
        "Y2 SPD 02": 0,

        "Mode FAN SPD 01": 0.99,
        "Mode FAN SPD 02": 0.99,
        "Mode FAN SP": 0.0
    }

    # =====================================
    # 🧠 4. NORMALIZAR INPUT
    # =====================================
    prompt = completar_prompt(prompt)

    print("🧠 Prompt final usado:")
    print(json.dumps(prompt, indent=2))

    # =====================================
    # 🔮 5. PREDICCIÓN
    # =====================================
    resultado = predecir_hvac(
        modelo,
        target_columns,
        prompt
    )

    # =====================================
    # 📊 6. OUTPUT LEGIBLE
    # =====================================
    print("\n🔮 Resultado HVAC:")
    print(json.dumps(resultado, indent=2))