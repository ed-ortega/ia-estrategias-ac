import math
import re

SIN_AJUSTE = "Sin ajuste"

RANGOS: dict[str, dict[bool, dict[str, tuple[int, int]]]] = {
    "NL": {
        True:  {"SP": (70, 73), "SPD01": (71, 76), "SPD02": (71, 75)},
        False: {"SP": (70, 73), "SPD01": (71, 77), "SPD02": (71, 76)},
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

_DATA_KEY = {
    "SP":    "SP",
    "SPD01": "SPD01",
    "SPD02": "SPD03",
}

REGLAS_CALIDO = {}

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
REGLAS_CALIDO["NL"] = {"SP": [], "SPD01": [], "SPD02": []}

REGLAS_CALIDO["NL"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 90))), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_sp", -2.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>=', 60)), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_sp", -1.0)),
])
REGLAS_CALIDO["NL"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), ("zt_spd01", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 90))), ("zt_spd01", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd01", -2.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 70)), ("zt_spd01", +1.5)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 70)), ("zt_spd01", +1.5)),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (40, 70))), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 40)), ("zt_spd01", -0.5)),
])
REGLAS_CALIDO["NL"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), ("zt_spd02", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 90))), ("zt_spd02", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd02", -2.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 85)), ("zt_spd02", +0.5)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 85)), ("zt_spd02", +0.5)),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (60, 85))), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd02", -0.5))
])

# ---------- REGIÓN SURESTE ----------
REGLAS_CALIDO["Sureste"] = {"SP": [], "SPD01": [], "SPD02": []}
REGLAS_CALIDO["Sureste"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 90))), ("zt_sp", -1)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_sp", -2.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 80)), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 80)), ("zt_sp", -1.0)),
])
REGLAS_CALIDO["Sureste"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), ("zt_spd01", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 90))), ("zt_spd01", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd01", -2.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 85)), ("zt_spd01", +1.5)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 85)), ("zt_spd01", +1.5)),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (60, 85))), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd01", -0.5)),
])
REGLAS_CALIDO["Sureste"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), ("zt_spd02", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 90)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 90))), ("zt_spd02", -1)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd02", -2.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 90)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 90)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (65, 90))), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 65)), ("zt_spd02", -0.5)),
])

# ---------- REGIÓN BC ----------
REGLAS_CALIDO["BC"] = {"SP": [], "SPD01": [], "SPD02": []}
REGLAS_CALIDO["BC"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 80)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 80)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 80))), ("zt_sp", -1)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_sp", -2)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 70)), ("zt_sp", +1.0)),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (50, 70))), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 50)), ("zt_sp", -1.0)),
])
REGLAS_CALIDO["BC"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 80)), ("zt_spd01", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 80)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 80))), ("zt_spd01", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd01", -2.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 60)), ("zt_spd01", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd01", +1.5)),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (30, 60))), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 30)), ("zt_spd01", -0.5)),
])
REGLAS_CALIDO["BC"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 80)), ("zt_spd02", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 80)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 80))), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd02", -2.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 60)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 55)), ("zt_spd02", +1.5)),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (40, 60))), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 40)), ("zt_spd02", -0.5)),
    
])

