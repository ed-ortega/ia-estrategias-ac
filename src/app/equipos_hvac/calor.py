SIN_AJUSTE = "Sin ajuste"
_K = None  # alias para "Sin cambios"
UMBRALES: dict[str, dict[str, dict]] = {
    "NL": {
        "Ok_TI_baja": {
            "queja_si":  {"spd1": 50, "spd2": 70},
            "queja_no":  {"spd1": 40, "spd2": 60},
            "idoneo":    {"spd1_min": 40, "spd1_max": 70, "spd2_min": 60, "spd2_max": 85, "sp_min": 60},
            "adj_alto_si":  {"SP": ("zt_sp", -2.0),   "SPD01": ("zt_spd01", -1.0), "SPD02": ("zt_spd02", -1.5)},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", -1.0), "SPD02": ("zt_spd02", +0.5)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -1.0), "SPD02": ("zt_spd02", -1.0)},
        },
        "No_enfria_TI_alta": {
            "queja_si":  {"spd1": 70, "spd2": 85},
            "queja_no":  {"spd1": 70, "spd2": 85},
            "idoneo":    {"spd1_min": 40, "spd1_max": 70, "spd2_min": 60, "spd2_max": 85, "sp_min": 60},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +1.5), "SPD02": ("zt_spd02", +0.5)},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +1.5), "SPD02": ("zt_spd02", +0.5)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -0.5), "SPD02": ("zt_spd02", -0.5)},
        },
    },
    "Sureste": {
        "Ok_TI_baja": {
            "queja_si":  {"spd1": 80, "spd2": 90},
            "queja_no":  {"spd1": 80, "spd2": 90},
            "idoneo":    {"spd1_min": 60, "spd1_max": 85, "spd2_min": 65, "spd2_max": 90, "sp_min": 80},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", -0.5), "SPD02": _K},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +0.5)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -1.0), "SPD02": ("zt_spd02", -1.0)},
        },
        "No_enfria_TI_alta": {
            "queja_si":  {"spd1": 80, "spd2": 90},
            "queja_no":  {"spd1": 80, "spd2": 70},
            "idoneo":    {"spd1_min": 60, "spd1_max": 85, "spd2_min": 65, "spd2_max": 90, "sp_min": 80},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +1.5), "SPD02": ("zt_spd02", +1.0)},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +1.5), "SPD02": ("zt_spd02", +1.0)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -0.5), "SPD02": ("zt_spd02", -0.5)},
        },
    },
    "BC": {
        "Ok_TI_baja": {
            "queja_si":  {"spd1": 40, "spd2": 50},
            "queja_no":  {"spd1": 30, "spd2": 40},
            "idoneo":    {"spd1_min": 30, "spd1_max": 60, "spd2_min": 40, "spd2_max": 60, "sp_min": 50},
            "adj_alto_si":  {"SP": ("zt_sp", -1.0),   "SPD01": ("zt_spd01", -0.5), "SPD02": ("zt_spd02", -0.5)},
            "adj_alto_no":  {"SP": ("zt_sp", -1.0),   "SPD01": ("zt_spd01", -0.5), "SPD02": _K},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", +0.5), "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +0.5)},
        },
        "No_enfria_TI_alta": {
            "queja_si":  {"spd1": 60, "spd2": 60},
            "queja_no":  {"spd1": 50, "spd2": 55},
            "idoneo":    {"spd1_min": 30, "spd1_max": 60, "spd2_min": 40, "spd2_max": 60, "sp_min": 50},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +1.0)},
            "adj_alto_no":  {"SP": ("zt_sp", +1.0),   "SPD01": ("zt_spd01", +1.5), "SPD02": ("zt_spd02", +1.5)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -0.5), "SPD02": ("zt_spd02", -0.5)},
        },
    },
    "Metro": {
        "Ok_TI_baja": {
            "queja_si":  {"spd1": 60, "spd2": 70},
            "queja_no":  {"spd1": 60, "spd2": 60},
            "idoneo":    {"spd1_min": 45, "spd1_max": 65, "spd2_min": 55, "spd2_max": 70, "sp_min": 60},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": _K},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +1.0)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -1.0), "SPD02": ("zt_spd02", -1.0)},
        },
        "No_enfria_TI_alta": {
            "queja_si":  {"spd1": 65, "spd2": 70},
            "queja_no":  {"spd1": 50, "spd2": 60},
            "idoneo":    {"spd1_min": 45, "spd1_max": 65, "spd2_min": 55, "spd2_max": 70, "sp_min": 60},
            "adj_alto_si":  {"SP": _K,   "SPD01": ("zt_spd01", +1.0), "SPD02": ("zt_spd02", +1.0)},
            "adj_alto_no":  {"SP": _K,   "SPD01": ("zt_spd01", +1.5), "SPD02": ("zt_spd02", +1.5)},
            "adj_idoneo":   {"SP": _K,   "SPD01": _K,                 "SPD02": _K},
            "adj_bajo":     {"SP": ("zt_sp", -1.0), "SPD01": ("zt_spd01", -0.5), "SPD02": ("zt_spd02", -0.5)},
        },
    },
}

RANGOS: dict[str, dict[bool, dict[str, tuple[int, int]]]] = {
    "NL": {
        True:  {"SP": (70, 73), "SPD01": (71, 76), "SPD02": (71, 75)},
        False: {"SP": (70, 74), "SPD01": (71, 77), "SPD02": (71, 76)},
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
# 🔧 APLICAR AJUSTE INDIVIDUAL
# ==============================
def _resolver_adj(
    campo:     str,
    instruccion,
    data:      dict,
    prediccion: dict,
) -> float:
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

def clima_calido(data, alerta_ti, pct, queja, grupo, limite_alto, prediccion, resultado, resultclima):
    
    ti_spd1 = data.get("TI Y1 SPD 01") or data.get("TIY1") or 0
    ti_alta = ti_spd1 > 65 or alerta_ti

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
        adj_key = f"adj_alto_{('si' if queja == 'Si' else 'no')}"
        motivo = "Disminuye SP por estrategía"
        
    # SIN MODIFICACION
    elif (
        idoneo["spd1_min"] <= pct_spd1 <= idoneo["spd1_max"]
        and
        idoneo["spd2_min"] <= pct_spd2 <= idoneo["spd2_max"]
        and
        pct_sp >= idoneo["sp_min"]
    ):
        adj_key = "adj_idoneo"
        return {
            **resultado,
            "SP": "",
            "SPD01": "",
            "SPD02": "",
            "BandaY1": "",
            "BandaY2": "",
            "motivo": f"{SIN_AJUSTE}: Caso idóneo",
            **resultclima,
        }
    
    else:
        adj_key = "adj_bajo"
        motivo = "Aumenta SP por estrategía"

    adj = umbrales[adj_key]

    # Aplicar ajustes y clipping
    for campo in ("SP", "SPD01", "SPD02"):
        valor_raw  = _resolver_adj(campo, adj[campo], data, prediccion)
        resultado[campo] = _clip(valor_raw, campo, grupo, limite_alto)

    resultado["motivo"] = motivo

    return {**resultado, **resultclima}
