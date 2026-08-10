# frio.py
import math
import re

SIN_AJUSTE = "Sin ajuste"

RANGOS: dict[str, dict[bool, dict[str, tuple[int, int]]]] = {
    "NL": {
        True:  {"SP": (71, 74), "SPD01": (71, 77), "SPD02": (71, 76)},
        False: {"SP": (71, 74), "SPD01": (71, 77), "SPD02": (71, 76)},
    },
    "Sureste": {
        True:  {"SP": (70, 73), "SPD01": (71, 77), "SPD02": (71, 75)},
        False: {"SP": (70, 73), "SPD01": (71, 77), "SPD02": (71, 75)},
    },
    "BC": {
        True:  {"SP": (70, 74), "SPD01": (71, 77), "SPD02": (71, 76)},
        False: {"SP": (70, 74), "SPD01": (71, 77), "SPD02": (71, 76)},
    },
    "Metro": {
        True:  {"SP": (70, 74), "SPD01": (71, 77), "SPD02": (71, 76)},
        False: {"SP": (70, 74), "SPD01": (71, 77), "SPD02": (71, 76)},
    },
}

_DATA_KEY = {
    "SP":    "TZ SP",
    "SPD01": "TZ SPD 01",
    "SPD02": "TZ SPD 02",
}

REGLAS_FRIO = {}

def _cond_and(*conds):
    return lambda ctx: all(c(ctx) for c in conds)

def _pct_cmp(ctx, op, val):
    pct = ctx.get('pct')
    if pct is None:
        return False
    if op == '>':
        return pct > val
    elif op == '<':
        return pct < val
    elif op == '>=':
        return pct >= val
    elif op == '<=':
        return pct <= val
    elif op == 'range':
        lo, hi = val
        return lo <= pct <= hi
    return False

# ---------- REGIÓN NL ----------
REGLAS_FRIO["NL"] = {"SP": [], "SPD01": [], "SPD02": []}

REGLAS_FRIO["NL"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 60)), (None, None, "Norte-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 60)), ("zt_sp", +1.0, "Norte-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (15, 60))), (None, None, "Norte-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 15)), ("zt_sp", -0.5, "Norte-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 50)), (None, None, "Norte-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 50)), (None, None, "Norte-No enfria2")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (15, 50))), (None, None, "Norte-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 15)), ("zt_sp", -1.0, "Norte-No enfria4")),
])
REGLAS_FRIO["NL"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 40)), ("zt_spd01", +1.0, "Norte-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 40)), ("zt_spd01", +1.5, "Norte-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (5, 40))), (None, None, "Norte-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 5)), ("zt_spd01", -0.5, "Norte-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd01", +1.0, "Norte-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd01", +1.0, "Norte-No enfria2")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (5, 30))), (None, None, "Norte-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 5)), ("zt_spd01", -0.5, "Norte-No enfria4")),
])
REGLAS_FRIO["NL"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 45)), ("zt_spd02", +0.5, "Norte-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 45)), ("zt_spd02", +1.0, "Norte-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (10, 45))), (None, None, "Norte-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 10)), ("zt_spd02", -0.5, "Norte-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 35)), ("zt_spd02", +1.0, "Norte-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 35)), ("zt_spd02", +2.0, "Norte-No enfria2")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (10, 35))), (None, None, "Norte-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 10)), ("zt_spd02", -0.5, "Norte-No enfria4")),
])

