import math
from ...api.openmateo import obtener_clima
from datetime import datetime, time
from rich.console import Console
import pandas as pd
import requests
import unicodedata
from .templado import clima_templado
from .calor import clima_calido
from .frio import clima_frio

def cargar_quejas_api() -> pd.DataFrame:
    URL = "https://an-5dd0c5c60d33470a8a883871ce404f2b.ecs.us-east-1.on.aws/ml/quejas"
    page = 1
    size = 500  # usa el máximo que permita la API
    registros = []

    while True:
        response = requests.get(
            URL,
            params={
                "page": page,
                "size": size
            },
            timeout=60
        )

        response.raise_for_status()

        payload = response.json()

        data = payload["data"]

        if not data:
            break

        registros.extend(data)

        total = payload["total"]
        total_pages = math.ceil(total / size)

        if page >= total_pages:
            break

        page += 1

    df = pd.DataFrame(registros)

    df = df.rename(columns={
        "fecha": "Fecha",
        "sucursal": "Sucursal",
        "ubicacion": "Ubicacion"
    })

    df["Fecha"] = pd.to_datetime(df["Fecha"])

    return df

df_quejas = cargar_quejas_api()

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
    "Mexico":           "Metro",
    "México":           "Metro",
    "mexico":           "Metro",
    "méxico":           "Metro",
}

def _grupo(region: str | None) -> str:
    """Normaliza la región al grupo correspondiente. Default: NL."""
    if not region:
        return "NL"
    return REGION_A_GRUPO.get(region.lower().strip(), "NL")

# ==============================
# 🕐 UTILIDADES HORARIAS
# ==============================
def _parse_hora(valor):

    if valor is None or pd.isna(valor):
        return None

    if isinstance(valor, time):
        return datetime.combine(datetime.today(), valor)

    valor = str(valor).strip()

    if valor == "":
        return None

    if len(valor) == 5:  # 08:00
        valor += ":00"

    try:
        return datetime.strptime(valor, "%H:%M:%S")
    except ValueError:
        return None


def _horas_entre(inicio, fin) -> float:

    inicio = _parse_hora(inicio)
    fin = _parse_hora(fin)

    if inicio is None or fin is None:
        return 0.0

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
    try:
        if pd.isna(valor):
            return None

        valor = float(valor)

        if abs(valor) > 1000:
            valor /= 1_000_000

        return valor

    except:
        return None

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

    if not pd.isna(lat):
        lat = normalizar_coord(lat)

    if not pd.isna(lon):
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

        def obtener_hora(valor, default=0):

            if valor is None:
                return default

            try:
                if pd.isna(valor):
                    return default
            except:
                pass

            if isinstance(valor, time):
                return valor.hour

            valor = str(valor).strip()

            if valor == "" or valor.lower() == "nan":
                return default

            try:
                return int(valor.split(":")[0])
            except (ValueError, TypeError):
                return default

        def filtrar_periodo(inicio, fin):

            h_ini = obtener_hora(inicio)
            h_fin = obtener_hora(fin)

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
    elif temp_f >= 68:
        return "Templado"
    else:
        return "Frio"

# ==============================
# 🧠 EVALUADORES
# ==============================
def es_vacio(valor):
    return (
        valor is None
        or pd.isna(valor)
        or (isinstance(valor, str) and valor.strip() == "")
    )

def num(valor):
    """Convierte a float o devuelve None."""
    return None if es_vacio(valor) else float(valor)

def evaluar_estado(data: dict) -> str:
    """
    Estados:
    - Sin control GSE
    - Offline
    - TI Offline
    - TI Dañado
    - Apagado
    - No enfria
    - Ok
    - No cumple
    """

    CtrlGSE = data.get("CtrlGSE")
    alerta_TI = int(data.get("AlertaTIdanado") or 0)
    TIY1 = num(data.get("TIY1"))
    TIY2 = num(data.get("TIY2"))
    Y1 = num(data.get("Y1"))
    TC = num(data.get("TC"))
    TZ = num(data.get("TZ"))
    tecnologia = (data.get("Tecnologia") or "").lower().strip()
    ti_offline = (data.get("TI Offline") or 0) > 0

    ti_alta = TIY1 is not None and TIY1 > 65
    tz_alta = TZ is not None and TZ > 75
    tc_apagado = TC is None or TC < 0.5

    # 1. Sin control GSE
    if not CtrlGSE:
        return "Sin control GSE"

    # 2. Offline
    if TZ is None and Y1 is None and (TIY1 is None or TIY2 is None):
        return "Offline"
    
    if tecnologia == "salus" and TIY1 is None and TC is None and Y1 is None:
        return "Offline"

    # 3. TI Offline
    if ti_offline:
        return "TI Offline"

    # 4. TI Dañado
    if alerta_TI == 1 or (TIY1 is None and Y1 is not None and Y1 > 12):
        return "TI Dañado"

    # 5. Apagado
    if tecnologia in ("plc", "salus") and ti_alta and tc_apagado:
        return "Apagado"

    if tecnologia == "venstar" and ti_alta and TC is not None and TC < 0.5:
        return "Apagado"

    if tecnologia == "sensibo" and tz_alta and ti_alta and tc_apagado: 
        return "Apagado"

    # 6. No enfria
    if tecnologia in ("plc", "salus") and ti_alta and not tc_apagado:
        return "No enfria"
    
    if (tecnologia == "sensibo" and tz_alta) and ((TIY1 is None) or (ti_alta and not tc_apagado)):
        return "No enfria"
    
    if tecnologia == "venstar" and ti_alta and ((TC is None and Y1 is not None and Y1 > 4) or (not tc_apagado)):
        return "No enfria"
    
    # 7. Ok
    if tecnologia in ("plc", "salus") and ((not ti_alta and not tc_apagado) or (not ti_alta and TC is None)):
        return "Ok"
    
    if tecnologia == "salus" and TIY1 is None and ((not tc_apagado and Y1 is None) or (TC is None and Y1 is not None and Y1 < 11)):
        return "Ok"

    if (tecnologia == "sensibo" and not tz_alta) and ((TIY1 is None) or (not ti_alta and not tc_apagado)):
        return "Ok"
    
    if (tecnologia == "sensibo" and not tc_apagado and (
        (tz_alta and not ti_alta )
        or (not tz_alta and ti_alta)
    )):
        return "Ok"
    
    if tecnologia == "venstar" and (
        (not ti_alta and not tc_apagado)
        or (TIY1 is None and TC is None and Y1 is not None and Y1 < 11)
        or (not ti_alta and TC is None and Y1 is None)
        or (not ti_alta and TC is None and Y1 is not None and Y1 > 4)
    ):
        return "Ok"

    return "No cumple"

