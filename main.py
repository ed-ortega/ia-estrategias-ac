from src.app.horario_spd.ia import entrenar_modelo, predecir_spd, cargar_modelo

if __name__ == "__main__":
    # ENTRENAMIENTO DE MODELOS
    entrenar_modelo()

    # APLICACIÓN DE MODELOS
    modelo = cargar_modelo()

    resultado = predecir_spd(
        modelo,
        temporada="Invierno",
        tipo_clima="Templado",
        area="Operativo",
        temperatura=14
    )

    print("\nPredicción SPD:")
    print(resultado)