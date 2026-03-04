from dataclasses import dataclass

@dataclass
class HorarioVentaPublicoModel:
    cliente: str
    sucursal: str
    idvbox: int
    cc: int
    horario: str

@dataclass
class ReglaHorarioSPDModel:
    id: int
    temporada: str
    periodo: str
    temperatura_exterior: str
    tipo_clima: str
    area: str
    spd1_inicio: str
    spd1_fin: str
    spd2_inicio: str
    spd2_fin: str

@dataclass
class ReglaSPSPDModel:
    id: int
    temporada: str
    periodo: str
    temperatura_exterior: str
    ahorro: str
    quejas: bool
    modificar: bool
    accion: str
    sp_min: float
    sp_max: float
    spd_min: float
    spd_max: float