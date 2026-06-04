# dataset.py

import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console

from ...api.gsepro import GSEClient
from .utils import dividir_en_bloques, procesar

console = Console()

# ==============================
# 📁 PATHS
# ==============================
DATA_PATH = Path("src/data/hvac_historico.parquet")
META_PATH = Path("src/data/meta.json")

BLOQUE_DIAS = 7


# ==============================
# 🧹 LIMPIEZA
# ==============================
def limpiar_numeros(df, columnas):
    for col in columnas:
        if col not in df.columns:
            continue

        df[col] = (
            df[col]
            .astype(str)
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
        )

        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def detectar_columnas_corruptas(df, columnas):
    console.print("\n[bold yellow]🔍 Detectando columnas corruptas...[/bold yellow]")

    for col in columnas:
        if col not in df.columns:
            continue

        max_val = df[col].max()
        min_val = df[col].min()

        if pd.notna(max_val) and pd.notna(min_val):
            if max_val > 10000 or min_val < -1000:
                console.print(f"[red]⚠️ {col} sospechosa → min={min_val}, max={max_val}[/red]")


# ==============================
# 🧠 META (última fecha)
# ==============================
def guardar_ultima_fecha(fecha):
    META_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(META_PATH, "w") as f:
        json.dump({"ultima_fecha": fecha.isoformat()}, f)


def obtener_ultima_fecha():
    if not META_PATH.exists():
        return None

    with open(META_PATH, "r") as f:
        return datetime.fromisoformat(json.load(f)["ultima_fecha"])


# ==============================
# 🧱 NORMALIZACIONES
# ==============================
def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={
        "idVbox": "Idvbox",
        "Ubicacion": "Ubicación",
        "Tecnologia": "Tecnología"
    })


def asegurar_columnas(df: pd.DataFrame, columnas: list):
    for col in columnas:
        if col not in df.columns:
            df[col] = None
    return df


# ==============================
# 📊 CREAR DATASET
# ==============================
def crear_dataset():

    console.rule("[bold cyan]📦 CREANDO DATASET HVAC")

    gse = GSEClient()

    cliente = next(
        (c for c in gse.clientes_regiones() if c["idCliente"] == 160),
        None
    )

    if not cliente:
        console.print("[bold red]Cliente no encontrado[/bold red]")
        return pd.DataFrame()

    # ==============================
    # 📅 RANGO DE FECHAS
    # ==============================
    hoy = datetime.now()
    ultima_fecha = obtener_ultima_fecha()

    if ultima_fecha:
        fecha_inicio = ultima_fecha + timedelta(days=1)
    else:
        fecha_inicio = datetime(hoy.year, 1, 1)

    fecha_fin = hoy - timedelta(days=2)

    if fecha_inicio >= fecha_fin:
        console.print("[yellow]Dataset ya actualizado[/yellow]")

        if DATA_PATH.exists():
            return pd.read_parquet(DATA_PATH)

        return pd.DataFrame()

    console.print(f"[cyan]Descargando: {fecha_inicio.date()} → {fecha_fin.date()}[/cyan]")

    # ==============================
    # 🔄 BLOQUES + PARALELISMO
    # ==============================
    bloques = dividir_en_bloques(fecha_inicio, fecha_fin, BLOQUE_DIAS)
    regiones = cliente["regiones"]

    resultados_globales = []

    for inicio, fin in bloques:
        console.print(f"[blue]Bloque: {inicio.date()} → {fin.date()}[/blue]")

        for region in regiones:
            try:
                console.print(
                    f"[cyan]Procesando región {region['idRegion']} - {region['nombre']}[/cyan]"
                )

                result = procesar(
                    gse,
                    cliente["idCliente"],
                    region,
                    inicio,
                    fin
                )

                if result:
                    resultados_globales.extend(result)

            except Exception as e:
                console.print(
                    f"[red]Error en región {region['idRegion']}:[/red] {e}"
                )

    if not resultados_globales:
        console.print("[red]Sin resultados nuevos[/red]")
        return pd.DataFrame()

    # ==============================
    # 🧱 DATAFRAME
    # ==============================
    df_nuevo = pd.DataFrame(resultados_globales)
    df_nuevo = normalizar_columnas(df_nuevo)

    # ==============================
    # 🧹 LIMPIEZA NUMÉRICA
    # ==============================
    columnas_numericas = [
        "Y1","Y2","SP","SPD01","SPD03",
        "TZ","TIY1","TIY2"
    ]

    df_nuevo = limpiar_numeros(df_nuevo, columnas_numericas)
    detectar_columnas_corruptas(df_nuevo, columnas_numericas)

    # ==============================
    # 🔧 ASEGURAR COLUMNAS (ML READY)
    # ==============================
    columnas_modelo = [
        "CtrlGSE","CambiosSP","CiclosY1","CiclosY2","AlertaTIdanado",
        "TI Offline",

        "TZ SPD 01","TZ SPD 02","TZ SP",

        "TI Y1 SPD 01","TI Y1 SPD 02","TI Y1 SP",
        "TI Y2 SPD 01","TI Y2 SPD 02","TI Y2 SP",

        "TE SPD 01","TE SPD 02","TE SP","TC",

        "Y1 SPD 01","Y1 SPD 02","Y1 SP",
        "Y2 SPD 01","Y2 SPD 02","Y2 SP",

        "Mode FAN SPD 01","Mode FAN SPD 02","Mode FAN SP",

        "horario_inicio_SPD_01","horario_fin_SPD_01",
        "horario_inicio_SPD_02","horario_fin_SPD_02",
    ]

    df_nuevo = asegurar_columnas(df_nuevo, columnas_modelo)

    # ==============================
    # 📚 HISTÓRICO
    # ==============================
    if DATA_PATH.exists():
        df_hist = pd.read_parquet(DATA_PATH)
        df_total = pd.concat([df_hist, df_nuevo]).drop_duplicates()
    else:
        df_total = df_nuevo

    # ==============================
    # 🧹 FILTROS IMPORTANTES
    # ==============================
    columnas_clave = ["SP","SPD01","SPD03","BandaY1","BandaY2"]
    df_total = df_total.dropna(subset=columnas_clave)

    # ==============================
    # 💾 GUARDAR
    # ==============================
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_total.to_parquet(DATA_PATH, index=False)

    guardar_ultima_fecha(fecha_fin)

    console.print(f"[green]Dataset listo: {len(df_total)} filas[/green]")

    return df_total