# ---------- REGIÓN SURESTE ----------
REGLAS_FRIO["Sureste"] = {"SP": [], "SPD01": [], "SPD02": []}
REGLAS_FRIO["Sureste"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 65)), (None, None, "Sureste-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 65)), ("zt_sp", +0.5, "Sureste-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (15, 65))), (None, None, "Sureste-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 15)), ("zt_sp", -1.0, "Sureste-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 50)), (None, None, "Sureste-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 50)), (None, None, "Sureste-No enfria2")),
    (_cond_and(lambda c: c['estatus'] == "No enfria", lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (15, 50))), (None, None, "Sureste-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 15)), ("zt_sp", -1.0, "Sureste-No enfria4")),
])
REGLAS_FRIO["Sureste"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd01", +1.0, "Sureste-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd01", +1.0, "Sureste-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (5, 50))), (None, None, "Sureste-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 5)), ("zt_spd01", -0.5, "Sureste-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd01", +1.0, "Sureste-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd01", +1.0, "Sureste-No enfria2")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (5, 30))), (None, None, "Sureste-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 5)), ("zt_spd01", -0.5, "Sureste-No enfria4")),
])
REGLAS_FRIO["Sureste"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 55)), ("zt_spd02", +0.5, "Sureste-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 55)), ("zt_spd02", +1.0, "Sureste-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (10, 55))), (None, None, "Sureste-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 10)), ("zt_spd02", -0.5, "Sureste-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 35)), ("zt_spd02", +1.0, "Sureste-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 35)), ("zt_spd02", +1.0, "Sureste-No enfria2")),
    (_cond_and(lambda c: c['estatus'] is None,
               lambda c: _pct_cmp(c, 'range', (10, 35))), (None, None, "Sureste-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 10)), ("zt_spd02", -0.5, "Sureste-No enfria4")),
])

# ---------- REGIÓN BC ----------
REGLAS_FRIO["BC"] = {"SP": [], "SPD01": [], "SPD02": []}
REGLAS_FRIO["BC"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['pct'] is None), (None, None, "BC-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 50)), ("zt_sp", +1.0, "BC-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (15, 30))), (None, None, "BC-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 15)), ("zt_sp", -0.5, "BC-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['pct'] is None), (None, None, "BC-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 50)), ("zt_sp", +1.5, "BC-No enfria2")),
    (_cond_and(lambda c: c['estatus'] is None,
               lambda c: _pct_cmp(c, 'range', (15, 50))), (None, None, "BC-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 15)), ("zt_sp", -0.5, "BC-No enfria4")),
])
REGLAS_FRIO["BC"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 25)), ("zt_spd01", +1.0, "BC-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 25)), ("zt_spd01", +2.0, "BC-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (15, 25))), (None, None, "BC-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 5)), ("zt_spd01", -0.5, "BC-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 25)), ("zt_spd01", +1.5, "BC-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 25)), ("zt_spd01", +2.0, "BC-No enfria2")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (15, 25))), (None, None, "BC-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 5)), ("zt_spd01", -0.5, "BC-No enfria4")),
])
REGLAS_FRIO["BC"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd02", +0.5, "BC-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd02", +1.0, "BC-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (20, 30))), (None, None, "BC-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 20)), ("zt_spd02", -0.5, "BC-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd02", +1.0, "BC-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd02", +2.0, "BC-No enfria2")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (20, 30))), (None, None, "BC-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 10)), ("zt_spd02", -0.5, "BC-No enfria4")),
])

# ---------- REGIÓN METRO ----------
REGLAS_FRIO["Metro"] = {"SP": [], "SPD01": [], "SPD02": []}
REGLAS_FRIO["Metro"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['pct'] is None), (None, None, "Centro-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 50)), ("zt_sp", +1.0, "Centro-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (15, 50))), (None, None, "Centro-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 15)), ("zt_sp", -0.5, "Centro-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['pct'] is None), (None, None, "Centro-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 50)), ("zt_sp", +1.5, "Centro-No enfria2")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (15, 50))), (None, None, "Centro-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 15)), ("zt_sp", -0.5, "Centro-No enfria4")),
])
REGLAS_FRIO["Metro"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 35)), ("zt_spd01", +1.0, "Centro-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 35)), ("zt_spd01", +2.0, "Centro-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (15, 35))), (None, None, "Centro-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 5)), ("zt_spd01", -0.5, "Centro-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd01", +1.5, "Centro-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd01", +2.0, "Centro-No enfria2")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (15, 30))), (None, None, "Centro-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 5)), ("zt_spd01", -0.5, "Centro-No enfria4")),
])
REGLAS_FRIO["Metro"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 35)), ("zt_spd02", +0.5, "Centro-Ok1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 35)), ("zt_spd02", +1.0, "Centro-Ok2")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (20, 35))), (None, None, "Centro-Ok3")),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 10)), ("zt_spd02", -0.5, "Centro-Ok4")),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd02", +1.0, "Centro-No enfria1")),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 30)), ("zt_spd02", +2.0, "Centro-No enfria2")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (20, 30))), (None, None, "Centro-No enfria3")),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 10)), ("zt_spd02", -0.5, "Centro-No enfria4")),
])

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================
def _parse_pct(val) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if math.isnan(val):
            return None
        return float(val)
    if not isinstance(val, str):
        return None
    s = val.strip().upper()
    if s == "NA" or s == "":
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", s)
    if match:
        return float(match.group(1))
    return None

