import math
from ...api.openmateo import obtener_clima
from datetime import datetime, time
from pathlib import Path
from rich.console import Console
import pandas as pd
import requests
import unicodedata
from .templado import clima_templado
from .calor import clima_calido
from .frio import clima_frio
from ...database.dbPosgres import get_connection

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
# 📦 HISTÓRICO HVAC
# ==============================
HISTORICO_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "hvac_historico.parquet"
)

_HVAC_HISTORICO = None

def cargar_historico_hvac():

    global _HVAC_HISTORICO

    if _HVAC_HISTORICO is not None:
        return _HVAC_HISTORICO

    if not HISTORICO_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró histórico HVAC: {HISTORICO_PATH}"
        )

    df = pd.read_parquet(HISTORICO_PATH)

    df["Fecha"] = pd.to_datetime(
        df["Fecha"],
        errors="coerce"
    )

    df["_ubicacion_norm"] = (
        df["Ubicación"]
        .fillna("")
        .map(lambda x: normalizar_estado(str(x)))
    )

    df["_tipo_norm"] = (
        df["Tipo de HVAC"]
        .fillna("")
        .map(lambda x: normalizar_estado(str(x)))
    )

    df["_region_norm"] = (
        df["Region"]
        .fillna("")
        .map(lambda x: normalizar_estado(str(x)))
    )   

    df["_mes"] = df["Fecha"].dt.month

    # Coordenadas numéricas para búsqueda de tiendas cercanas
    df["_lat"] = pd.to_numeric(
        df["Latitud"],
        errors="coerce"
    )

    df["_lon"] = pd.to_numeric(
        df["Longitud"],
        errors="coerce"
    )

    # Algunas coordenadas pueden venir multiplicadas
    df.loc[df["_lat"].abs() > 1000, "_lat"] /= 1_000_000
    df.loc[df["_lon"].abs() > 1000, "_lon"] /= 1_000_000
    
    _HVAC_HISTORICO = df

    return _HVAC_HISTORICO

def clima_valido(clima):

    if not isinstance(clima, dict):
        return False

    hourly = clima.get("hourly")

    if not isinstance(hourly, dict):
        return False

    tiempos = hourly.get("time")
    temperaturas = hourly.get("apparent_temperature")

    if tiempos is None or temperaturas is None:
        return False

    if len(tiempos) == 0 or len(temperaturas) == 0:
        return False

    if len(tiempos) != len(temperaturas):
        return False

    temperaturas_validas = pd.to_numeric(
        pd.Series(temperaturas),
        errors="coerce"
    )

    if temperaturas_validas.notna().sum() == 0:
        return False

    return True

def distancia_km(lat1, lon1, lat2, lon2):
    """
    Distancia aproximada entre dos coordenadas
    usando la fórmula de Haversine.
    """

    try:
        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)
    except (TypeError, ValueError):
        return float("inf")

    radio_tierra = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radio_tierra * c

