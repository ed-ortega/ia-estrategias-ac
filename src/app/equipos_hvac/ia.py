from rich.console import Console
from .hvac_model import entrenar, cargar, predecir
from .hvac_rules import evaluar_estado, evaluar_queja, calcular_porcentajes_operacion
from .dataset import crear_dataset

console = Console()


# ==============================
# 🚀 ENTRENAMIENTO
# ==============================
def entrenar_modelo():
    df = crear_dataset()

    if df is None or df.empty:
        console.print("[red]Sin datos[/red]")
        return

    entrenar(df)


# ==============================
# 🔮 PREDICCIÓN COMPLETA
# ==============================
def evaluar_equipo(data: dict):

    model, columns, targets = cargar()

    resultado_modelo = predecir(model, columns, targets, data)

    estado = evaluar_estado(data)
    queja = evaluar_queja(data)

    try:
        operacion = calcular_porcentajes_operacion(data)
    except:
        operacion = {"SPD1": 0, "SPD2": 0, "SP": 0}

    return {
        "estado": estado,
        "queja": queja,
        "operacion": operacion,
        "modelo": resultado_modelo
    }