def _safe_int(v) -> int | None:
    if v is None:
        return None
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return int(f)
    except (TypeError, ValueError):
        return None

def _safe_float(v, fallback: float = 0.0) -> float:
    if v is None:
        return fallback
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return fallback
        return f
    except (TypeError, ValueError):
        return fallback

def _valor_actual_data(campo: str, data: dict) -> float | None:
    data_key = _DATA_KEY.get(campo, campo)
    valor = data.get(data_key)
    if valor is None:
        return None
    try:
        f = float(valor)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None

def _aplicar_instruccion(campo: str, instruccion, actual: float | None, grupo: str, limite_alto: bool, data: dict, prediccion: dict = None, estatus: str | None = None) -> tuple[int | None, str, str | None]:
    rangos = RANGOS.get(grupo, RANGOS["NL"]).get(limite_alto, RANGOS["NL"][True])
    min_v, max_v = rangos.get(campo, (70, 77))
    permitir_sobre_max = (estatus == "No enfria")
    algoritmo_tag = None

    # Sin instrucción
    if instruccion is None:
        if actual is None:
            return None, "Sin valor actual y sin instrucción → en blanco", None
        if actual < min_v or actual > max_v:
            return None, f"Valor actual {actual:.2f} fuera de rango [{min_v}, {max_v}] → se deja en blanco", None
        return None, f"Valor actual {actual:.2f} dentro de rango, sin cambios", None

    # Desempaquetar instrucción
    if isinstance(instruccion, tuple):
        if len(instruccion) == 2:
            tipo, valor = instruccion
            algoritmo_tag = None
        elif len(instruccion) >= 3:
            tipo, valor, algoritmo_tag = instruccion[0], instruccion[1], instruccion[2]
        else:
            return None, "Instrucción inválida: longitud de tupla incorrecta", None
    else:
        return None, "Instrucción inválida", None

    # Si valor es None, se comporta como sin ajuste (solo validar rango)
    if valor is None:
        if actual is None:
            return None, "Sin valor actual y sin ajuste → en blanco", algoritmo_tag
        if actual < min_v or actual > max_v:
            return None, f"Valor actual {actual:.2f} fuera de rango [{min_v}, {max_v}] → se deja en blanco", algoritmo_tag
        return None, f"Valor actual {actual:.2f} dentro de rango, sin cambios", algoritmo_tag

    # Si es fixed, asignar directamente
    if tipo == "fixed":
        nuevo = float(valor)
        if nuevo < min_v or (nuevo > max_v and not permitir_sobre_max):
            return None, f"Valor fijo {nuevo:.2f} fuera de rango → no se aplica", algoritmo_tag
        return _safe_int(nuevo), f"Valor fijo asignado: {nuevo:.2f} → {_safe_int(nuevo)}", algoritmo_tag

    # Delta: aplicar suma
    if actual is None:
        # Si no hay valor actual, usar predicción si existe
        if prediccion is not None:
            pred_val = prediccion.get(campo)
            if pred_val is not None:
                actual = _safe_float(pred_val, None)
        if actual is None:
            return None, "No hay valor actual ni predicción para aplicar delta", algoritmo_tag

    nuevo = actual + valor
    if nuevo < min_v:
        return None, f"Delta {valor:+} lleva el valor a {nuevo:.2f} por debajo del mínimo {min_v} → no se aplica, se deja en blanco", algoritmo_tag
    if nuevo > max_v:
        if permitir_sobre_max:
            return _safe_int(nuevo), f"Delta {valor:+} excede máximo {max_v} pero estatus='No enfria' → se aplica: {actual:.2f} -> {nuevo:.2f} -> {_safe_int(nuevo)}", algoritmo_tag
        else:
            return None, f"Delta {valor:+} excede máximo {max_v} → no se aplica, se deja en blanco", algoritmo_tag
    return _safe_int(nuevo), f"Aplicado delta {valor:+} → {actual:.2f} -> {nuevo:.2f} -> {_safe_int(nuevo)}", algoritmo_tag

