import pandas as pd
import json

# =========================
# CONFIGURACIÓN
# =========================

ARCHIVO_ENTRADA = "resultado_hvac.xlsx"
HOJA = "Sheet1"
COLUMNA_JSON = "resultado"

ARCHIVO_SALIDA = "resultado_json.xlsx"

# =========================
# FUNCIONES
# =========================

def limpiar_json(texto: str):

    if pd.isna(texto):
        return None

    texto = str(texto).strip()

    # convertir NaN inválido
    texto = texto.replace(": NaN", ": null")

    try:
        return json.loads(texto)
    except Exception as e:
        print(f"Error parseando JSON:\n{e}\n")
        return None


def obtener_valor(data, ruta, default=None):

    try:
        for key in ruta:
            data = data[key]
        return data
    except Exception:
        return default


# =========================
# LEER EXCEL
# =========================

df = pd.read_excel(
    ARCHIVO_ENTRADA,
    sheet_name=HOJA
)

# =========================
# PARSEAR JSON
# =========================

json_parseado = df[COLUMNA_JSON].apply(
    limpiar_json
)

# =========================
# DATOS GENERALES
# =========================

df["estado"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["estado"])
)

df["queja"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["queja"])
)

# =========================
# SP
# =========================

df["sp"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SP", "SP"])
)

df["clima_sp"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SP", "clima"])
)

df["motivo_sp"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SP", "motivo"])
)

df["temp_prom_sp"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SP", "temp_prom"])
)

df["operacion_pct_sp"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SP", "operacion_pct"])
)

# =========================
# SPD1
# =========================

df["spd01"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SPD1", "SPD01"])
)

df["clima_spd1"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SPD1", "clima"])
)

df["motivo_spd1"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SPD1", "motivo"])
)

df["temp_prom_spd1"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SPD1", "temp_prom"])
)

df["operacion_pct_spd1"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SPD1", "operacion_pct"])
)

# =========================
# SPD2
# =========================

df["spd02"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SPD2", "SPD02"])
)

df["clima_spd2"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SPD2", "clima"])
)

df["motivo_spd2"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SPD2", "motivo"])
)

df["temp_prom_spd2"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SPD2", "temp_prom"])
)

df["operacion_pct_spd2"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["SPD2", "operacion_pct"])
)

# =========================
# BANDAS
# =========================

df["banday1"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["BandaY1"])
)

df["banday2"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["BandaY2"])
)

# =========================
# EXPORTAR
# =========================

df.to_excel(
    ARCHIVO_SALIDA,
    index=False
)

print(f"\n✅ Archivo generado: {ARCHIVO_SALIDA}")