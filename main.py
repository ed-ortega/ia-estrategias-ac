from src.api.gse import get_horarios_venta_publico as get_horarios, get_reglas_horario_spd, get_reglas_sp_spd

if __name__ == "__main__":
    horarios = get_horarios()
    reglas_horario = get_reglas_horario_spd()
    reglas_sp = get_reglas_sp_spd()

    print("Horarios Venta Público:", horarios)
    print("Reglas Horario SPD:", reglas_horario)
    print("Reglas SP SPD:", reglas_sp)

    pass