def _resumir_motivo(resultado, data_original, grupo, limite_alto):
    """Genera un motivo descriptivo basado en los cambios aplicados."""
    cambios = []
    rangos = RANGOS.get(grupo, RANGOS["NL"]).get(limite_alto, RANGOS["NL"][True])
    for campo, nombre in [("SP", "SP"), ("SPD01", "SPD01"), ("SPD02", "SPD02")]:
        nuevo = resultado.get(nombre)
        original = _valor_actual_data(campo, data_original)
        if nuevo is None or (isinstance(nuevo, str) and nuevo == ""):
            if original is not None:
                min_v, max_v = rangos.get(campo, (70, 77))
                if original < min_v:
                    cambios.append(f"{nombre} debajo del mínimo")
                elif original > max_v:
                    cambios.append(f"{nombre} arriba del máximo y no aplicaba para cambio")
                else:
                    cambios.append(f"{nombre} sin cambios")
            else:
                cambios.append(f"{nombre} sin cambios")
        else:
            if original is None:
                cambios.append(f"{nombre} sin valor previo")
            elif nuevo > original:
                cambios.append(f"{nombre} aumentó")
            elif nuevo < original:
                cambios.append(f"{nombre} disminuyó")
            else:
                cambios.append(f"{nombre} ajuste de límite")
    return cambios

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================
def clima_frio(data, alerta_ti, pct, queja, grupo, limite_alto, prediccion, resultado, resultclima, estatus):
    explicacion = []
    te = _safe_float(data.get("TE"), 65.0)
    control_gse_raw = data.get("Control GSE")
    control_gse = None if control_gse_raw is None else int(float(control_gse_raw)) if str(control_gse_raw).strip() not in ("", "NA") else None
    tc_raw = data.get("TC")
    tc = None if tc_raw is None else _safe_float(tc_raw, None) if str(tc_raw).strip() not in ("", "NA") else None
    ti_raw = data.get("TI") or data.get("TI Y1 SPD 01")
    ti = None if ti_raw is None else _safe_float(ti_raw, None) if str(ti_raw).strip() not in ("", "NA") else None
    cambios_sp_raw = data.get("Cambios SP")
    cambios_sp = None if cambios_sp_raw is None else int(float(cambios_sp_raw)) if str(cambios_sp_raw).strip() not in ("", "NA") else None

    pct_sp = _parse_pct(pct["SP"]["operacion_pct"]) if isinstance(pct, dict) else None
    pct_spd1 = _parse_pct(pct["SPD1"]["operacion_pct"]) if isinstance(pct, dict) else None
    pct_spd2 = _parse_pct(pct["SPD2"]["operacion_pct"]) if isinstance(pct, dict) else None

    if grupo not in REGLAS_FRIO:
        grupo = "NL"

    explicacion.append(f"Clima FRÍO (TE={te:.1f}°F)")
    explicacion.append(f"Región: {grupo}, Queja: {queja}, Estatus: {estatus}")
    explicacion.append(f"PCT SP: {pct_sp}%, SPD1: {pct_spd1}%, SPD2: {pct_spd2}%")

    resultado_parcial = {}
    campos = [("SP", pct_sp, "SP"), ("SPD01", pct_spd1, "SPD01"), ("SPD02", pct_spd2, "SPD02")]
    for campo, pct_val, nombre_salida in campos:
        ctx = {
            'queja': queja,
            'estatus': estatus,
            'control_gse': control_gse,
            'tc': tc,
            'ti': ti,
            'cambios_sp': cambios_sp,
            'pct': pct_val
        }
        instruccion = None
        for cond, inst in REGLAS_FRIO[grupo][campo]:
            try:
                if cond(ctx):
                    instruccion = inst
                    break
            except Exception:
                continue
        actual = _valor_actual_data(campo, data)
        nuevo, msg, algoritmo_tag = _aplicar_instruccion(campo, instruccion, actual, grupo, limite_alto, data, prediccion, estatus)
        resultado_parcial[nombre_salida] = nuevo if nuevo is not None else ""
        name_algoritmo_tag = (
            "SP" if nombre_salida == "SP"
            else "SPD1" if nombre_salida == "SPD01"
            else "SPD2" if nombre_salida == "SPD02"
            else None
        ) 
        resultado_parcial[f"algoritmo_tag_{name_algoritmo_tag}"] = algoritmo_tag
        explicacion.append(f"{nombre_salida}: {msg}" + (f" (algoritmo: {algoritmo_tag})" if algoritmo_tag else ""))

    resultado.update(resultado_parcial)
    motivo_resumen = _resumir_motivo(resultado, data, grupo, limite_alto)
    
    resultado["motivo"] = motivo_resumen
    resultado["motivo_detallado"] = "\n".join(explicacion)

    return {**resultado, **resultclima}