def obtener_clima_parquet(data: dict):


    historico = cargar_historico_hvac()

    # =========================
    # IDENTIFICAR REGISTRO
    # =========================
    idvbox = data.get("Idvbox")

    if idvbox is None:
        idvbox = data.get("idVbox")

    ubicacion = (
        data.get("Ubicacion")
        or data.get("Ubicación")
        or ""
    )

    tipo_hvac = data.get("Tipo de HVAC") or ""
    region = data.get("Region") or ""

    fecha = pd.to_datetime(
        data.get("Fecha"),
        errors="coerce"
    )

    if pd.isna(fecha):
        fecha = pd.Timestamp.today()

    mes = fecha.month

    # =========================
    # NORMALIZAR TEXTO
    # =========================

    ubicacion_norm = normalizar_estado(ubicacion)
    tipo_norm = normalizar_estado(tipo_hvac)
    region_norm = normalizar_estado(region)

    # Creamos columnas temporales normalizadas
    h = historico

    # =========================
    # SELECCIÓN DEL HISTÓRICO
    # =========================

    lat = normalizar_coord(data.get("Latitud"))
    lon = normalizar_coord(data.get("Longitud"))

    muestra_base = pd.DataFrame()
    origen_historico = "sin_datos"

    # =====================================================
    # 1. PRIORIDAD: TIENDAS CERCANAS POR LATITUD / LONGITUD
    # =====================================================
    if lat is not None and lon is not None:

        cercanos = h[
            h["_lat"].notna()
            & h["_lon"].notna()
            & (h["_tipo_norm"] == tipo_norm)
        ].copy()

        if not cercanos.empty:

            cercanos["_distancia_km"] = cercanos.apply(
                lambda fila: distancia_km(
                    lat,
                    lon,
                    fila["_lat"],
                    fila["_lon"]
                ),
                axis=1
            )

            # Evitamos usar exactamente la misma ubicación
            # como único punto de referencia.
            cercanos = cercanos[
                cercanos["_distancia_km"] > 0.05
            ]

            # Primero buscamos dentro de 25 km
            vecinos_25 = cercanos[
                cercanos["_distancia_km"] <= 25
            ].sort_values("_distancia_km")

            if len(vecinos_25) >= 5:
                muestra_base = vecinos_25
                origen_historico = "tiendas_cercanas_25km"

            else:
                # Si no hay suficientes, ampliamos a 50 km
                vecinos_50 = cercanos[
                    cercanos["_distancia_km"] <= 50
                ].sort_values("_distancia_km")

                if len(vecinos_50) >= 5:
                    muestra_base = vecinos_50
                    origen_historico = "tiendas_cercanas_50km"


    # =====================================================
    # 2. FALLBACK: MISMO EQUIPO FÍSICO
    # =====================================================
    if muestra_base.empty:

        mismo_equipo = h[
            (h["Idvbox"] == idvbox)
            & (h["_ubicacion_norm"] == ubicacion_norm)
            & (h["_tipo_norm"] == tipo_norm)
        ]

        if not mismo_equipo.empty:
            muestra_base = mismo_equipo
            origen_historico = "equipo"


    # =====================================================
    # 3. FALLBACK: MISMA REGIÓN + TIPO HVAC
    # =====================================================
    if muestra_base.empty:

        regional = h[
            (h["_region_norm"] == region_norm)
            & (h["_tipo_norm"] == tipo_norm)
        ]

        if not regional.empty:
            muestra_base = regional
            origen_historico = "region_tipo"


    # =====================================================
    # 4. ÚLTIMO FALLBACK: MISMO TIPO HVAC
    # =====================================================
    if muestra_base.empty:

        muestra_base = h[
            h["_tipo_norm"] == tipo_norm
        ]

        origen_historico = "tipo_hvac"


    # =====================================================
    # PRIORIZAR MISMO MES
    # =====================================================
    mismo_mes = muestra_base[
        muestra_base["_mes"] == mes
    ]

    if len(mismo_mes) >= 5:
        muestra = mismo_mes
    else:
        muestra = muestra_base


    # Referencia usada después para percentiles
    mismo_equipo = muestra_base

    # =========================
    # VARIABLES HVAC
    # =========================
    y1_hist = pd.to_numeric(
        muestra["Y1"],
        errors="coerce"
    ).dropna()

    tc_hist = pd.to_numeric(
        muestra["TC"],
        errors="coerce"
    ).dropna()

    # Predicción histórica robusta:
    # utilizamos mediana para evitar outliers.
    y1_estimado = (
        y1_hist.median()
        if not y1_hist.empty
        else None
    )

    tc_estimado = (
        tc_hist.median()
        if not tc_hist.empty
        else None
    )

    # =========================
    # REFERENCIA HISTÓRICA
    # =========================
    y1_ref = pd.to_numeric(
        mismo_equipo["Y1"],
        errors="coerce"
    ).dropna()

    tc_ref = pd.to_numeric(
        mismo_equipo["TC"],
        errors="coerce"
    ).dropna()

    percentiles = []

    if (
        y1_estimado is not None
        and not y1_ref.empty
    ):
        percentil_y1 = (
            y1_ref <= y1_estimado
        ).mean()

        percentiles.append(percentil_y1)

    if (
        tc_estimado is not None
        and not tc_ref.empty
    ):
        percentil_tc = (
            tc_ref <= tc_estimado
        ).mean()

        percentiles.append(percentil_tc)

    # =========================
    # NIVEL TÉRMICO
    # =========================
    if percentiles:

        indice_termico = sum(percentiles) / len(percentiles)

    else:

        # Caso extremo:
        # no existe información histórica utilizable.
        indice_termico = 0.5

    # =========================
    # TEMPERATURA CONTINUA
    # =========================

    # En lugar de asignar únicamente
    # 65, 73 u 82 °F, interpolamos
    # una temperatura según el índice.

    if indice_termico < 0.33:

        categoria = "Frio"

        temperatura = (
            62
            + (indice_termico / 0.33) * 6
        )

    elif indice_termico <= 0.67:
    
        categoria = "Templado"

        temperatura = (
            68
            + ((indice_termico - 0.33) / 0.34) * 10
        )

    else:
    
        categoria = "Calor"

        temperatura = (
        78
            + ((indice_termico - 0.67) / 0.33) * 8
        )

    temperatura = round(
        float(temperatura),
        2
    )

    # =========================
    # CREAR PERFIL HORARIO
    # =========================

    fecha_inicio = fecha.normalize()

    tiempos = pd.date_range(
        start=fecha_inicio,
        periods=48,
        freq="h"
    )

    temperaturas = []

    for t in tiempos:

        hora = t.hour

        # SPD1: madrugada
        if 0 <= hora <= 6:
            ajuste = -4.0

        # transición mañana
        elif 7 <= hora <= 10:
            ajuste = -1.0

        # SP: periodo más cálido
        elif 11 <= hora <= 17:
            ajuste = 3.0

        # transición tarde
        elif 18 <= hora <= 20:
            ajuste = 1.0

        # SPD2: noche
        else:
            ajuste = -2.0

        temperaturas.append(
            round(temperatura + ajuste, 2)
        )

    # =========================
    # ESTRUCTURA COMPATIBLE
    # =========================
    clima = {
        "hourly": {
            "time": [
                t.strftime("%Y-%m-%d %H:%M:%S")
                for t in tiempos
            ],
            "apparent_temperature": temperaturas
        },

        "_origen": "historico_hvac",

        "_detalle_historico": {
            "nivel": origen_historico,
            "categoria": categoria,
            "indice_termico": round(
                float(indice_termico),
                3
            ),
            "y1_estimado": (
                round(float(y1_estimado), 2)
                if y1_estimado is not None
                else None
            ),
            "tc_estimado": (
                round(float(tc_estimado), 2)
                if tc_estimado is not None
                else None
            ),
            "registros_utilizados": len(muestra)
        }
    }

    return clima

