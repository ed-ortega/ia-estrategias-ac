from datetime import timedelta, datetime
import numpy as np
import pandas as pd
from ...api.openmateo import cargar_temperatura
#from ...api.meteostat_api import cargar_temperatura

def dividir_en_bloques(inicio, fin, dias=7):
    bloques = []
    actual = inicio
    while actual <= fin:
        fin_bloque = min(actual + timedelta(days=dias - 1), fin)
        bloques.append((actual, fin_bloque))
        actual = fin_bloque + timedelta(days=1)
    return bloques

def tiene_decimales(x: float) -> bool:
    return not x.is_integer()

def procesar(gse, cliente_id, region, inicio, fin):
    idRegion = region["idRegion"]
    nombre = region["nombre"]
    print(inicio, fin)
    try:
        data = gse.hvac_valores(
            cliente_id,
            inicio.strftime("%Y-%m-%d"),
            fin.strftime("%Y-%m-%d"),
            idRegion
        )
    except Exception as e:
        print(f"💥 Error API - [{datetime.now().strftime('%H:%M:%S')}] - ({nombre}): {e}")
        return []
    if not data:
        print(f"⚠️ Sin datos → {nombre}")
        return []

    registros = []
    
    for e in data:
        if str(e.get("Tecnología", "")).lower() == "sensibo":
            continue

        sp, spd01, spd03 = e.get("SP"), e.get("SPD01"), e.get("SPD03")

        if spd01 is not None and spd03 is not None:
            irregular = spd01 <= spd03
        else:
            irregular = False

        SP_decimal = tiene_decimales(sp) if sp is not None else False
        SPD_03_decimal = tiene_decimales(spd03) if spd03 is not None else False

        registro = {
            "Idvbox": e.get("idVbox"),
            "CC": e.get("CC"),
            "Sucursal": e.get("Sucursal"),
            "Ubicación": e.get("Ubicacion"),
            "Tecnología": e.get("Tecnologia"),
            "Fecha": e.get("Fecha"),
            "Region": nombre,
            "Estado": e.get("Estado"),
            "Latitud": e.get("Latitud"),
            "Longitud": e.get("Longitud"),
            "Tipo de HVAC": e.get("Tipo de HVAC"),
            "TZ": e.get("TZ"),
            "TIY1": e.get("TIY1"),
            "TIY2": e.get("TIY2"),
            "Y1": e.get("Y1"),
            "Y2": e.get("Y2"),
            "BandaY1": e.get("BandaY1"),
            "BandaY2": e.get("BandaY2"),
            "SP": e.get("SP"),
            "SPD01": e.get("SPD01"),
            "SPD02": e.get("SPD02"),
            "SPD03": e.get("SPD03"),
            "horario_inicio_SPD_01": e.get("horario_inicio_SPD_01"),
            "horario_fin_SPD_01": e.get("horario_fin_SPD_01"),
            "horario_inicio_SPD_02": e.get("horario_inicio_SPD_02"),
            "horario_fin_SPD_02": e.get("horario_fin_SPD_02"),
            "irregular": irregular,
            "SP_decimal": SP_decimal,
            "SPD03_decimal": SPD_03_decimal
        }

        registros.append(registro)

    registros = cargar_temperatura(registros)

    return registros

def hora_a_ciclico(h):
    if pd.isna(h) or h == 0:
        return 0, 0
    
    try:
        hh, mm = map(int, str(h).split(":"))
        minutos = hh * 60 + mm
        angulo = 2 * np.pi * minutos / 1440
        
        return np.sin(angulo), np.cos(angulo)
    except:
        return 0, 0