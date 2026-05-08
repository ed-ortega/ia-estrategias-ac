"""
Motor de reglas HVAC basado en estrategias del Excel.

Flujo:
    1. modelo predice SP/SPD01/SPD02 normalizados (qué deberían ser)
    2. aplicar_reglas_hvac() ajusta esos valores según condiciones operativas
"""


from datetime import datetime, timedelta
from rich.console import Console
import pandas as pd
import requests
import unicodedata

console = Console()

# ==============================
# 🗺️ MAPEO REGIÓN → GRUPO
# ==============================
REGION_A_GRUPO: dict[str, str] = {
    # NL / Noreste / Mexicali / Sonora / GDL
    "nuevo leon":       "NL",
    "nuevo león":       "NL",
    "nl":               "NL",
    "noreste":          "NL",
    "monterrey":        "NL",
    "mexicali":         "NL",
    "sonora":           "NL",
    "hermosillo":       "NL",
    "gdl":              "NL",
    "guadalajara":      "NL",
    "jalisco":          "NL",
    # Sureste
    "sureste":          "Sureste",
    "yucatan":          "Sureste",
    "yucatán":          "Sureste",
    "merida":           "Sureste",
    "mérida":           "Sureste",
    "quintana roo":     "Sureste",
    "cancun":           "Sureste",
    "cancún":           "Sureste",
    # BC
    "bc":               "BC",
    "baja california":  "BC",
    "tijuana":          "BC",
    "ensenada":         "BC",
    "rosarito":         "BC",
    # Metro
    "metro":            "Metro",
    "cdmx":             "Metro",
    "ciudad de mexico": "Metro",
    "ciudad de méxico": "Metro",
    "puebla":           "Metro",
    "morelos":          "Metro",
    "estado de mexico": "Metro",
    "estado de méxico": "Metro",
    "edomex":           "Metro",
}


def _grupo(region: str | None) -> str:
    """Normaliza la región al grupo correspondiente. Default: NL."""
    if not region:
        return "NL"
    return REGION_A_GRUPO.get(region.lower().strip(), "NL")


# ==============================
# 📐 RANGOS VÁLIDOS POR REGIÓN
# ==============================
# limite_alto=True  → rangos más ajustados (ej. NL >15%)
# limite_alto=False → rangos más amplios  (ej. NL <15%)
RANGOS: dict[str, dict[bool, dict[str, tuple[int, int]]]] = {
    "NL": {
        True:  {"SP": (70, 73), "SPD01": (71, 77), "SPD02": (71, 76)},
        False: {"SP": (70, 74), "SPD01": (71, 78), "SPD02": (71, 77)},
    },
    "Sureste": {
        True:  {"SP": (70, 72), "SPD01": (71, 76), "SPD02": (71, 75)},
        False: {"SP": (70, 73), "SPD01": (71, 77), "SPD02": (71, 76)},
    },
    "BC": {
        True:  {"SP": (70, 74), "SPD01": (71, 77), "SPD02": (71, 76)},
        False: {"SP": (70, 75), "SPD01": (71, 78), "SPD02": (71, 77)},
    },
    "Metro": {
        True:  {"SP": (70, 73), "SPD01": (71, 77), "SPD02": (71, 76)},
        False: {"SP": (70, 74), "SPD01": (71, 78), "SPD02": (71, 77)},
    },
}

# ==============================
# 📋 UMBRALES OPERATIVOS
# ==============================
# Cada entrada define:
#   queja_si/no  → {spd1, spd2} % mínimo para considerarse "alto"
#   idoneo       → {spd1_min, spd1_max, spd2_min, spd2_max, sp_min}
#   adj_alto_*   → ajuste cuando está en zona alta
#   adj_idoneo   → ajuste cuando está en zona ideal (sin cambios)
#   adj_bajo     → ajuste cuando está por debajo del rango
#
# Formato de ajuste por campo:
#   None                  → Sin cambios (conservar predicción del modelo)
#   ("zt_spd01", delta)   → TZ_SPD01 + delta
#   ("zt_spd02", delta)   → TZ_SPD02 + delta
#   ("zt_sp",    delta)   → TZ_SP    + delta
#   ("fixed",    valor)   → valor fijo

_K = None  # alias para "Sin cambios"

