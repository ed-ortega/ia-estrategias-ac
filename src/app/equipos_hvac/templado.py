# templado.py
import math
import re

SIN_AJUSTE = "Sin ajuste"

RANGOS: dict[str, dict[bool, dict[str, tuple[int, int]]]] = {
    "NL": {
        True:  {"SP": (70, 73), "SPD01": (71, 77), "SPD02": (71, 76)},
        False: {"SP": (70, 73), "SPD01": (71, 77), "SPD02": (71, 76)},
    },
    "Sureste": {
        True:  {"SP": (70, 72), "SPD01": (71, 76), "SPD02": (71, 75)},
        False: {"SP": (70, 72), "SPD01": (71, 76), "SPD02": (71, 75)},
    },
    "BC": {
        True:  {"SP": (70, 74), "SPD01": (71, 77), "SPD02": (71, 76)},
        False: {"SP": (70, 74), "SPD01": (71, 77), "SPD02": (71, 76)},
    },
    "Metro": {
        True:  {"SP": (70, 73), "SPD01": (71, 77), "SPD02": (71, 76)},
        False: {"SP": (70, 73), "SPD01": (71, 77), "SPD02": (71, 76)},
    },
}

_DATA_KEY = {
    "SP":    "SP",
    "SPD01": "SPD01",
    "SPD02": "SPD03",
}

REGLAS_TEMPLADO = {}

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
REGLAS_TEMPLADO["NL"] = {"SP": [], "SPD01": [], "SPD02": []}

REGLAS_TEMPLADO["NL"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] is not None and c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 60)), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 60)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 60)), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 60)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
])

REGLAS_TEMPLADO["NL"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 70)), ("zt_spd01", +0.5)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 70)), ("zt_spd01", +0.5)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (30, 70))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 30)), ("zt_spd01", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd01", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd01", +1.0)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (30, 50))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 30)), ("zt_spd01", -0.5)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 74)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
])

REGLAS_TEMPLADO["NL"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 85)), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 85)), ("zt_spd02", +0.5)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (45, 85))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 45)), ("zt_spd02", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 70)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 70)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (45, 70))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 45)), ("zt_spd02", -0.5)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 73)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
])

# ---------- REGIÓN SURESTE ----------
REGLAS_TEMPLADO["Sureste"] = {"SP": [], "SPD01": [], "SPD02": []}
REGLAS_TEMPLADO["Sureste"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 70)), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 70)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 70)), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 70)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
])
REGLAS_TEMPLADO["Sureste"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 80)), ("zt_spd01", +0.5)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 80)), ("zt_spd01", +0.5)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (50, 80))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 50)), ("zt_spd01", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 70)), ("zt_spd01", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 60)), ("zt_spd01", +1.0)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (50, 60))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 50)), ("zt_spd01", -0.5)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 74)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
])
REGLAS_TEMPLADO["Sureste"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 90)), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 90)), ("zt_spd02", +0.5)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (60, 90))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd02", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 90)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 70)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (60, 70))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 60)), ("zt_spd02", -0.5)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 73)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
])

# ---------- REGIÓN BC ----------
REGLAS_TEMPLADO["BC"] = {"SP": [], "SPD01": [], "SPD02": []}
REGLAS_TEMPLADO["BC"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 30)), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 30)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 30)), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 30)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
])
REGLAS_TEMPLADO["BC"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd01", +0.5)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 40)), ("zt_spd01", +0.5)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (10, 40))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 10)), ("zt_spd01", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd01", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 40)), ("zt_spd01", +1.0)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (10, 40))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 10)), ("zt_spd01", -0.5)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 74)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
])
REGLAS_TEMPLADO["BC"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 60)), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd02", +0.5)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (20, 50))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 20)), ("zt_spd02", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 60)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (20, 50))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 20)), ("zt_spd02", -0.5)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 73)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
])

# ---------- REGIÓN METRO ----------
REGLAS_TEMPLADO["Metro"] = {"SP": [], "SPD01": [], "SPD02": []}
REGLAS_TEMPLADO["Metro"]["SP"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 50)), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 50)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: c['pct'] is None), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 50)), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 50)), ("zt_sp", -1.0)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
])
REGLAS_TEMPLADO["Metro"]["SPD01"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 60)), ("zt_spd01", +0.5)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd01", +0.5)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (30, 50))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 30)), ("zt_spd01", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 60)), ("zt_spd01", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 50)), ("zt_spd01", +1.0)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (30, 50))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 30)), ("zt_spd01", -0.5)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 74)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
])
REGLAS_TEMPLADO["Metro"]["SPD02"].extend([
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 70)), None),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 60)), ("zt_spd02", +0.5)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (40, 60))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "Ok",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] <= 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 40)), ("zt_spd02", -1.0)),
    (_cond_and(lambda c: c['queja'] == "Si", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 70)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['queja'] == "No", lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '>', 60)), ("zt_spd02", +1.0)),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] is None,
               lambda c: c['control_gse'] is None, lambda c: c['tc'] is None,
               lambda c: c['ti'] is None, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, 'range', (40, 60))), None),
    (_cond_and(lambda c: c['queja'] is None, lambda c: c['estatus'] == "No enfria",
               lambda c: c['control_gse'] == 1, lambda c: c['tc'] > 0.5,
               lambda c: c['ti'] > 65, lambda c: c['cambios_sp'] < 8,
               lambda c: _pct_cmp(c, '<', 40)), ("zt_spd02", -0.5)),
    (_cond_and(lambda c: c['estatus'] == "Apagado", lambda c: c['control_gse'] == 1,
               lambda c: c['tc'] < 0.5, lambda c: c['ti'] > 65,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 73)),
    (_cond_and(lambda c: c['estatus'] == "Sin control GSE", lambda c: c['control_gse'] == 0,
               lambda c: c['tc'] is None, lambda c: c['ti'] is None,
               lambda c: c['cambios_sp'] is None, lambda c: c['pct'] is None), ("fixed", 72)),
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
        return int(round(f))
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

