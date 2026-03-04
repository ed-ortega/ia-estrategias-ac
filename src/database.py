import mysql.connector

# Configuración de la conexión
config: dict[str, str | bool] = {
    'user': 'root',
    'password': '.UdeG-2811',
    'host': 'localhost',
    'database': 'gse_ia_estrategias',
    'raise_on_warnings': True
}

def tryConnect():
    conexion = mysql.connector.connect(**config)
    try:
        if conexion.is_connected():
            return "Conexión exitosa a la base de datos."
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()


def searchQuery(query: str, params: tuple[int | str | float] | None= None):
    conexion = mysql.connector.connect(**config)
    if not conexion.is_connected():
        return "Error: No se pudo conectar a la base de datos."
    
    cursor = conexion.cursor(dictionary=True)

    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if query.strip().upper().startswith('SELECT'):
            resultados = cursor.fetchall()
            return resultados
        else:
            conexion.commit()
            return f"Consulta ejecutada: {cursor.rowcount} fila(s) afectada(s)."

    except mysql.connector.Error as err:
        return f"Error: {err}"

    finally:
        # Cerrar el cursor y la conexión
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def select(query: str, params: tuple[int | str | float] | None= None):
    """
    select("SELECT * FROM usuarios WHERE edad > %s", (18,))
    """
    if not query.strip().upper().startswith('SELECT'):
        return "Error: Esta función solo admite consultas SELECT."
    return searchQuery(query, params)

def insert(query: str, params: tuple[int | str | float] | None= None):
    """
    insert("INSERT INTO usuarios (nombre, edad) VALUES (%s, %s)", ('Juan', 25))
    """
    if not query.strip().upper().startswith('INSERT'):
        return "Error: Esta función solo admite consultas INSERT."
    return searchQuery(query, params)

def update(query: str, params: tuple[int | str | float] | None= None):
    """
    update("UPDATE usuarios SET edad = %s WHERE id = %s", (30, 1))
    """
    if not query.strip().upper().startswith('UPDATE'):
        return "Error: Esta función solo admite consultas UPDATE."
    return searchQuery(query, params)