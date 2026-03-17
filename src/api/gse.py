from ..database import select
from ..models.gse_ia_estrategias import HorarioVentaPublicoModel, ReglaHorarioSPDModel, ReglaSPSPDModel

def get_horarios_venta_publico(id_cliente = 1):
    query = """
        SELECT 
            c.nombre AS cliente,
            s.nombre AS sucursal,
            s.idvbox AS idvbox,
            s.cc AS cc,
            h.horario
        FROM clientes c
        INNER JOIN sucursales s 
            ON s.id_cliente = c.id
        INNER JOIN horarios_venta_publico h 
            ON h.id_sucursal = s.id
        WHERE c.id = %s;
    """

    resultados = select(query, (id_cliente,))

    return [HorarioVentaPublicoModel(**fila) for fila in resultados]

def get_reglas_horario_spd():
    query = 'SELECT * FROM reglas_horario_spd'
    resultados = select(query)
    return [ReglaHorarioSPDModel(**fila) for fila in resultados]

def get_reglas_sp_spd():
    query = 'SELECT * FROM reglas_sp_spd'
    resultados = select(query)
    return [ReglaSPSPDModel(**fila) for fila in resultados]