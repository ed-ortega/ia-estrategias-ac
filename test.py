import pandas as pd
import json

ARCHIVO_ENTRADA = "resultado_hvac.xlsx"
HOJA = "Sheet1"
COLUMNA_JSON = "resultado"
ARCHIVO_SALIDA = "resultado_json.xlsx"

def parse_json_safe(texto):
    """Parsea JSON manejando errores y mostrando la causa."""
    if pd.isna(texto):
        return None
    texto = str(texto).strip()
    if texto == "":
        return None
    # Reemplazar NaN no válidos
    texto = texto.replace(": NaN", ": null")
    try:
        return json.loads(texto)
    except json.JSONDecodeError as e:
        print(f"❌ Error JSON en fila: {e}")
        print("Fragmento problemático:", texto[:200])
        return None

def extraer_campo(parsed, ruta):
    """Extrae un campo siguiendo una lista de claves."""
    if parsed is None:
        return None
    try:
        for key in ruta:
            parsed = parsed[key]
        return parsed
    except (KeyError, TypeError):
        return None

# Leer archivo
df = pd.read_excel(ARCHIVO_ENTRADA, sheet_name=HOJA)
print(f"📄 Filas leídas: {len(df)}")

# Parsear JSON
json_parsed = df[COLUMNA_JSON].apply(parse_json_safe)

# Verificar cuántos parseos fueron exitosos
num_validos = json_parsed.notna().sum()
print(f"✅ JSON válidos: {num_validos} / {len(df)}")

# Extraer campos generales
df["estado"] = json_parsed.apply(lambda x: extraer_campo(x, ["estado"]))
df["queja"] = json_parsed.apply(lambda x: extraer_campo(x, ["queja"]))

# Extraer campos para SP
df["resultado_sp"] = json_parsed.apply(lambda x: extraer_campo(x, ["SP", "SP"]))
df["clima_sp"] = json_parsed.apply(lambda x: extraer_campo(x, ["SP", "clima"]))
df["motivo_sp"] = json_parsed.apply(lambda x: extraer_campo(x, ["SP", "motivo"]))
df["motivo_detallado_sp"] = json_parsed.apply(
    lambda x: (extraer_campo(x, ["SP", "motivo_detallado"]) or "").replace("\n", " ")
)
df["temp_prom_sp"] = json_parsed.apply(lambda x: extraer_campo(x, ["SP", "temp_prom"]))
df["operacion_pct_sp"] = json_parsed.apply(lambda x: extraer_campo(x, ["SP", "operacion_pct"]))

# Extraer campos para SPD1
df["resultado_spd1"] = json_parsed.apply(lambda x: extraer_campo(x, ["SPD1", "SPD01"]))
df["clima_spd1"] = json_parsed.apply(lambda x: extraer_campo(x, ["SPD1", "clima"]))
df["motivo_spd1"] = json_parsed.apply(lambda x: extraer_campo(x, ["SPD1", "motivo"]))
df["motivo_detallado_spd1"] = json_parsed.apply(
    lambda x: (extraer_campo(x, ["SPD1", "motivo_detallado"]) or "").replace("\n", " ")
)
df["temp_prom_spd1"] = json_parsed.apply(lambda x: extraer_campo(x, ["SPD1", "temp_prom"]))
df["operacion_pct_spd1"] = json_parsed.apply(lambda x: extraer_campo(x, ["SPD1", "operacion_pct"]))

# Extraer campos para SPD2
df["resultado_spd2"] = json_parsed.apply(lambda x: extraer_campo(x, ["SPD2", "SPD02"]))
df["clima_spd2"] = json_parsed.apply(lambda x: extraer_campo(x, ["SPD2", "clima"]))
df["motivo_spd2"] = json_parsed.apply(lambda x: extraer_campo(x, ["SPD2", "motivo"]))
df["motivo_detallado_spd2"] = json_parsed.apply(
    lambda x: (extraer_campo(x, ["SPD2", "motivo_detallado"]) or "").replace("\n", " ")
)
df["temp_prom_spd2"] = json_parsed.apply(lambda x: extraer_campo(x, ["SPD2", "temp_prom"]))
df["operacion_pct_spd2"] = json_parsed.apply(lambda x: extraer_campo(x, ["SPD2", "operacion_pct"]))

# Bandas (nota: en tu JSON BandaY1 y BandaY2 están al mismo nivel que SP, SPD1, SPD2)
df["resultado_bandaY1"] = json_parsed.apply(lambda x: extraer_campo(x, ["BandaY1"]))
df["resultado_bandaY2"] = json_parsed.apply(lambda x: extraer_campo(x, ["BandaY2"]))

# Mostrar primeras filas de las nuevas columnas para verificar
print("\n🔍 Muestra de motivos detallados extraídos:")
print(df[["motivo_detallado_sp", "motivo_detallado_spd1", "motivo_detallado_spd2"]].head())

# Exportar
df.to_excel(ARCHIVO_SALIDA, index=False)
print(f"\n✅ Archivo generado: {ARCHIVO_SALIDA}")

# Después de exportar, lee el mismo archivo y muestra una muestra
df_check = pd.read_excel(ARCHIVO_SALIDA)
print("\n🔍 Verificación post-exportación:")
print(df_check[["motivo_detallado_sp", "motivo_detallado_spd1", "motivo_detallado_spd2"]].head(2))