# ---------- REGIÓN METRO ----------
REGLAS_CALIDO["Metro"] = {"SP": [], "SPD01": [], "SPD02": []}
REGLAS_CALIDO["Metro"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 85)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 85)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 85))), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_sp", -2.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 60)), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_sp", -1.0)),
])
REGLAS_CALIDO["Metro"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 85)), ("zt_spd01", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 85)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 85))), ("zt_sp01", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd01", -2.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 65)), ("zt_spd01", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd01", +1.5)),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (45, 65))), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 30)), ("zt_spd01", -0.5)),
])
REGLAS_CALIDO["Metro"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 85)), ("zt_spd02", -1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '>', 85)), None),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, 'range', (60, 85))), ("zt_spd02", -1)),
    (_cond_and(lambda c: c['estatus'] == "Ok",
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd02", -2.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 70)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '>', 60)), ("zt_spd02", +1.5)),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, 'range', (55, 70))), None),
    (_cond_and(lambda c: c['estatus'] == "No enfria",
               lambda c: _pct_cmp(c, '<', 55)), ("zt_spd02", -0.5)),
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

def _aplicar_instruccion(campo: str, instruccion, actual: float | None, grupo: str, limite_alto: bool, data: dict, estatus: str | None = None) -> tuple[int | None, str]:
    rangos = RANGOS.get(grupo, RANGOS["NL"]).get(limite_alto, RANGOS["NL"][True])
    min_v, max_v = rangos.get(campo, (70, 77))

    # Si es "No enfria", no aplicamos límite máximo (solo se respeta el mínimo)
    no_upper_clamp = (estatus == "No enfria")

    # --- Caso sin instrucción ---
    if instruccion is None:
        if actual is None:
            return None, "Sin valor actual y sin instrucción → en blanco"
        if actual < min_v:
            return None, f"Valor actual {actual:.2f} < mínimo {min_v} → se deja en blanco"
        if actual > max_v:
            if no_upper_clamp:
                # No hay instrucción de cambio, el valor excede el máximo y está en "No enfria" → se pone None
                return None, f"Valor actual {actual:.2f} > máximo {max_v} y estatus='No enfria' sin instrucción → se deja en blanco"
            else:
                return max_v, f"Valor actual {actual:.2f} > máximo {max_v} → se ajusta a {max_v}"
        return None, f"Valor actual {actual:.2f} dentro de rango, sin cambios"

    # --- Caso con instrucción (fixed o delta) ---
    if isinstance(instruccion, tuple) and len(instruccion) == 2:
        tipo, valor = instruccion

        if tipo == "fixed":
            nuevo = valor
            if nuevo < min_v:
                return None, f"Valor fijo {nuevo} < mínimo {min_v} → no se aplica, se deja en blanco"
            if nuevo > max_v:
                if no_upper_clamp:
                    # Aplicamos el fixed aunque exceda el máximo
                    return _safe_int(nuevo), f"Valor fijo {nuevo} excede máximo {max_v} pero estatus='No enfria' → se asigna {nuevo}"
                else:
                    nuevo = max_v
                    return _safe_int(nuevo), f"Valor fijo excede máximo → se ajusta a {nuevo}"
            return _safe_int(nuevo), f"Se asigna valor fijo {nuevo}"

        else:  # delta
            if actual is None:
                return None, "No hay valor actual para aplicar delta"
            nuevo = actual + valor
            if nuevo < min_v:
                nuevo = min_v
                return _safe_int(nuevo), f"Delta {valor:+} lleva el valor a {nuevo:.2f} por debajo del mínimo, se ajusta a {min_v}"
            if nuevo > max_v:
                if no_upper_clamp:
                    # Aplicamos el delta aunque exceda el máximo
                    return _safe_int(nuevo), f"Delta {valor:+} excede máximo {max_v} pero estatus='No enfria' → se aplica: {actual:.2f} -> {nuevo:.2f} -> {_safe_int(nuevo)}"
                else:
                    nuevo = max_v
                    return _safe_int(nuevo), f"Delta {valor:+} excede máximo → se ajusta a {nuevo}"
            return _safe_int(nuevo), f"Aplicado delta {valor:+} → {actual:.2f} -> {nuevo:.2f} -> {_safe_int(nuevo)}"

    return None, "Instrucción inválida"

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
                    cambios.append(f"{nombre} no se modificó porque estaba debajo del mínimo ({min_v})")
                elif original > max_v:
                    cambios.append(f"{nombre} no se modificó porque excedía el máximo y no aplicaba cambio")
                else:
                    cambios.append(f"{nombre} sin cambios")
            else:
                cambios.append(f"{nombre} sin cambios (sin valor original)")
        else:
            if original is None:
                cambios.append(f"{nombre} asignado a {nuevo} (sin valor previo)")
            elif nuevo > original:
                cambios.append(f"{nombre} aumentó de {original} a {nuevo}")
            elif nuevo < original:
                cambios.append(f"{nombre} disminuyó de {original} a {nuevo}")
            else:
                cambios.append(f"{nombre} permaneció en {nuevo}")
    return " | ".join(cambios)

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================
def clima_calido(data, alerta_ti, pct, queja, grupo, limite_alto, prediccion, resultado, resultclima, estatus):
    explicacion = []
    te = _safe_float(data.get("TE"), 80.0)
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

    if grupo not in REGLAS_CALIDO:
        grupo = "NA"

    explicacion.append(f"Clima CÁLIDO (TE={te:.1f}°F)")
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
        for cond, inst in REGLAS_CALIDO[grupo][campo]:
            try:
                if cond(ctx):
                    instruccion = inst
                    break
            except Exception:
                continue
        actual = _valor_actual_data(campo, data)
        nuevo, msg = _aplicar_instruccion(campo, instruccion, actual, grupo, limite_alto, data, estatus)
        resultado_parcial[nombre_salida] = nuevo if nuevo is not None else ""
        explicacion.append(f"{nombre_salida}: {msg}")

    resultado.update(resultado_parcial)
    motivo_resumen = _resumir_motivo(resultado, data, grupo, limite_alto)
    
    resultado["motivo"] = motivo_resumen
    resultado["motivo_detallado"] = "\n".join(explicacion)

    return {**resultado, **resultclima}