#!/usr/bin/env python3 

# from src.app.horario_spd.ia import entrenar_modelo, predecir_spd, cargar_modelo
from src.app.equipos_hvac.ia import entrenar_modelo, cargar_modelo, predecir_hvac

if __name__ == "__main__":
    # ENTRENAMIENTO DE MODELOS
    entrenar_modelo()

    # APLICACIÓN DE MODELOS
    modelo, target_columns = cargar_modelo()

    prompt = {
        "Tecnología": "Salus",
        "Region": "Norte",
        "Estado": "Nuevo León",
        "Tipo de HVAC": "HVAC 01",
        "Latitud": 25.326873,
        "Longitud": -100.063793,
        "TZ": 78.64,
        "TIY1": 57.77,
        "TIY2": 0,
        "TE Maxima": 85.1,
        "TE Minima": 55.4,
        "Fecha": "2026-03-18",
    }

    resultado = predecir_hvac(
        modelo,
        target_columns,
        prompt
    )

    print("\nPredicción HVAC:")
    print(resultado)