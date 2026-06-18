#!/usr/bin/env python3

import time
import traceback
from datetime import datetime

from src.app.equipos_hvac.ia import entrenar_modelo
from src.app.equipos_hvac.dataset import obtener_ultima_fecha

# ==============================
# 🧾 LOG
# ==============================
def log(msg, tipo="INFO"):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{tipo}] {msg}")


# ==============================
# 🧠 CONTROL DE ENTRENAMIENTO
# ==============================
ultima_fecha_entrenada = None


def hay_datos_nuevos():
    global ultima_fecha_entrenada

    fecha_actual = obtener_ultima_fecha()

    if fecha_actual is None:
        return True

    if ultima_fecha_entrenada is None:
        ultima_fecha_entrenada = fecha_actual
        return True

    if fecha_actual > ultima_fecha_entrenada:
        ultima_fecha_entrenada = fecha_actual
        return True

    return False


# ==============================
# 🚀 EJECUCIÓN
# ==============================
def ejecutar_entrenamiento():
    try:
        if not hay_datos_nuevos():
            log("⏭️ Sin datos nuevos, se omite entrenamiento", "SKIP")
            return

        inicio = time.time()

        entrenar_modelo()

        fin = time.time()
        duracion = round(fin - inicio, 2)

        log(f"✅ Entrenamiento completado en {duracion}s", "SUCCESS")

    except Exception as e:
        log("❌ Error en entrenamiento", "ERROR")
        log(str(e), "ERROR")
        traceback.print_exc()


# ==============================
# 🔁 LOOP
# ==============================
def loop_entrenamiento(intervalo_segundos=21600):

    log(f"🔁 Modo automático cada {intervalo_segundos/3600} horas")

    while True:
        ejecutar_entrenamiento()

        log(f"⏳ Esperando {intervalo_segundos} segundos...\n")
        time.sleep(intervalo_segundos)


# ==============================
# 🎛️ CLI
# ==============================
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Entrenamiento HVAC ML")

    parser.add_argument(
        "--loop",
        action="store_true",
        help="Ejecutar entrenamiento continuo"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=21600,
        help="Intervalo en segundos (default: 6h)"
    )

    args = parser.parse_args()

    if args.loop:
        loop_entrenamiento(args.interval)
    else:
        ejecutar_entrenamiento()