#!/usr/bin/env python3

from src.app.equipos_hvac.hvac_model import cargar, predecir
from src.app.equipos_hvac.hvac_rules import (
    evaluar_estado,
    evaluar_queja,
    calcular_porcentajes_operacion
)

import json
import pandas as pd
from rich.console import Console
from rich.progress import track

console = Console()


# ==============================
# 🧩 COMPLETAR PROMPT
# ==============================
def completar_prompt(data):
    defaults = {
        "CtrlGSE": 0,
        "CambiosSP": 0,
        "CiclosY1": 0,
        "CiclosY2": 0,
        "AlertaTIdanado": 0,
        "TI Offline": 0,

        "Y1 SP": 0,
        "Y1 SPD 01": 0,
        "Y1 SPD 02": 0,

        "TE SP": 0,
        "TC": 0,

        # horarios (CRÍTICO para reglas)
        "horario_inicio_SPD_01": "00:00",
        "horario_fin_SPD_01": "06:00",
        "horario_inicio_SPD_02": "20:00",
        "horario_fin_SPD_02": "23:59",
    }

    for k, v in defaults.items():
        if k not in data or data[k] is None:
            data[k] = v

    return data


# ==============================
# 🚀 MAIN
# ==============================
if __name__ == "__main__":

    model, columns, targets = cargar()
    console.print("📦 Modelo cargado\n")

    # Leer archivo excel "EQUIPOS 7 ELEVEN.xlsx" y obtener datos para generar promps
    archivo = "EQUIPOS 7 ELEVEN.xlsx"

    df = pd.read_excel(archivo)

    console.print(f"✅ Registros encontrados: {len(df)}\n")

    resultados = []

    # ==============================
    # 🔁 RECORRER EQUIPOS
    # ==============================
    for _, row in track(df.iterrows(), total=len(df), description="Procesando equipos..."):

        try:

            prompt = row.to_dict()

            prompt = completar_prompt(prompt)

            # ==============================
            # 🔮 PREDICCIÓN
            # ==============================
            resultado_modelo = predecir(
                model,
                columns,
                targets,
                prompt
            )

            # ==============================
            # 📊 EVALUACIONES
            # ==============================
            estado = evaluar_estado(prompt)

            queja = evaluar_queja(prompt)

            try:
                operacion = calcular_porcentajes_operacion(prompt)

            except Exception:
                operacion = {
                    "SPD1": {},
                    "SPD2": {},
                    "SP": {}
                }

            # ==============================
            # 🎯 RESUMEN RESULTADO
            # ==============================
            ajustado = (
                resultado_modelo
                .get("ajustado", {})
                .get("resultados_ia", {})
            )

            resultado_final = {
                "estado": estado,
                "queja": queja
            }

            for sensor in ["SP", "SPD1", "SPD2"]:

                resultado_sensor = {
                    "operacion_pct": operacion.get(sensor, {}).get("operacion_pct", ""),
                    "temp_prom": operacion.get(sensor, {}).get("temp_prom", ""),
                    "motivo": ajustado.get(sensor, {}).get("motivo", ""),
                    "clima": ajustado.get(sensor, {}).get("clima", "")
                }

                if sensor == "SP":
                    resultado_sensor["SP"] = (
                        ajustado.get(sensor, {}).get("SP", "")
                    )

                elif sensor == "SPD1":
                    resultado_sensor["SPD01"] = (
                        ajustado.get(sensor, {}).get("SPD01", "")
                    )

                elif sensor == "SPD2":
                    resultado_sensor["SPD02"] = (
                        ajustado.get(sensor, {}).get("SPD02", "")
                    )

                resultado_final[sensor] = resultado_sensor

            resultado_final["BandaY1"] = (
                ajustado.get("SP", {}).get("BandaY1", "")
            )

            resultado_final["BandaY2"] = (
                ajustado.get("SP", {}).get("BandaY2", "")
            )

            resultados.append({
                **prompt,
                "resultado": json.dumps(
                    resultado_final,
                    ensure_ascii=False
                )
            })

        except Exception as e:

            console.print(f"❌ Error procesando fila: {e}")

    # ==============================
    # 💾 EXPORTAR RESULTADOS
    # ==============================
    df_resultados = pd.DataFrame(resultados)

    salida = "resultado_hvac.xlsx"

    df_resultados.to_excel(salida, index=False)

    console.print(f"\n✅ Archivo generado: {salida}")