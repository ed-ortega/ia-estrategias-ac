import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.panel import Panel
from ...api.gsepro import GSEClient
from .utils import dividir_en_bloques, procesar, hora_a_ciclico
from ...api.openmateo import cerrar_cache

MODEL_PATH = Path("src/data/equipos_hvac_model.pkl")

hoy = datetime.now()
ANIO_INICIO = hoy.year - 2
MES_INICIO = 1
DIA_INICIO = 1
ANIO_FIN = hoy.year
MES_FIN = hoy.month
DIA_FIN = hoy.day - 2

BLOQUE_DIAS = 14

console = Console()

# ----------------------------------
# CREAR DATASET
# ----------------------------------
def crear_dataset():
    gse = GSEClient()

    cliente = next(
        (c for c in gse.clientes_regiones() if c["idCliente"] == 160),
        None
    )

    if not cliente:
        console.print("[bold red]Cliente no encontrado[/bold red]")
        return pd.DataFrame()  # 🔥 SIEMPRE regresar DataFrame

    fecha_inicio = datetime(ANIO_INICIO, MES_INICIO, DIA_INICIO)
    fecha_fin = datetime(ANIO_FIN, MES_FIN, DIA_FIN)
    
    bloques = dividir_en_bloques(fecha_inicio, fecha_fin, BLOQUE_DIAS)
    regiones = cliente["regiones"]

    resultados_globales = []
    
    for inicio, fin in bloques:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    procesar,
                    gse,
                    cliente["idCliente"],
                    region,
                    inicio,
                    fin
                )
                for region in regiones
            ]

            bloque_registros = []

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:  # 🔥 evita None o []
                        bloque_registros.extend(result)
                except Exception as e:
                    console.print(f"[red]Error en thread:[/red] {e}")

        resultados_globales.extend(bloque_registros)

    # 🔥 VALIDACIÓN CRÍTICA
    if not resultados_globales:
        console.print("[bold red]❌ Dataset vacío desde origen (API sin datos)[/bold red]")
        return pd.DataFrame()

    columnas = [
        "Idvbox","CC","Sucursal","Ubicación","Tecnología","Fecha",
        "Region","Estado","Latitud","Longitud","Tipo de HVAC",
        "TZ","TIY1","TIY2","Y1","Y2","BandaY1","BandaY2",
        "SP","SPD01","SPD02","SPD03", "TE Maxima", "TE Minima",
        "horario_inicio_SPD_01","horario_fin_SPD_01",
        "horario_inicio_SPD_02","horario_fin_SPD_02",
        "irregular","SP_decimal","SPD03_decimal"
    ]

    df = pd.DataFrame(resultados_globales, columns=columnas)

    # 🔥 VALIDACIÓN EXTRA
    if df.empty:
        console.print("[bold red]❌ DataFrame vacío después de construirlo[/bold red]")
        return df
    
    cerrar_cache()

    return df

