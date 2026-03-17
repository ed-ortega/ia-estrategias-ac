import pandas as pd
from .mapsca import temporada_map, tipo_clima_map, area_map

# ----------------------------------
# UTILIDADES
# ----------------------------------

def time_to_minutes(t):

    if t is None:
        return None

    t = str(t).strip().lower()

    if "inicio venta" in t:
        return None

    try:
        h, m = map(int, t.split(":"))
        return h * 60 + m
    except:
        return None


def minutes_to_time(m):

    if m is None:
        return None

    h = int(m // 60)
    m = int(m % 60)

    return f"{h:02d}:{m:02d}"


# ----------------------------------
# PARSE TEMPERATURA
# ----------------------------------

def parse_temp_range(rule):

    if rule is None:
        return (-10, 50)

    rule = str(rule).strip()

    if "<" in rule:
        v = float(rule.replace("<", ""))
        return (-10, v)

    if ">" in rule:
        v = float(rule.replace(">", ""))
        return (v, 50)

    try:
        v = float(rule)
        return (v, v)
    except:
        return (-10, 50)


# ----------------------------------
# CONVERTIR REGLAS → DATASET
# ----------------------------------

def reglas_to_dataset(reglas):

    rows = []

    for r in reglas:

        temp_min, temp_max = parse_temp_range(r.temperatura_exterior)

        spd1_inicio = time_to_minutes(r.spd1_inicio)
        spd1_fin = time_to_minutes(r.spd1_fin)

        spd2_inicio = time_to_minutes(r.spd2_inicio)
        spd2_fin = time_to_minutes(r.spd2_fin)

        row = {

            "temporada": temporada_map().get(r.temporada),
            "tipo_clima": tipo_clima_map().get(r.tipo_clima),
            "area": area_map().get(r.area),

            "temp_min": temp_min,
            "temp_max": temp_max,

            "spd1_inicio": spd1_inicio,
            "spd1_fin": spd1_fin,

            "spd2_inicio": spd2_inicio,
            "spd2_fin": spd2_fin,

            # flags de evento
            "spd1_fin_evento": 1 if spd1_fin is None else 0,
            "spd2_fin_evento": 1 if spd2_fin is None else 0
        }

        # duración spd1
        if spd1_inicio is not None and spd1_fin is not None:
            row["spd1_duracion"] = spd1_fin - spd1_inicio
        else:
            row["spd1_duracion"] = None

        # duración spd2
        if spd2_inicio is not None and spd2_fin is not None:
            row["spd2_duracion"] = spd2_fin - spd2_inicio
        else:
            row["spd2_duracion"] = None

        rows.append(row)

    df = pd.DataFrame(rows)

    return df