UMBRALES: dict[str, dict[str, dict]] = {
    "NL": {
        "Ok_TI_baja": {
            "queja_si":  {"spd1": 70, "spd2": 85},
            "queja_no":  {"spd1": 70, "spd2": 85},
            "idoneo":    {"spd1_min": 30, "spd1_max": 70, "spd2_min": 45, "spd2_max": 85, "sp_min": 60},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +0.5), "SPD02": _K},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +0.5), "SPD02": ("zt_spd02", +0.5)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -1.0), "SPD02": ("zt_spd02", -1.0)},
        },
        "No_enfria_TI_alta": {
            "queja_si":  {"spd1": 50, "spd2": 70},
            "queja_no":  {"spd1": 50, "spd2": 70},
            "idoneo":    {"spd1_min": 30, "spd1_max": 50, "spd2_min": 45, "spd2_max": 70, "sp_min": 60},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +1.0)},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +1.0)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -0.5), "SPD02": ("zt_spd02", -0.5)},
        },
    },
    "Sureste": {
        "Ok_TI_baja": {
            "queja_si":  {"spd1": 80, "spd2": 90},
            "queja_no":  {"spd1": 80, "spd2": 90},
            "idoneo":    {"spd1_min": 50, "spd1_max": 80, "spd2_min": 60, "spd2_max": 90, "sp_min": 70},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +0.5), "SPD02": _K},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +0.5), "SPD02": ("zt_spd02", +0.5)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -1.0), "SPD02": ("zt_spd02", -1.0)},
        },
        "No_enfria_TI_alta": {
            "queja_si":  {"spd1": 70, "spd2": 90},
            "queja_no":  {"spd1": 60, "spd2": 70},
            "idoneo":    {"spd1_min": 50, "spd1_max": 60, "spd2_min": 60, "spd2_max": 70, "sp_min": 70},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +1.0)},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +1.0)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -0.5), "SPD02": ("zt_spd02", -0.5)},
        },
    },
    "BC": {
        "Ok_TI_baja": {
            "queja_si":  {"spd1": 50, "spd2": 60},
            "queja_no":  {"spd1": 40, "spd2": 50},
            "idoneo":    {"spd1_min": 10, "spd1_max": 40, "spd2_min": 20, "spd2_max": 50, "sp_min": 30},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +0.5), "SPD02": _K},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +0.5), "SPD02": ("zt_spd02", +0.5)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -1.0), "SPD02": ("zt_spd02", -1.0)},
        },
        "No_enfria_TI_alta": {
            "queja_si":  {"spd1": 50, "spd2": 60},
            "queja_no":  {"spd1": 40, "spd2": 50},
            "idoneo":    {"spd1_min": 10, "spd1_max": 40, "spd2_min": 20, "spd2_max": 50, "sp_min": 30},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +1.0)},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +1.0)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -0.5), "SPD02": ("zt_spd02", -0.5)},
        },
    },
    "Metro": {
        "Ok_TI_baja": {
            "queja_si":  {"spd1": 60, "spd2": 70},
            "queja_no":  {"spd1": 50, "spd2": 60},
            "idoneo":    {"spd1_min": 30, "spd1_max": 50, "spd2_min": 40, "spd2_max": 60, "sp_min": 50},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +0.5), "SPD02": _K},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +0.5), "SPD02": ("zt_spd02", +0.5)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -1.0), "SPD02": ("zt_spd02", -1.0)},
        },
        "No_enfria_TI_alta": {
            "queja_si":  {"spd1": 60, "spd2": 70},
            "queja_no":  {"spd1": 50, "spd2": 60},
            "idoneo":    {"spd1_min": 30, "spd1_max": 50, "spd2_min": 40, "spd2_max": 60, "sp_min": 50},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +1.0)},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +1.0)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -0.5), "SPD02": ("zt_spd02", -0.5)},
        },
    },
}

# ==============================
# 🕐 UTILIDADES HORARIAS
# ==============================
def _horas_entre(inicio: str, fin: str) -> float:
    """Horas entre dos strings HH:MM. Soporta cruce de medianoche."""
    fmt = "%H:%M"
    t1 = datetime.strptime(inicio, fmt)
    t2 = datetime.strptime(fin, fmt)
    
    diff = (t2 - t1).total_seconds() / 3600
    return diff + 24 if diff < 0 else diff

def clamp_pct(valor):
    return min(max(valor, 0), 100)