def evaluar_queja(data: dict) -> str:
    sucursal = data.get("Sucursal")
    ubicacion = data.get("Ubicacion")

    fecha =data.get("Fecha")

    fecha = pd.to_datetime(fecha)

    fecha_inicio = fecha - pd.Timedelta(days=60)

    coincidencias = df_quejas[
        (df_quejas["Sucursal"] == sucursal) &
        (df_quejas["Ubicacion"] == ubicacion) &
        (df_quejas["Fecha"] >= fecha_inicio) &
        (df_quejas["Fecha"] <= fecha)
    ]
    
    return "Si" if not coincidencias.empty else "No"

# ==============================
# 🚀 FUNCIÓN PRINCIPAL
# ==============================
def _sin_ajuste(resultado, motivo):
    return {
        "resultados_ia": {
            "SP": {
                **resultado,
                "SP": "",
                "SPD01": "",
                "SPD02": "",
                "BandaY1": "",
                "BandaY2": "",
                "motivo": [motivo, motivo, motivo],
                "motivo_detallado": motivo
            },
            "SPD1": {
                **resultado,
                "SP": "",
                "SPD01": "",
                "SPD02": "",
                "BandaY1": "",
                "BandaY2": "",
                "motivo": [motivo, motivo, motivo],
                "motivo_detallado": motivo
            },
            "SPD2": {
                **resultado,
                "SP": "",
                "SPD01": "",
                "SPD02": "",
                "BandaY1": "",
                "BandaY2": "",
                "motivo": [motivo, motivo, motivo],
                "motivo_detallado": motivo
            }
        }
    }

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

    if estatus == "Sin control GSE":
        motivo = f"{SIN_AJUSTE}: Sin control GSE"
        return _sin_ajuste(
            resultado,
            motivo
        )
    
    if ti_offline:
        motivo = f"{SIN_AJUSTE}: TI Offline"
        return _sin_ajuste(
            resultado,
            motivo
        )

    
    if estatus == "TI Dañado":
        motivo = f"{SIN_AJUSTE}: TI Dañado"
        return _sin_ajuste(
            resultado,
            motivo
        )

    if estatus == "Apagado":
        motivo = f"{SIN_AJUSTE}: Apagado"
        return _sin_ajuste(
            resultado,
            motivo
        )

    if estatus == "Offline":
        motivo = f"{SIN_AJUSTE}: Offline"
        return _sin_ajuste(
            resultado,
            motivo
        )

    if cambios_sp >= 8:
        motivo = f"{SIN_AJUSTE}: CambiosSP > 8"
        return _sin_ajuste(
            resultado,
            motivo
        )

    # Porcentajes de operación
    try:
        pct = calcular_porcentajes_operacion(data)
    except Exception as e:
        print("ERROR calcular_porcentajes_operacion:", e)
        raise
    
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
            resultados_ia[sensor] = clima_frio(
                data=data,
                alerta_ti=alerta_ti,
                pct=pct,
                queja=queja,
                grupo=grupo,
                limite_alto=limite_alto,
                prediccion=prediccion,
                resultado=resultado,
                resultclima=resultclima,
                estatus=estatus
            )

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
                resultclima=resultclima,
                estatus=estatus
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
                resultclima=resultclima,
                estatus=estatus
            )
    
    for _, resultado_sensor in resultados_ia.items():

        clima = climas["SP"]["clima"]

        # CALOR
        if clima == "Calor":
            resultado_sensor["BandaY1"] = 1
            resultado_sensor["BandaY2"] = 1

        # FRÍO
        elif clima == "Frio":
            resultado_sensor["BandaY1"] = 2
            resultado_sensor["BandaY2"] = 12

        # TEMPLADO
        elif clima == "Templado":

            if estatus == "Ok":
                resultado_sensor["BandaY1"] = 1
                resultado_sensor["BandaY2"] = 3

            elif estatus == "No enfria":

                banday2 = data.get("BandaY2")

                if pd.isna(banday2):
                    banday2 = 1
                else:
                    banday2 = min(int(float(banday2)) + 1, 5)

                resultado_sensor["BandaY1"] = 1
                resultado_sensor["BandaY2"] = banday2

    return {
        "resultados_ia": resultados_ia
    }
