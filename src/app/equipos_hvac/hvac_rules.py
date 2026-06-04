import math
from ...api.openmateo import obtener_clima
from datetime import datetime, time
from rich.console import Console
import pandas as pd
import requests
import unicodedata
from .templado import clima_templado
from .calor import clima_calido

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
# 🕐 UTILIDADES HORARIAS
# ==============================
def _horas_entre(inicio, fin) -> float:

    if isinstance(inicio, time):
        inicio = datetime.combine(datetime.today(), inicio)
    else:
        inicio = datetime.strptime(str(inicio), "%H:%M:%S")

    if isinstance(fin, time):
        fin = datetime.combine(datetime.today(), fin)
    else:
        fin = datetime.strptime(str(fin), "%H:%M:%S")

    diff = (fin - inicio).total_seconds() / 3600

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

CLIMA_DEFAULT = {
    "temp_min": 72,
    "temp_max": 88,
    "temp_prom": 80,
}

def normalizar_coord(valor):
    valor = float(valor)

    if abs(valor) > 1000:
        valor /= 1_000_000

    return valor

def to_float(valor, default=0.0):
    if pd.isna(valor):
        return default
    return float(valor)

def calcular_porcentajes_operacion(data: dict) -> dict:

    # =========================
    # 🔵 OPERACIÓN
    # =========================
    h_spd1 = _horas_entre(
        data.get("horario_inicio_SPD_01", "00:00"),
        data.get("horario_fin_SPD_01", "00:00"),
    )

    h_spd2 = _horas_entre(
        data.get("horario_inicio_SPD_02", "00:00"),
        data.get("horario_fin_SPD_02", "00:00"),
    )

    h_sp = max(24.0 - h_spd1 - h_spd2, 0.0)

    y1_spd1 = to_float(data.get("Y1 SPD 01"))
    y1_spd2 = to_float(data.get("Y1 SPD 02"))
    y1_sp   = to_float(data.get("Y1 SP"))

    def pct(y, h):
        if not h:
            return 0.0
        return round(clamp_pct((y / h) * 100), 2)

    resultado = {
        "SPD1": {
            "operacion_pct": pct(y1_spd1, h_spd1),
            **CLIMA_DEFAULT
        },
        "SPD2": {
            "operacion_pct": pct(y1_spd2, h_spd2),
            **CLIMA_DEFAULT
        },
        "SP": {
            "operacion_pct": pct(y1_sp, h_sp),
            **CLIMA_DEFAULT
        },
    }

    # =========================
    # 🔴 CLIMA
    # =========================
    def is_invalid(value):
        return pd.isna(value)

    lat = data.get("Latitud")
    lon = data.get("Longitud")
    
    lat = normalizar_coord(lat)
    lon = normalizar_coord(lon)

    # fallback por estado
    if is_invalid(lat) or is_invalid(lon):
        estado = normalizar_estado(data.get("Estado"))
        coords = ESTADOS_COORDS.get(estado)

        if coords:
            lat = coords["lat"]
            lon = coords["lon"]

    try:

        # =========================
        # PRIMER INTENTO: OPEN-METEO
        # =========================
        try:
            clima = obtener_clima(lat, lon, provider="openmeteo")

            if (
                "hourly" not in clima
                or "time" not in clima["hourly"]
                or "apparent_temperature" not in clima["hourly"]
            ):
                raise ValueError("Respuesta inválida de Open-Meteo")

        except Exception as e:
            console.print(
                f"[yellow]Open-Meteo falló ({e}), intentando WeatherAPI...[/yellow]"
            )

            clima = obtener_clima(lat, lon, provider="weatherapi")

            if (
                "hourly" not in clima
                or "time" not in clima["hourly"]
                or "apparent_temperature" not in clima["hourly"]
            ):
                raise ValueError("Respuesta inválida de WeatherAPI")

        # =========================
        # PROCESAMIENTO NORMAL
        # =========================
        df = pd.DataFrame({
            "time": clima["hourly"]["time"],
            "at": clima["hourly"]["apparent_temperature"]
        })

        if df.empty:
            return resultado

        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(None)

        fechas = sorted(df["time"].dt.date.unique())

        if len(fechas) >= 2:
            manana = fechas[1]
        else:
            manana = fechas[0]

        df = df[df["time"].dt.date == manana]

        if df.empty:
            return resultado

        
        def filtrar_periodo(inicio, fin):

            if isinstance(inicio, time):
                h_ini = inicio.hour
            else:
                h_ini = int(str(inicio).split(":")[0])

            if isinstance(fin, time):
                h_fin = fin.hour
            else:
                h_fin = int(str(fin).split(":")[0])

            if h_ini <= h_fin:
                return df[
                    (df["time"].dt.hour >= h_ini)
                    & (df["time"].dt.hour <= h_fin)
                ]

            return df[
                (df["time"].dt.hour >= h_ini)
                | (df["time"].dt.hour <= h_fin)
            ]

        spd1_df = filtrar_periodo(
            data.get("horario_inicio_SPD_01", "00:00"),
            data.get("horario_fin_SPD_01", "06:00"),
        )

        spd2_df = filtrar_periodo(
            data.get("horario_inicio_SPD_02", "20:00"),
            data.get("horario_fin_SPD_02", "23:59"),
        )

        horas_spd = set(
            spd1_df["time"].dt.hour.tolist()
            + spd2_df["time"].dt.hour.tolist()
        )

        sp_df = df[
            ~df["time"].dt.hour.isin(horas_spd)
        ]

        def stats(df_):

            if df_.empty:
                return CLIMA_DEFAULT.copy()

            return {
                "temp_min": round(df_["at"].min(), 2),
                "temp_max": round(df_["at"].max(), 2),
                "temp_prom": round(df_["at"].mean(), 2),
            }

        resultado["SPD1"].update(stats(spd1_df))
        resultado["SPD2"].update(stats(spd2_df))
        resultado["SP"].update(stats(sp_df))

    except requests.Timeout:
        console.print("[yellow]Timeout obteniendo clima[/yellow]")

    except requests.ConnectionError:
        console.print("[yellow]Sin conexión con proveedores climáticos[/yellow]")

    except requests.HTTPError as e:
        console.print(f"[yellow]HTTP Error clima: {e}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error obteniendo clima: {e}[/red]")
    
    return resultado