def obtener_clima_historico(data: dict):

    lat = normalizar_coord(data.get("Latitud"))
    lon = normalizar_coord(data.get("Longitud"))

    # Sin coordenadas no podemos buscar tiendas cercanas
    if lat is None or lon is None:
        return obtener_clima_parquet(data)

    conn = None

    try:
        conn = get_connection()

        query = """
            SELECT
                sucursal,
                ubicacion,
                tecnologia,
                estado,
                ciudad,
                latitud,
                longitud,
                tipo_hvac,
                temp_prom_sp,
                temp_prom_spd1,
                temp_prom_spd2
            FROM public.estrategias
            WHERE latitud IS NOT NULL
              AND longitud IS NOT NULL
              AND temp_prom_sp IS NOT NULL
              AND temp_prom_spd1 IS NOT NULL
              AND temp_prom_spd2 IS NOT NULL
              AND fecha >= CURRENT_DATE - INTERVAL '60 days'
        """

        vecinos = pd.read_sql_query(
            query,
            conn
        )

    except Exception as e:

        console.print(
            f"[yellow]No se pudo consultar tiendas cercanas "
            f"({e}), utilizando parquet...[/yellow]"
        )

        return obtener_clima_parquet(data)

    finally:
        if conn is not None:
            conn.close()

    if vecinos.empty:
        return obtener_clima_parquet(data)

    # Coordenadas válidas
    vecinos["_lat"] = vecinos["latitud"].map(
        normalizar_coord
    )

    vecinos["_lon"] = vecinos["longitud"].map(
        normalizar_coord
    )

    vecinos = vecinos[
        vecinos["_lat"].notna()
        & vecinos["_lon"].notna()
    ].copy()

    if vecinos.empty:
        return obtener_clima_parquet(data)

    # Calcular distancia contra la tienda actual
    vecinos["_distancia_km"] = vecinos.apply(
        lambda fila: distancia_km(
            lat,
            lon,
            fila["_lat"],
            fila["_lon"]
        ),
        axis=1
    )

    # No usar exactamente la misma tienda
    vecinos = vecinos[
        vecinos["_distancia_km"] > 0.05
    ]

    # Primero buscar en 25 km
    cercanos = vecinos[
        vecinos["_distancia_km"] <= 25
    ].copy()

    radio = 25

    # Si no hay suficientes, ampliar a 50 km
    if len(cercanos) < 3:

        cercanos = vecinos[
            vecinos["_distancia_km"] <= 50
        ].copy()

        radio = 50

    # Si tampoco hay suficientes,
    # utilizar el parquet
    if len(cercanos) < 3:
        return obtener_clima_parquet(data)

    # Una sola referencia por tienda/ubicación
    cercanos = (
        cercanos
        .sort_values("_distancia_km")
        .drop_duplicates(
            subset=[
                "sucursal",
                "ubicacion"
            ]
        )
        .head(20)
    )

    if len(cercanos) < 3:
        return obtener_clima_parquet(data)

    # Temperaturas reales de tiendas cercanas
    temp_sp = pd.to_numeric(
        cercanos["temp_prom_sp"],
        errors="coerce"
    ).median()

    temp_spd1 = pd.to_numeric(
        cercanos["temp_prom_spd1"],
        errors="coerce"
    ).median()

    temp_spd2 = pd.to_numeric(
        cercanos["temp_prom_spd2"],
        errors="coerce"
    ).median()

    if (
        pd.isna(temp_sp)
        or pd.isna(temp_spd1)
        or pd.isna(temp_spd2)
    ):
        return obtener_clima_parquet(data)

    # SP debe ser el periodo más alto
    temp_sp = max(
        temp_sp,
        temp_spd1,
        temp_spd2
    )

    fecha = pd.to_datetime(
        data.get("Fecha"),
        errors="coerce"
    )

    if pd.isna(fecha):
        fecha = pd.Timestamp.today()

    tiempos = pd.date_range(
        start=fecha.normalize(),
        periods=48,
        freq="h"
    )

    temperaturas = []

    for t in tiempos:

        hora = t.hour

        # SPD1
        if 0 <= hora <= 6:
            temp = temp_spd1

        # SPD2
        elif 20 <= hora <= 23:
            temp = temp_spd2

        # SP
        else:
            temp = temp_sp

        temperaturas.append(
            round(float(temp), 2)
        )

    return {
        "hourly": {
            "time": [
                t.strftime("%Y-%m-%d %H:%M:%S")
                for t in tiempos
            ],
            "apparent_temperature": temperaturas
        },

        "_origen": "historico_hvac",

        "_detalle_historico": {
            "nivel": f"tiendas_cercanas_{radio}km",
            "tiendas_utilizadas": len(cercanos),
            "temp_sp": round(float(temp_sp), 2),
            "temp_spd1": round(float(temp_spd1), 2),
            "temp_spd2": round(float(temp_spd2), 2)
        }
    }