ESTADOS_COORDS = {
    "ciudad de mexico": {"lat": 19.4326, "lon": -99.1332},
    "quintana roo": {"lat": 21.1631, "lon": -86.8023},
    "yucatan": {"lat": 20.9674, "lon": -89.5926},
    "morelos": {"lat": 18.9242, "lon": -99.2216},
    "jalisco": {"lat": 16.43033, "lon": -91.97499},
}

def normalizar_estado(nombre):
    if not nombre:
        return ""

    nombre = nombre.strip().lower()

    # quitar acentos
    nombre = ''.join(
        c for c in unicodedata.normalize('NFD', nombre)
        if unicodedata.category(c) != 'Mn'
    )

    return nombre

def calcular_porcentajes_operacion(data: dict) -> dict:

    # =========================
    # 🔵 TU LÓGICA ORIGINAL
    # =========================
    h_spd1 = _horas_entre(
        data.get("horario_inicio_SPD_01", "00:00"),
        data.get("horario_fin_SPD_01",   "00:00"),
    )
    h_spd2 = _horas_entre(
        data.get("horario_inicio_SPD_02", "00:00"),
        data.get("horario_fin_SPD_02",   "00:00"),
    )
    h_sp = max(24.0 - h_spd1 - h_spd2, 0.0)
    
    

    y1_spd1 = float(data.get("Y1 SPD 01") or 0)
    y1_spd2 = float(data.get("Y1 SPD 02") or 0)
    y1_sp   = float(data.get("Y1 SP")     or 0)

    def pct(y, h):
        if not h:
            return 0.0
        return round(clamp_pct((y / h) * 100), 2)

    resultado = {
        "SPD1": {"operacion_pct": pct(y1_spd1, h_spd1)},
        "SPD2": {"operacion_pct": pct(y1_spd2, h_spd2)},
        "SP":   {"operacion_pct": pct(y1_sp,   h_sp)},
    }

    # =========================
    # 🔴 CLIMA (AUTOMÁTICO)
    # =========================
    lat = data.get("Latitud")
    lon = data.get("Longitud")

    if not lat or not lon:
        estado = normalizar_estado(data.get("Estado"))
        coords = ESTADOS_COORDS.get(estado)
        if coords:
            lat, lon = coords["lat"], coords["lon"]
    if lat and lon:
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&hourly=apparent_temperature"
                f"&temperature_unit=fahrenheit"
                f"&timezone=auto"
            )

            resp = requests.get(url, timeout=10)
            
            clima = resp.json()

            df = pd.DataFrame({
                "time": clima["hourly"]["time"],
                "at": clima["hourly"]["apparent_temperature"]
            })

            df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(None)

            # 👉 mañana basado en tu data
            fechas = sorted(df["time"].dt.date.unique())

            if len(fechas) >= 2:
                mañana = fechas[1]
            else:
                mañana = fechas[0]  # fallback

            df = df[df["time"].dt.date == mañana]

            def filtrar_periodo(inicio, fin):
                h_ini = int(inicio.split(":")[0])
                h_fin = int(fin.split(":")[0])

                if h_ini <= h_fin:
                    return df[(df["time"].dt.hour >= h_ini) & (df["time"].dt.hour <= h_fin)]
                else:
                    return df[(df["time"].dt.hour >= h_ini) | (df["time"].dt.hour <= h_fin)]

            spd1_df = filtrar_periodo(
                data.get("horario_inicio_SPD_01", "00:00"),
                data.get("horario_fin_SPD_01",   "06:00"),
            )

            spd2_df = filtrar_periodo(
                data.get("horario_inicio_SPD_02", "20:00"),
                data.get("horario_fin_SPD_02",   "23:59"),
            )

            horas_spd = set(spd1_df["time"].dt.hour.tolist() + spd2_df["time"].dt.hour.tolist())
            sp_df = df[~df["time"].dt.hour.isin(horas_spd)]

            def stats(df_):
                if df_.empty:
                    return {"temp_min": 0, "temp_max": 0, "temp_prom": 0}
                return {
                    "temp_min": round(df_["at"].min(), 2),
                    "temp_max": round(df_["at"].max(), 2),
                    "temp_prom": round(df_["at"].mean(), 2),
                }

            resultado["SPD1"].update(stats(spd1_df))
            resultado["SPD2"].update(stats(spd2_df))
            resultado["SP"].update(stats(sp_df))

        except Exception as e:
            console.print(f"[red]Error obteniendo clima: {e}[/red]")

    return resultado

