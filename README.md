# Preparación de entorno
Instalar entorno virtual (si ya esta creado se puede saltar este paso)
Linux
```bash
python3 -m venv venv
```

Windows
```bash
python -m venv venv
```

Activar entorno virtual:
Linux
```bash
source venv/bin/activate
```
Windows
```bash 
.\venv\Scripts\activate.ps1

```

# Instalar Dependencias
```bash
pip install -r requirements.txt
```

# Guardar Dependencias
```bash
pip freeze > requirements.txt
```

# Comprimir proyecto
```bash
zip -r proyecto_hvac.zip . \
-x "venv/*" \
-x "db/*" \
-x "*/__pycache__/*" \
-x "*.pyc" \
-x "*.pyo" \
-x ".git/*" \
-x ".DS_Store"
```

uvicorn server:app --reload

http://127.0.0.1:8000/openapi.json

{
            "idCliente": 160,
            "nombre": "GSE - Seven Eleven",
            "regiones": [
                {
                    "idRegion": 606,
                    "nombre": "PACIFICO"
                },
                {
                    "idRegion": 698,
                    "nombre": "NUEVO LEÓN "
                },
                {
                    "idRegion": 707,
                    "nombre": "CENTRO-PENÍNSULA"
                },
                {
                    "idRegion": 708,
                    "nombre": "NORESTE"
                }
            ]
        },