# ==============================
# 🗺️ MAPEO REGIÓN → GRUPO
# ==============================
REGION_A_GRUPO = {
    ("COAHUILA", "SALTILLO"): "NL",
    ("TAMAULIPAS", "REYNOSA"): "NL",
    ("COAHUILA", "TORREON"): "NL",
    ("COAHUILA", "RAMOS ARIZPE"): "NL",
    ("TAMAULIPAS", "MATAMOROS"): "NL",
    ("NUEVO LEÓN", "MONTERREY"): "NL",
    ("NUEVO LEÓN", "GENERAL ZUAZUA"): "NL",
    ("NUEVO LEÓN", "APODACA"): "NL",
    ("NUEVO LEÓN", "GUADALUPE"): "NL",
    ("NUEVO LEÓN", "SANTA CATARINA"): "NL",
    ("NUEVO LEÓN", "SAN PEDRO GARZA GARCIA"): "NL",
    ("NUEVO LEÓN", "GENERAL ESCOBEDO"): "NL",
    ("NUEVO LEÓN", "ALLENDE"): "NL",
    ("NUEVO LEÓN", "SAN NICOLAS DE LOS GARZA"): "NL",
    ("NUEVO LEÓN", "JUAREZ"): "NL",
    ("NUEVO LEÓN", "SANTIAGO"): "NL",
    ("NUEVO LEÓN", "CADEREYTA JIMENEZ"): "NL",
    ("NUEVO LEÓN", "PESQUERIA"): "NL",
    ("NUEVO LEÓN", "MONTEMORELOS"): "NL",
    ("NUEVO LEÓN", "GARCIA"): "NL",
    ("NUEVO LEÓN", "CIENEGA DE FLORES"): "NL",
    ("NUEVO LEÓN", "CARMEN"): "NL",
    ("NUEVO LEÓN", "SALINAS VICTORIA"): "NL",
    ("JALISCO", "TLAQUEPAQUE"): "NL",
    ("JALISCO", "GUADALAJARA"): "NL",
    ("JALISCO", "ZAPOPAN"): "NL",
    ("JALISCO", "TLAJOMULCO DE ZUÑIGA"): "NL",
    ("JALISCO", "EL SALTO"): "NL",
    ("BAJA CALIFORNIA", "MEXICALI"): "NL",
    ("SONORA", "HERMOSILLO"): "NL",

    ("YUCATÁN", "KANASIN"): "Sureste",
    ("QUINTANA ROO", "BENITO JUAREZ"): "Sureste",
    ("YUCATÁN", "MERIDA"): "Sureste",
    ("QUINTANA ROO", "TULUM"): "Sureste",
    ("QUINTANA ROO", "SOLIDARIDAD"): "Sureste",
    ("QUINTANA ROO", "PUERTO MORELOS"): "Sureste",
    ("YUCATÁN", "SEYE"): "Sureste",
    ("YUCATÁN", "CONKAL"): "Sureste",
    ("QUINTANA ROO", "COZUMEL"): "Sureste",

    ("BAJA CALIFORNIA", "TIJUANA"): "BC",
    ("BAJA CALIFORNIA", "PLAYAS DE ROSARITO"): "BC",
    ("BAJA CALIFORNIA", "ENSENADA"): "BC",

    ("CIUDAD DE MÉXICO", "BENITO JUAREZ"): "Metro",
    ("CIUDAD DE MÉXICO", "CUAUHTEMOC"): "Metro",
    ("CIUDAD DE MÉXICO", "LA MAGDALENA CONTRERAS"): "Metro",
    ("CIUDAD DE MÉXICO", "COYOACAN"): "Metro",
    ("CIUDAD DE MÉXICO", "MIGUEL HIDALGO"): "Metro",
    ("CIUDAD DE MÉXICO", "ALVARO OBREGON"): "Metro",
    ("CIUDAD DE MÉXICO", "TLALPAN"): "Metro",
    ("MÉXICO", "ATIZAPAN DE ZARAGOZA"): "Metro",
    ("CIUDAD DE MÉXICO", "IZTAPALAPA"): "Metro",
    ("CIUDAD DE MÉXICO", "AZCAPOTZALCO"): "Metro",
    ("PUEBLA", "SAN ANDRES CHOLULA"): "Metro",
    ("CIUDAD DE MÉXICO", "CUAJIMALPA DE MORELOS"): "Metro",
    ("MÉXICO", "TOLUCA"): "Metro",
    ("MORELOS", "TEMIXCO"): "Metro",
    ("CIUDAD DE MÉXICO", "VENUSTIANO CARRANZA"): "Metro",
    ("PUEBLA", "CORONANGO"): "Metro",
    ("MÉXICO", "CALIMAYA"): "Metro",
    ("MÉXICO", "SAN MATEO ATENCO"): "Metro",
    ("MÉXICO", "NAUCALPAN DE JUAREZ"): "Metro",
    ("MORELOS", "XOCHITEPEC"): "Metro",
    ("PUEBLA", "PUEBLA"): "Metro",
    ("MORELOS", "CUERNAVACA"): "Metro",
    ("CIUDAD DE MÉXICO", "XOCHIMILCO"): "Metro",
    ("MÉXICO", "HUIXQUILUCAN"): "Metro",
    ("PUEBLA", "SAN PEDRO CHOLULA"): "Metro",
    ("MÉXICO", "COACALCO DE BERRIOZABAL"): "Metro",
    ("MÉXICO", "LERMA"): "Metro",
    ("MÉXICO", "METEPEC"): "Metro",
    ("CIUDAD DE MÉXICO", "IZTACALCO"): "Metro",
    ("CIUDAD DE MÉXICO", "GUSTAVO A MADERO"): "Metro",
    ("MÉXICO", "TLALNEPANTLA DE BAZ"): "Metro",
    ("MÉXICO", "CUAUTITLAN IZCALLI"): "Metro",
    ("MÉXICO", "ECATEPEC DE MORELOS"): "Metro",
    ("MÉXICO", "TULTITLAN"): "Metro",
}