def clasificar_clima(temp_f):
    if temp_f > 78:
        return "Calor"
    elif temp_f >= 68 and temp_f <= 78:
        return "Templado"
    elif temp_f < 68:
        return "Frio"

# ==============================
# 🧠 EVALUADORES
# ==============================
def es_vacio(valor):

    return (
        valor is None
        or pd.isna(valor)
        or valor == 0
    )

def evaluar_estado(data: dict) -> str:
    """
    Estados:
    - Sin control GSE
    - TI Dañado
    - Apagado
    - No enfria
    - Ok
    """

    CtrlGSE = data.get("CtrlGSE")
    alerta_TI = data.get("AlertaTIdanado") or 0
    TIY1 = data.get("TIY1")
    TIY2 = data.get("TIY2")
    Y1 = data.get("Y1")
    TC = data.get("TC")
    TZ = data.get("TZ")
    tecnologia = data.get("Tecnología")

    # 1. Sin control GSE
    if not CtrlGSE:
        return "Sin control GSE"

    if ((es_vacio(TZ) and es_vacio(TIY1) and es_vacio(Y1)) or (es_vacio(TZ) and es_vacio(TIY2) and es_vacio(Y1))):
        return "Offline"

    # 2. TI Dañado
    if alerta_TI == 1 or (es_vacio(TIY1) and Y1 > 12):
        return "TI Dañado"
    
    # TI OFFILINE

    # 3. Apagado
    if tecnologia != "venstar":
        if (
            TC < 0.5
            and TIY1 > 65
            and alerta_TI == 0
        ):
            return "Apagado"
    else:
        if (
            TIY1 > 65
            and alerta_TI == 0
        ):
            return "Apagado"

    # 4. No enfria
    if (TC > 0.5 and TIY1 > 65 and alerta_TI == 0):
        return "No enfria"

    if tecnologia != "venstar":
        # 5. Ok
        if (TC > 0.5 and TIY1 <= 65 and alerta_TI == 0):
            return "Ok"
    else:
        # 6. Ok cuando TIY1 viene vacío
        if (es_vacio(TIY1) and Y1 <= 12):
            return "Ok"

    return "Ok"

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
    ti_offline = (data.get("TI Offline") or 0) > 0
    cambios_sp  = data.get("CambiosSP") or 0

    estatus = evaluar_estado(data)
    queja   = evaluar_queja(data)

    resultado = dict(prediccion)  # copia de la predicción normalizada
    SIN_AJUSTE = "Sin ajuste"
    motivo    = SIN_AJUSTE

    if ti_offline:
        motivo = f"{SIN_AJUSTE}: TI Offline"
        return {
            **resultado,
            "SP":    '',
            "SPD01": '',
            "SPD02": '',
            "BandaY1": '',
            "BandaY2": '',
            "motivo": motivo,
        }

    if estatus == "Sin control GSE":
        motivo = f"{SIN_AJUSTE}: Sin control GSE"
        return {
            **resultado,
            "SP":    '',
            "SPD01": '',
            "SPD02": '',
            "BandaY1": '',
            "BandaY2": '',
            "motivo": motivo,
        }
    
    if estatus == "TI Dañado":
        motivo = f"{SIN_AJUSTE}: TI Dañado"
        return {
            **resultado,
            "SP":    '',
            "SPD01": '',
            "SPD02": '',
            "BandaY1": '',
            "BandaY2": '',
            "motivo": motivo,
        }

    if estatus == "Apagado":
        motivo = f"{SIN_AJUSTE}: Apagado"
        return {
            **resultado,
            "SP":    '',
            "SPD01": '',
            "SPD02": '',
            "BandaY1": '',
            "BandaY2": '',
            "motivo": motivo,
        }

    if estatus == "Offline":
        motivo = f"{SIN_AJUSTE}: Offline"
        return {
            **resultado,
            "SP":    '',
            "SPD01": '',
            "SPD02": '',
            "BandaY1": '',
            "BandaY2": '',
            "motivo": motivo,
        }

    if cambios_sp >= 8:
        motivo = f"{SIN_AJUSTE}: CambiosSP={cambios_sp} ≥ 8 → sin ajuste automático"
        return {
            **resultado, 
            "SP":    '',
            "SPD01": '',
            "SPD02": '',
            "BandaY1": '',
            "BandaY2": '',
            "motivo": motivo, 
        }

    # Porcentajes de operación
    try:
        pct = calcular_porcentajes_operacion(data)
    except Exception:
        pct = {
            "SPD1": {"operacion_pct": 0},
            "SPD2": {"operacion_pct": 0},
            "SP": {"operacion_pct": 0, "temp_prom": 0},
        }
    
    climas = {
        "SP": {
            "temperatura": pct["SP"].get("temp_prom", 0),
            "clima": clasificar_clima(pct["SP"].get("temp_prom", 0))
        },
        "SPD1": {
            "temperatura": pct["SPD1"].get("temp_prom", 0),
            "clima": clasificar_clima(pct["SPD1"].get("temp_prom", 0))
        },
        "SPD2": {
            "temperatura": pct["SPD2"].get("temp_prom", 0),
            "clima": clasificar_clima(pct["SPD2"].get("temp_prom", 0))
        }
    }

    resultados_ia = {}

    for sensor, resultclima in climas.items():

        clima = resultclima["clima"]

        if clima == "Frio":
            resultados_ia[sensor] = {
                **resultado,
                "SP": "",
                "SPD01": "",
                "SPD02": "",
                "BandaY1": "",
                "BandaY2": "",
                "motivo": f"{SIN_AJUSTE}, clima: Frio → reglas aún no implementadas"
            }

        elif clima == "Calor":
            resultados_ia[sensor] = clima_calido(
                data=data,
                alerta_ti=alerta_ti,
                pct=pct,
                queja=queja,
                grupo=grupo,
                limite_alto=limite_alto,
                prediccion=prediccion,
                resultado=resultado,
                resultclima=resultclima
            )

        elif clima == "Templado":
            resultados_ia[sensor] = clima_templado(
                data=data,
                alerta_ti=alerta_ti,
                pct=pct,
                queja=queja,
                grupo=grupo,
                limite_alto=limite_alto,
                prediccion=prediccion,
                resultado=resultado,
                resultclima=resultclima
            )

    return {
        "resultados_ia": resultados_ia
    }