def _resolver_adj(campo: str, instruccion, data: dict, prediccion: dict) -> float | None:
    if instruccion is None:
        return None
    if isinstance(instruccion, tuple) and len(instruccion) == 2:
        tipo, delta = instruccion
        if tipo == "fixed":
            return float(delta)
        if tipo == "zt_sp":
            base = _safe_float(data.get("SP"), float("nan"))
            if math.isnan(base):
                base = _safe_float(prediccion.get("SP"), float("nan"))
        elif tipo == "zt_spd01":
            base = _safe_float(data.get("SPD01"), float("nan"))
            if math.isnan(base):
                base = _safe_float(prediccion.get("SPD01"), float("nan"))
        elif tipo == "zt_spd02":
            base = _safe_float(data.get("SPD03"), float("nan"))
            if math.isnan(base):
                base = _safe_float(prediccion.get("SPD02"), float("nan"))
        else:
            return None
        if math.isnan(base):
            return None
        return base + delta
    return None

def _aplicar_instruccion(campo: str, instruccion, actual: float | None, grupo: str, limite_alto: bool, data: dict, prediccion: dict) -> tuple[int | None, str]:
    if instruccion is None:
        if actual is None:
            return None, "Sin valor actual y sin instrucción → en blanco"
        rangos = RANGOS.get(grupo, RANGOS["NL"]).get(limite_alto, RANGOS["NL"][True])
        min_v, max_v = rangos.get(campo, (70, 77))
        if actual < min_v:
            return None, f"Valor actual {actual:.2f} < mínimo {min_v} → no se ajusta, se deja en blanco"
        if actual > max_v:
            return max_v, f"Valor actual {actual:.2f} > máximo {max_v}, se baja a {max_v}"
        return None, f"Valor actual {actual:.2f} dentro de rango, sin cambios"
    if isinstance(instruccion, tuple) and len(instruccion) == 2:
        tipo, valor = instruccion
        if tipo == "fixed":
            rangos = RANGOS.get(grupo, RANGOS["NL"]).get(limite_alto, RANGOS["NL"][True])
            min_v, max_v = rangos.get(campo, (70, 77))
            if valor < min_v or valor > max_v:
                return None, f"Valor fijo {valor} fuera de rango [{min_v},{max_v}], no se aplica"
            return int(valor), f"Se asigna valor fijo {valor}"
        else:
            if actual is None:
                pred_val = prediccion.get(campo)
                if pred_val is None:
                    return None, "No hay valor actual ni predicción para aplicar delta"
                actual = _safe_float(pred_val, None)
                if actual is None:
                    return None, "Predicción inválida"
            nuevo = actual + valor
            rangos = RANGOS.get(grupo, RANGOS["NL"]).get(limite_alto, RANGOS["NL"][True])
            min_v, max_v = rangos.get(campo, (70, 77))
            if nuevo < min_v:
                return None, f"Nuevo valor {nuevo:.2f} < mínimo {min_v}, no se aplica"
            if nuevo > max_v:
                return max_v, f"Delta {valor:+} excede máximo, se limita a {max_v}"
            return _safe_int(nuevo), f"Aplicado delta {valor:+} → {nuevo:.2f} -> {int(round(nuevo))}"
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
                    cambios.append(f"{nombre} se limitó a {max_v} por exceder máximo")
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
def clima_templado(data, alerta_ti, pct, queja, grupo, limite_alto, prediccion, resultado, resultclima):
    explicacion = []
    te = _safe_float(data.get("TE"), 72.0)
    estatus = data.get("Estatus Equipo")
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

    if grupo not in REGLAS_TEMPLADO:
        grupo = "NL"

    explicacion.append(f"Clima TEMPLADO (TE={te:.1f}°F)")
    explicacion.append(f"Región: {grupo}, Queja: {queja}, Estatus: {estatus}, Control GSE: {control_gse}, TC: {tc}, TI: {ti}, Cambios SP: {cambios_sp}")
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
        for cond, inst in REGLAS_TEMPLADO[grupo][campo]:
            try:
                if cond(ctx):
                    instruccion = inst
                    break
            except Exception:
                continue
        actual = _valor_actual_data(campo, data)
        nuevo, msg = _aplicar_instruccion(campo, instruccion, actual, grupo, limite_alto, data, prediccion)
        resultado_parcial[nombre_salida] = nuevo if nuevo is not None else ""
        explicacion.append(f"{nombre_salida}: {msg}")

    resultado.update(resultado_parcial)
    motivo_resumen = _resumir_motivo(resultado, data, grupo, limite_alto)
    resultado["motivo"] = motivo_resumen
    resultado["motivo_detallado"] = "\n".join(explicacion)
    
    return {**resultado, **resultclima}