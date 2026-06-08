from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from src.app.equipos_hvac.hvac_model import cargar, predecir
from src.app.equipos_hvac.hvac_rules import (
    evaluar_estado,
    evaluar_queja,
    calcular_porcentajes_operacion
)

model, columns, targets = cargar()

app = FastAPI(
    title="API HVAC Predict",
    version="1.0.0",
    description="API para recibir datos HVAC",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HvacPredict(BaseModel):
    idVbox: int
    CC: int
    Sucursal: str
    Ubicacion: str

    Tecnologia: str = Field(alias="Tecnología")
    Fecha: int
    Region: str
    Estado: str

    Latitud: float
    Longitud: float

    Tipo_HVAC: str = Field(alias="Tipo de HVAC")

    TZ: float
    TC: float
    TIY1: float
    TIY2: Optional[float] = None

    Y1: Optional[float] = None
    Y2: Optional[float] = None

    BandaY1: Optional[float] = None
    BandaY2: Optional[float] = None

    SP: Optional[float] = None
    SPD01: Optional[float] = None
    SPD03: Optional[float] = None

    CambiosSP: Optional[float] = None
    CiclosY1: Optional[float] = None
    CiclosY2: Optional[float] = None

    CtrlGSE: Optional[float] = None
    AlertaTIdanado: Optional[int] = None

    TI_Offline: Optional[int] = Field(
        default=None,
        alias="TI Offline"
    )

    horario_inicio_SPD_01: Optional[str] = None
    horario_fin_SPD_01: Optional[str] = None
    horario_inicio_SPD_02: Optional[str] = None
    horario_fin_SPD_02: Optional[str] = None

    TZ_SPD_01: Optional[float] = Field(
        default=None,
        alias="TZ SPD 01"
    )

    TZ_SPD_02: Optional[float] = Field(
        default=None,
        alias="TZ SPD 02"
    )

    TZ_SP: Optional[float] = Field(
        default=None,
        alias="TZ SP"
    )

    TI_Y1_SPD_01: Optional[float] = Field(
        default=None,
        alias="TI Y1 SPD 01"
    )

    TI_Y1_SPD_02: Optional[float] = Field(
        default=None,
        alias="TI Y1 SPD 02"
    )

    TI_Y1_SP: Optional[float] = Field(
        default=None,
        alias="TI Y1 SP"
    )

    TI_Y2_SPD_01: Optional[float] = Field(
        default=None,
        alias="TI Y2 SPD 01"
    )

    TI_Y2_SPD_02: Optional[float] = Field(
        default=None,
        alias="TI Y2 SPD 02"
    )

    TI_Y2_SP: Optional[float] = Field(
        default=None,
        alias="TI Y2 SP"
    )

    TE_SPD_01: Optional[float] = Field(
        default=None,
        alias="TE SPD 01"
    )

    TE_SPD_02: Optional[float] = Field(
        default=None,
        alias="TE SPD 02"
    )

    TE_SP: Optional[float] = Field(
        default=None,
        alias="TE SP"
    )

    Y1_SPD_01: Optional[float] = Field(
        default=None,
        alias="Y1 SPD 01"
    )

    Y1_SPD_02: Optional[float] = Field(
        default=None,
        alias="Y1 SPD 02"
    )

    Y1_SP: Optional[float] = Field(
        default=None,
        alias="Y1 SP"
    )

    Y2_SPD_01: Optional[float] = Field(
        default=None,
        alias="Y2 SPD 01"
    )

    Y2_SPD_02: Optional[float] = Field(
        default=None,
        alias="Y2 SPD 02"
    )

    Y2_SP: Optional[float] = Field(
        default=None,
        alias="Y2 SP"
    )

    Mode_FAN_SPD_01: Optional[float] = Field(
        default=None,
        alias="Mode FAN SPD 01"
    )

    Mode_FAN_SP: Optional[float] = Field(
        default=None,
        alias="Mode FAN SP"
    )

    Mode_FAN_SPD_02: Optional[float] = Field(
        default=None,
        alias="Mode FAN SPD 02"
    )

    model_config = {
        "populate_by_name": True
    }

@app.post("/hvac_predict")
async def hvac_predict(hvac: HvacPredict):

    # Objeto Python
    prompt = hvac.model_dump(by_alias=True)
    
    resultado_modelo = predecir(
        model,
        columns,
        targets,
        prompt
    )
    estado = evaluar_estado(prompt)

    queja = evaluar_queja(prompt)

    try:
        operacion = calcular_porcentajes_operacion(prompt)

    except Exception:
        operacion = {
            "SPD1": {},
            "SPD2": {},
            "SP": {}
        }

    ajustado = (
        resultado_modelo
        .get("ajustado", {})
        .get("resultados_ia", {})
    )

    resultado_final = {
        "estado": estado,
        "queja": queja
    }

    for sensor in ["SP", "SPD1", "SPD2"]:

        resultado_sensor = {
            "operacion_pct": operacion.get(sensor, {}).get("operacion_pct", ""),
            "temp_prom": operacion.get(sensor, {}).get("temp_prom", ""),
            "motivo" : ajustado.get(sensor, {}).get("motivo", ""),
            "motivo_detallado": ajustado.get(sensor, {}).get("motivo_detallado", ""),
            "clima": ajustado.get(sensor, {}).get("clima", "")
        }

        if sensor == "SP":
            resultado_sensor["SP"] = (
                ajustado.get(sensor, {}).get("SP", "")
            )

        elif sensor == "SPD1":
            resultado_sensor["SPD01"] = (
                ajustado.get(sensor, {}).get("SPD01", "")
            )

        elif sensor == "SPD2":
            resultado_sensor["SPD02"] = (
                ajustado.get(sensor, {}).get("SPD02", "")
            )

        resultado_final[sensor] = resultado_sensor

    resultado_final["BandaY1"] = (
        ajustado.get("SP", {}).get("BandaY1", "")
    )

    resultado_final["BandaY2"] = (
        ajustado.get("SP", {}).get("BandaY2", "")
    )

    response = {
        **prompt,
        "resultado":resultado_final
    }

    return JSONResponse(
        status_code=200,
        content=response
    )