def clasificar_clima(temp_f):
    if temp_f > 92:
        return "Calor"
    elif temp_f >= 68:
        return "Templado"
    else:
        return "Frio"

# ==============================
# 🔧 APLICAR AJUSTE INDIVIDUAL
# ==============================
def _resolver_adj(
    campo:     str,
    instruccion,
    data:      dict,
    prediccion: dict,
) -> float:
    """
    Resuelve una instrucción de ajuste para un campo (SP, SPD01, SPD02).

    Instrucciones:
        None              → conservar predicción del modelo
        ("zt_spd01", d)   → TZ_SPD01 + d
        ("zt_spd02", d)   → TZ_SPD02 + d
        ("zt_sp",    d)   → TZ_SP    + d
        ("fixed",    v)   → valor fijo v
    """
    if instruccion is None:
        return float(prediccion[campo])

    tipo, valor = instruccion

    if tipo == "zt_spd01":
        tz = data.get("TZ SPD 01") or data.get("TZ") or prediccion[campo]
        return float(tz) + valor

    if tipo == "zt_spd02":
        tz = data.get("TZ SPD 02") or data.get("TZ") or prediccion[campo]
        return float(tz) + valor

    if tipo == "zt_sp":
        tz = data.get("TZ SP") or data.get("TZ") or prediccion[campo]
        return float(tz) + valor

    if tipo == "fixed":
        return float(valor)

    return float(prediccion[campo])

# ==============================
# 🔒 CLIPPING A RANGO VÁLIDO
# ==============================
def _clip(valor: float, campo: str, grupo: str, limite_alto: bool) -> int:
    rangos = RANGOS.get(grupo, RANGOS["NL"]).get(limite_alto, RANGOS["NL"][True])
    min_v, max_v = rangos.get(campo, (70, 77))
    return int(round(max(min_v, min(max_v, valor))))


# ==============================
# 🧠 EVALUADORES
# ==============================
def evaluar_estado(data: dict) -> str:
    """Ok / No enfria / Apagado / Sin control GSE / NA"""
    if not data.get("CtrlGSE"):
        return "Sin control GSE"

    TC = data.get("TC")

    if TC > 0.5:
        TIY1_SPD1 = data.get("TI Y1 SPD 01")
        TIY1_SPD2= data.get("TI Y1 SPD 02")
        TIY1_SP= data.get("TI Y1 SP")

        TIY2_SPD1 = data.get("TI Y2 SPD 01")
        TIY2_SPD2= data.get("TI Y2 SPD 02")
        TIY2_SP= data.get("TI Y2 SP")

        enfria = "Ok" if (
            (TIY1_SPD1 and TIY1_SPD1 <= 65) or
            (TIY1_SPD2 and TIY1_SPD2 <= 65) or
            (TIY1_SP and TIY1_SP <= 65) or
            (TIY2_SPD1 and TIY2_SPD1 <= 65) or
            (TIY2_SPD2 and TIY2_SPD2 <= 65) or
            (TIY2_SP and TIY2_SP <= 65)
        ) else "No enfria"

        return enfria

    else: 
        return "Apagado"

def evaluar_queja(data: dict) -> str:
    """Si / No / NA"""
    if not data.get("CtrlGSE"):
        return "NA"

    tz_sp = data.get("TZ SP")
    sp    = data.get("SP")

    if tz_sp is None or sp is None:
        return "NA"

    return "Si" if (tz_sp - sp) > 2 else "No"

