from rich.console import Console
from train import ejecutar_entrenamiento
from datetime import date, timedelta 
from src.app.equipos_hvac.hvac_model import cargar, predecir
from src.app.equipos_hvac.hvac_rules import (
    evaluar_estado,
    evaluar_queja,
    calcular_porcentajes_operacion
)
import pandas as pd
from rich.console import Console
from rich.progress import track
from src.api.gsepro import GSEClient
from src.database.dbPosgres import get_connection
from psycopg2.extras import execute_values
import math

console = Console()

# ==============================
# UTILS
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

def clean_value(value):
    if pd.isna(value):
        return None

    if isinstance(value, str) and not value.strip():
        return None

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value

def clean_int(value):
    value = clean_value(value)
    return int(value) if value is not None else None

def redondear_valor(valor):
    valor = clean_value(valor)
    if valor is None:
        return None

    decimal = valor - math.floor(valor)

    if decimal <= 0.5:
        return math.floor(valor)

    return math.ceil(valor)


# Entrenar conocimiento con los ultimos datos
ejecutar_entrenamiento()

# Obtener datos un dia antes
ayer = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
# fecha de consulta de temp: ayer + 2

if __name__ == "__main__":

    model, columns, targets = cargar()
    console.print("📦 Modelo cargado\n")

    gse = GSEClient()

    cliente = next(
        (c for c in gse.clientes_regiones() if c["idCliente"] == 160),
        None
    )

    regiones = cliente["regiones"]

    todos_los_equipos = []

    for region in regiones:
        idRegion = region["idRegion"]
        nombre = region["nombre"]

        try:
            equipos = gse.hvac_valores(160, ayer, ayer, idRegion)

            if not equipos:
                continue

            # Agregar región a cada registro (opcional)
            for equipo in equipos:
                equipo["idRegion"] = idRegion
                equipo["region"] = nombre

            todos_los_equipos.extend(equipos)

        except Exception as e:
            print(f"💥 Error API - [{ayer}] - ({nombre}) {idRegion}: {e}")

    # DataFrame unificado
    df = pd.DataFrame(todos_los_equipos)

    console.print(f"✅ Registros encontrados: {len(df)}\n")

    resultados = []
    equipos_excluidos = 0
    # ==============================
    # 🔁 RECORRER EQUIPOS
    # ==============================
    for _, row in track(df.iterrows(), total=len(df), description="Procesando equipos..."):

        try:

            prompt = row.to_dict()
            # ==============================
            # EQUIPOS EXCLUIDOS
            # ==============================
            tecnologia = str(prompt.get("Tecnologia", "")).strip().lower()

            if tecnologia in ("sensibo", "n/a"):
                equipos_excluidos += 1
                continue
            
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

            algoritmo_tag_sp = ajustado.get("SP", {}).get("algoritmo_tag_SP", None)
            algoritmo_tag_spd1 = ajustado.get("SPD1", {}).get("algoritmo_tag_SPD1", None)
            algoritmo_tag_spd2 = ajustado.get("SPD2", {}).get("algoritmo_tag_SPD2", None)

            resultado_final = {
                "estado": estado,
                "queja": queja
            }

            for sensor in ["SP", "SPD1", "SPD2"]:

                resultado_sensor = {
                    "operacion_pct": operacion.get(sensor, {}).get("operacion_pct", ""),
                    "temp_prom": operacion.get(sensor, {}).get("temp_prom", ""),
                    "motivo" : ajustado.get(sensor, {}).get("motivo", ""),
                    "motivo_detallado": ajustado.get(sensor, {}).get("motivo_detallado", ""),
                    "clima": ajustado.get(sensor, {}).get("clima", ""),
                }

                if sensor == "SP":
                    valor = ajustado.get(sensor, {}).get("SP")
                    resultado_sensor["SP"] = redondear_valor(valor)

                elif sensor == "SPD1":
                    valor = ajustado.get(sensor, {}).get("SPD01")
                    resultado_sensor["SPD01"] = redondear_valor(valor)

                elif sensor == "SPD2":
                    valor = ajustado.get(sensor, {}).get("SPD02")
                    resultado_sensor["SPD02"] = redondear_valor(valor)

                resultado_final[sensor] = resultado_sensor

            resultado_final["BandaY1"] = (
                ajustado.get("SP", {}).get("BandaY1", "")
            )

            resultado_final["BandaY2"] = (
                ajustado.get("SP", {}).get("BandaY2", "")
            )

            clean_data = {
                "idvbox": str(prompt.get("idVbox")),
                "cc": prompt.get("CC"),
                "sucursal": prompt.get("Sucursal"),
                "ubicacion": prompt.get("Ubicacion"),
                "tecnologia": prompt.get("Tecnologia"),
                "fecha": prompt.get("Fecha"),
                "region": prompt.get("Region"),
                "estado": prompt.get("Estado"),
                "ciudad": prompt.get("Ciudad"),

                "latitud": clean_value(prompt.get("Latitud")),
                "longitud": clean_value(prompt.get("Longitud")),

                "tipo_hvac": prompt.get("Tipo de HVAC"),

                "tz": clean_value(prompt.get("TZ")),
                "tz_spd1": clean_value(prompt.get("TZ SPD 01")),
                "tz_spd2": clean_value(prompt.get("TZ SPD 02")),
                "tz_sp": clean_value(prompt.get("TZ SP")),

                "tc": clean_value(prompt.get("TC")),

                "tiy1": clean_value(prompt.get("TIY1")),
                "tiy1_spd1": clean_value(prompt.get("TI Y1 SPD 01")),
                "tiy1_spd2": clean_value(prompt.get("TI Y1 SPD 02")),
                "tiy1_sp": clean_value(prompt.get("TI Y1 SP")),

                "tiy2": clean_value(prompt.get("TIY2")),
                "tiy2_spd1": clean_value(prompt.get("TI Y2 SPD 01")),
                "tiy2_spd2": clean_value(prompt.get("TI Y2 SPD 02")),
                "tiy2_sp": clean_value(prompt.get("TI Y2 SP")),

                "y1": clean_value(prompt.get("Y1")),
                "y1_spd1": clean_value(prompt.get("Y1 SPD 01")),
                "y1_spd2": clean_value(prompt.get("Y1 SPD 02")),
                "y1_sp": clean_value(prompt.get("Y1 SP")),

                "y2": clean_value(prompt.get("Y2")),
                "y2_spd1": clean_value(prompt.get("Y2 SPD 01")),
                "y2_spd2": clean_value(prompt.get("Y2 SPD 02")),
                "y2_sp": clean_value(prompt.get("Y2 SP")),

                "banday1": clean_int(prompt.get("BandaY1")),
                "banday2": clean_int(prompt.get("BandaY2")),

                "sp": clean_value(prompt.get("SP")),
                "spd1": clean_value(prompt.get("SPD01")),
                "spd2": clean_value(prompt.get("SPD03")),

                "cambios_sp": clean_int(prompt.get("CambiosSP")),
                "alerta_ti_danado": clean_value(prompt.get("AlertaTIdanado")),
                "ti_offline": clean_value(prompt.get("TI Offline")),
                "control_gse": clean_value(prompt.get("CtrlGSE")),

                "clima_sp": clean_value(resultado_final.get("SP", {}).get("clima")),
                "temp_prom_sp": clean_value(resultado_final.get("SP", {}).get("temp_prom")),
                "operacion_pct_sp": clean_value(resultado_final.get("SP", {}).get("operacion_pct")),

                "clima_spd1": clean_value(resultado_final.get("SPD1", {}).get("clima")),
                "temp_prom_spd1": clean_value(resultado_final.get("SPD1", {}).get("temp_prom")),
                "operacion_pct_spd1": clean_value(resultado_final.get("SPD1", {}).get("operacion_pct")),

                "clima_spd2": clean_value(resultado_final.get("SPD2", {}).get("clima")),
                "temp_prom_spd2": clean_value(resultado_final.get("SPD2", {}).get("temp_prom")),
                "operacion_pct_spd2": clean_value(resultado_final.get("SPD2", {}).get("operacion_pct")),

                "estatus": clean_value(resultado_final.get("estado")),
                "queja": clean_value(resultado_final.get("queja")),

                "resultado_sp": clean_value(resultado_final.get("SP", {}).get("SP")),
                "motivo_sp": clean_value(resultado_final.get("SP", {}).get("motivo")[0]),
                "motivo_detallado_sp": clean_value(resultado_final.get("SP", {}).get("motivo_detallado")),
                "estrategia_sp": algoritmo_tag_sp,

                "resultado_spd1": clean_value(resultado_final.get("SPD1", {}).get("SPD01")),
                "motivo_spd1": clean_value(resultado_final.get("SPD1", {}).get("motivo")[1]),
                "motivo_detallado_spd1": clean_value(resultado_final.get("SPD1", {}).get("motivo_detallado")),
                "estrategia_spd1": algoritmo_tag_spd1,

                "resultado_spd2": clean_value(resultado_final.get("SPD2", {}).get("SPD02")),
                "motivo_spd2": clean_value(resultado_final.get("SPD2", {}).get("motivo")[2]),
                "motivo_detallado_spd2": clean_value(resultado_final.get("SPD2", {}).get("motivo_detallado")),
                "estrategia_spd2": algoritmo_tag_spd2,

                "resultado_banday1": clean_value(resultado_final.get("BandaY1")),
                "resultado_banday2": clean_value(resultado_final.get("BandaY2")),
            }

            resultados.append(clean_data)

        except Exception as e:
            console.print(f"❌ Error procesando fila: {e}")

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO public.estrategias(
        idvbox, cc, sucursal, ubicacion, tecnologia, fecha, region, estado,
        latitud, longitud, tipo_hvac, tz, tz_spd1, tz_spd2, tz_sp, tc,
        tiy1, tiy1_spd1, tiy1_spd2, tiy1_sp, tiy2, tiy2_spd1, tiy2_spd2, tiy2_sp,
        y1, y1_spd1, y1_spd2, y1_sp, y2, y2_spd1, y2_spd2, y2_sp,
        banday1, banday2, sp, spd1, spd2, cambios_sp, alerta_ti_danado,
        ti_offline, clima_sp, temp_prom_sp, operacion_pct_sp,
        clima_spd1, temp_prom_spd1, operacion_pct_spd1,
        clima_spd2, temp_prom_spd2, operacion_pct_spd2,
        estatus, queja,
        resultado_sp, motivo_sp, motivo_detallado_sp, estrategia_sp,
        resultado_spd1, motivo_spd1, motivo_detallado_spd1, estrategia_spd1,
        resultado_spd2, motivo_spd2, motivo_detallado_spd2, estrategia_spd2,
        resultado_banday1, resultado_banday2, control_gse, ciudad
    )
    VALUES %s
    """

    valores = [
        (
            r["idvbox"],
            r["cc"],
            r["sucursal"],
            r["ubicacion"],
            r["tecnologia"],
            r["fecha"],
            r["region"],
            r["estado"],
            r["latitud"],
            r["longitud"],
            r["tipo_hvac"],
            r["tz"],
            r["tz_spd1"],
            r["tz_spd2"],
            r["tz_sp"],
            r["tc"],
            r["tiy1"],
            r["tiy1_spd1"],
            r["tiy1_spd2"],
            r["tiy1_sp"],
            r["tiy2"],
            r["tiy2_spd1"],
            r["tiy2_spd2"],
            r["tiy2_sp"],
            r["y1"],
            r["y1_spd1"],
            r["y1_spd2"],
            r["y1_sp"],
            r["y2"],
            r["y2_spd1"],
            r["y2_spd2"],
            r["y2_sp"],
            r["banday1"],
            r["banday2"],
            r["sp"],
            r["spd1"],
            r["spd2"],
            r["cambios_sp"],
            r["alerta_ti_danado"],
            r["ti_offline"],
            r["clima_sp"],
            r["temp_prom_sp"],
            r["operacion_pct_sp"],
            r["clima_spd1"],
            r["temp_prom_spd1"],
            r["operacion_pct_spd1"],
            r["clima_spd2"],
            r["temp_prom_spd2"],
            r["operacion_pct_spd2"],
            r["estatus"],
            r["queja"],
            r["resultado_sp"],
            r["motivo_sp"],
            r["motivo_detallado_sp"],
            r["estrategia_sp"],
            r["resultado_spd1"],
            r["motivo_spd1"],
            r["motivo_detallado_spd1"],
            r["estrategia_spd1"],
            r["resultado_spd2"],
            r["motivo_spd2"],
            r["motivo_detallado_spd2"],
            r["estrategia_spd2"],
            r["resultado_banday1"],
            r["resultado_banday2"],
            r["control_gse"],
            r["ciudad"]
        )
        for r in resultados
    ]

    execute_values(
        cursor,
        sql,
        valores,
        page_size=1000  # ajusta según volumen
    )

    conn.commit()

    print(f"✅ {len(valores)} registros insertados")
    console.log(f"{equipos_excluidos} equipos excluidos")
    console.log(f"Total procesado: {equipos_excluidos + len(valores)}")
    cursor.close()
    conn.close()