# ----------------------------------
# ENTRENAR MODELO
# ----------------------------------
def entrenar_modelo():
    console.rule("[bold cyan]🚀 ENTRENAMIENTO MODELO HVAC")

    with console.status("[bold green]Cargando dataset..."):
        df = crear_dataset()

    # 🔥 VALIDACIÓN REAL
    if df is None or df.empty:
        console.print("[bold red]Modelo cancelado:[/bold red] no hay información por procesar")
        return

    console.print("[green]✔ Dataset cargado[/green]")

    columnas_clave = [
        "Idvbox",
        "CC",
        "Sucursal",
        "Ubicación"
    ]

    df_limpio = (
        df
        .sort_values("Fecha", ascending=False)
        .drop_duplicates(subset=columnas_clave, keep="first")
    )
    
    df_limpio.to_excel("datos_crudos.xlsx", index=False)

    console.print(Panel.fit(
        f"[bold]Registros:[/bold] {len(df)}\n[bold]Columnas:[/bold] {len(df.columns)}",
        title="📊 Dataset cargado",
        border_style="green"
    ))

    console.rule("[cyan]⚙️ Feature Engineering")

    # 🔥 Limpieza básica
    nulls = df.isna().sum().sum()
    df = df.fillna(0)
    console.print(f"[yellow]⚠ Nulls reemplazados:[/yellow] {nulls}")

    if df.empty:
        console.print("[bold red]❌ Dataset vacío después de limpieza[/bold red]")
        return

    # =========================================================
    # 🔷 FEATURES (X)
    # =========================================================
    X = df[
        [
            "Tecnología","Region","Estado","Tipo de HVAC",
            "Latitud","Longitud","TZ","TIY1","TIY2", "TE Maxima", "TE Minima",
            "Fecha"
        ]
    ]

    # 🔥 Convertir fecha a algo útil
    if "Fecha" in X.columns:
        X["Fecha"] = pd.to_datetime(X["Fecha"], errors="coerce")
        X["hora"] = X["Fecha"].dt.hour.fillna(0)
        X["dia_semana"] = X["Fecha"].dt.dayofweek.fillna(0)
        X.drop(columns=["Fecha"], inplace=True)

    X = pd.get_dummies(X)

    # =========================================================
    # 🔷 TARGET (y)
    # =========================================================
    y = df[
        [
            "Y1","Y2","BandaY1","BandaY2","SP",
            "SPD01","SPD02","SPD03",
            "horario_inicio_SPD_01","horario_fin_SPD_01",
            "horario_inicio_SPD_02","horario_fin_SPD_02"
        ]
    ].copy()

    # =========================================================
    # 🔥 1. HORARIOS → CODIFICACIÓN CÍCLICA
    # =========================================================
    cols_horario = [
        "horario_inicio_SPD_01","horario_fin_SPD_01",
        "horario_inicio_SPD_02","horario_fin_SPD_02"
    ]

    for col in cols_horario:
        y[[f"{col}_sin", f"{col}_cos"]] = y[col].apply(
            lambda x: pd.Series(hora_a_ciclico(x))
        )

    y.drop(columns=cols_horario, inplace=True)

    # =========================================================
    # 🔥 2. CATEGÓRICAS → ONE HOT
    # =========================================================
    cols_categoricas = ["BandaY1","BandaY2","SPD02"]

    for col in cols_categoricas:
        y[col] = y[col].astype(str)

    y = pd.get_dummies(y, columns=cols_categoricas)

    # =========================================================
    # 🤖 MODELO
    # =========================================================
    console.rule("[cyan]🤖 Entrenando modelo")

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    console.print(Panel.fit(
        "[bold green]✔ Modelo entrenado correctamente[/bold green]",
        border_style="green"
    ))

    guardar_modelo(model, X.columns.tolist(),y.columns.tolist())

    console.print(Panel.fit(
        "[bold cyan]💾 Modelo guardado exitosamente[/bold cyan]",
        border_style="cyan"
    ))

    console.rule("[bold green]✅ PROCESO COMPLETADO")

# ----------------------------------
# GUARDAR MODELO
# ----------------------------------
def guardar_modelo(modelo, x, y):
    joblib.dump({
        "model": modelo,
        "columns": x,
        "target_columns": y,
    }, MODEL_PATH)

# ----------------------------------
# CARGAR MODELO
# ----------------------------------
def cargar_modelo():
    data = joblib.load(MODEL_PATH)
    return data["model"], data["target_columns"]

# ----------------------------------
# PREDICCION
# ----------------------------------
def predecir_hvac(model, target_columns, data: dict):
    X = pd.DataFrame([data])

    X["Fecha"] = pd.to_datetime(X["Fecha"], errors="coerce")
    X["hora"] = X["Fecha"].dt.hour.fillna(0)
    X["dia_semana"] = X["Fecha"].dt.dayofweek.fillna(0)
    X.drop(columns=["Fecha"], inplace=True)

    X = pd.get_dummies(X)
    X = X.reindex(columns=model.feature_names_in_, fill_value=0)

    pred = model.predict(X)[0]
    raw = dict(zip(target_columns, pred))

    # =========================================
    # 🔥 PARSER HUMANO
    # =========================================
    
    # 🎯 bandas → tomar la mayor probabilidad
    def decode_one_hot(prefix):
        opciones = {k: v for k, v in raw.items() if k.startswith(prefix)}
        if not opciones:
            return None
        best = max(opciones, key=opciones.get)
        return float(best.split("_")[1])

    resultado = {
        "Y1": round(float(raw["Y1"]), 2),
        "Y2": round(float(raw["Y2"]), 2),
        "SP": round(float(raw["SP"]), 2),
        "SPD01": round(float(raw["SPD01"]), 2),
        "SPD02": round(float(raw["SPD03"]), 2),
        "BandaY1": round(decode_one_hot("BandaY1"), 2),
        "BandaY2": round(decode_one_hot("BandaY2"), 2) 
    }

    return resultado