# ==============================
# 🚀 FUNCIÓN PRINCIPAL
# ==============================
def aplicar_reglas_hvac(data: dict, prediccion: dict) -> dict:

    grupo       = _grupo(data.get("Estado"))
    limite_alto = bool(data.get("limite_sp_alto", True))
    alerta_ti   = (data.get("AlertaTIdanado") or 0) > 0
    cambios_sp  = data.get("CambiosSP") or 0

    estatus = evaluar_estado(data)
    queja   = evaluar_queja(data)

    resultado = dict(prediccion)  # copia de la predicción normalizada
    motivo    = "Sin ajuste"

    # Porcentajes de operación
    try:
        pct = calcular_porcentajes_operacion(data)
    except Exception:
        pct = {
            "SPD1": {"operacion_pct": 0},
            "SPD2": {"operacion_pct": 0},
            "SP": {"operacion_pct": 0, "temp_prom": 0},
        }

    temp_ref = pct["SP"].get("temp_prom", 0)

    clima = clasificar_clima(temp_ref)

    resultclima = {
        "temperaura": temp_ref,
        "clima": clima,
    }

    if clima != "Templado":
        return {
            **resultado,
            "SP":    '',
            "SPD01": '',
            "SPD02": '',
            "BandaY1": '',
            "BandaY2": '',
            "motivo": f"Clima: {clima} → reglas aún no implementadas"
        }

    # ------------------------------------------------------------------
    # CASO 1: Sin control GSE
    # ------------------------------------------------------------------
    if estatus == "Sin control GSE":
        motivo = "Sin control GSE"
        return {
            **resultado,
            "SP":    '',
            "SPD01": '',
            "SPD02": '',
            "BandaY1": '',
            "BandaY2": '',
            "motivo": motivo,
            **resultclima
        }

    # ------------------------------------------------------------------
    # CASO 2: Apagado + TI alta
    # ------------------------------------------------------------------
    ti_spd1 = data.get("TI Y1 SPD 01") or data.get("TIY1") or 0
    ti_alta = ti_spd1 > 65 or alerta_ti

    if estatus == "Apagado" and ti_alta:
        motivo = f"Apagado + TI {'(alerta)' if alerta_ti else '>65°F'}"
        return {
            **resultado,
            "SP":    '',
            "SPD01": '',
            "SPD02": '',
            "BandaY1": '',
            "BandaY2": '',
            "motivo": motivo,
            **resultclima
        }

    # ------------------------------------------------------------------
    # CASO 3: Reglas operativas (Ok / No enfria)
    # ------------------------------------------------------------------
    # Solo aplica si CambiosSP < 8
    if cambios_sp >= 8:
        motivo = f"CambiosSP={cambios_sp} ≥ 8 → sin ajuste automático"
        return {**resultado, "motivo": motivo, **resultclima}

    # Determinar rama de umbrales
    rama_estatus = "Ok_TI_baja" if not ti_alta else "No_enfria_TI_alta"
    umbrales_grupo = UMBRALES.get(grupo, UMBRALES["NL"])
    umbrales       = umbrales_grupo.get(rama_estatus, umbrales_grupo["Ok_TI_baja"])

    pct_spd1 = pct["SPD1"]["operacion_pct"]
    pct_spd2 = pct["SPD2"]["operacion_pct"]
    pct_sp   = pct["SP"]["operacion_pct"]

    # Umbral "alto" según queja
    q_key         = "queja_si" if queja == "Si" else "queja_no"
    thresh_alto   = umbrales[q_key]
    idoneo        = umbrales["idoneo"]

    # Clasificar zona operativa
    if pct_spd1 > thresh_alto["spd1"] or pct_spd2 > thresh_alto["spd2"]:
        adj_key   = f"adj_alto_{('si' if queja == 'Si' else 'no')}"
        motivo    = (
            f"TI={'alta' if ti_alta else 'baja'} | "
            f"Op SPD1={pct_spd1:.0f}% SPD2={pct_spd2:.0f}% → operación intensa"
        )
    elif (
        idoneo["spd1_min"] <= pct_spd1 <= idoneo["spd1_max"]
        or idoneo["spd2_min"] <= pct_spd2 <= idoneo["spd2_max"]
        or pct_sp >= idoneo["sp_min"]
    ):
        adj_key   = "adj_idoneo"
        motivo    = (
            f"TI={'alta' if ti_alta else 'baja'} | "
            f"Op SPD1={pct_spd1:.0f}% SPD2={pct_spd2:.0f}% → operación equilibrada"
        )
    else:
        adj_key   = "adj_bajo"
        motivo    = (
            f"TI={'alta' if ti_alta else 'baja'} | "
            f"Op SPD1={pct_spd1:.0f}% SPD2={pct_spd2:.0f}% → baja capacidad utilizada"
        )

    adj = umbrales[adj_key]

    # Aplicar ajustes y clipping
    for campo in ("SP", "SPD01", "SPD02"):
        valor_raw  = _resolver_adj(campo, adj[campo], data, prediccion)
        resultado[campo] = _clip(valor_raw, campo, grupo, limite_alto)

    resultado["motivo"] = motivo

    return {**resultado, **resultclima}
