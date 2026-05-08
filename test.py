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
    except:
        return default


# =========================
# LEER EXCEL
# =========================

df = pd.read_excel(ARCHIVO_ENTRADA, sheet_name=HOJA)

# =========================
# PARSEAR JSON
# =========================

json_parseado = df[COLUMNA_JSON].apply(limpiar_json)

# =========================
# EXTRAER DATOS
# =========================

df["estado"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["estado"])
)

df["queja"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["queja"])
)

# =========================
# MODELO AJUSTADO
# =========================

df["SP"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "ajustado", "SP"])
)

df["SPD01"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "ajustado", "SPD01"])
)

df["SPD02"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "ajustado", "SPD02"])
)

df["clima"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "ajustado", "clima"])
)

df["motivo"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "ajustado", "motivo"])
)

# =========================
# TEMPERATURAS
# =========================

df["temp_prom_SP"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["operacion", "SP", "temp_prom"])
)

df["temp_prom_SPD1"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["operacion", "SPD1", "temp_prom"])
)

df["temp_prom_SPD2"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["operacion", "SPD2", "temp_prom"])
)

# =========================
# OPERACION %
# =========================

df["operacion_pct_SP"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["operacion", "SP", "operacion_pct"])
)

df["operacion_pct_SPD1"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["operacion", "SPD1", "operacion_pct"])
)

df["operacion_pct_SPD2"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["operacion", "SPD2", "operacion_pct"])
)

# =========================
# NORMALIZADO
# =========================

df["normalizado_sp"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "normalizado", "SP"])
)

df["normalizado_spd1"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "normalizado", "SPD01"])
)

df["normalizado_spd2"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "normalizado", "SPD02"])
)

df["normalizado_banday1"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "normalizado", "BandaY1"])
)

df["normalizado_banday2"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "normalizado", "BandaY2"])
)

# =========================
# AJUSTADO
# =========================

df["ajustado_sp"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "ajustado", "SP"])
)

df["ajustado_spd1"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "ajustado", "SPD01"])
)

df["ajustado_spd2"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "ajustado", "SPD02"])
)

df["ajustado_banday1"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "ajustado", "BandaY1"])
)

df["ajustado_banday2"] = json_parseado.apply(
    lambda x: obtener_valor(x, ["modelo", "ajustado", "BandaY2"])
)

# =========================
# EXPORTAR
# =========================

df.to_excel(ARCHIVO_SALIDA, index=False)

print(f"\nArchivo generado: {ARCHIVO_SALIDA}")