def _grupo(estado: str | None, ciudad: str | None) -> str:
    """Normaliza la región al grupo correspondiente. Default: NL."""
    if not estado or not ciudad:
        return "NL"
    
    return REGION_A_GRUPO.get((estado.strip().upper(), ciudad.strip().upper()))

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

            clima = obtener_clima(
                lat,
                lon,
                provider="openmeteo"
            )

            if not clima_valido(clima):
                raise ValueError(
                    "Respuesta inválida o vacía de Open-Meteo"
                )

            clima["_origen"] = "openmeteo"

        except Exception as e:

            console.print(
                f"[yellow]Open-Meteo falló ({e}), "
                f"intentando WeatherAPI...[/yellow]"
            )
            # =========================
            # SEGUNDO INTENTO: WEATHERAPI
            # =========================
            try:

                clima = obtener_clima(
                    lat,
                    lon,
                    provider="weatherapi"
                )

                if not clima_valido(clima):
                    raise ValueError(
                        "Respuesta inválida o vacía de WeatherAPI"
                    )

                clima["_origen"] = "weatherapi"

            except Exception as e:

                console.print(
                    f"[yellow]WeatherAPI falló ({e}), "
                    f"utilizando histórico HVAC...[/yellow]"
                )

                # =========================
                # TERCER INTENTO:
                # HISTÓRICO HVAC
                # =========================
                clima = obtener_clima_historico(data)

                if not clima_valido(clima):
                    raise ValueError(
                        "No fue posible generar clima histórico válido"
                    )
                
        resultado["origen_clima"] = clima.get(
            "_origen",
            "Parquet"
        )

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

    grupo       = _grupo(data.get("Estado"), data.get("Ciudad"))

    limite_alto = bool(data.get("limite_sp_alto", True))
    alerta_ti   = (data.get("AlertaTIdanado") or 0) > 0
    ti_offline = (data.get("TI Offline") or 0) > 0
    cambios_sp  = data.get("CambiosSP") or 0

    estatus = evaluar_estado(data)
    queja   = evaluar_queja(data)

    resultado = dict(prediccion)  # copia de la predicción normalizada
    SIN_AJUSTE = "Sin cambios"
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
