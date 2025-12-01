from flask import Flask, request, jsonify 
from datetime import datetime, timezone
import sqlite3
 
app = Flask(__name__) # Es el centro de control de toda la aplicacion web, Flask lo usa como parámetro para ubicar la app y sus recursos
DB_FILE = 'BaseDatos_Logs.db' #Defino el nombre del archivo de mi base de datos

#Lista de tokens permitidos en mi servidor
validar_tokens = {"token-A"} 

# Lista de campos requeridos para validar un log
log_requeridos = ['timestamp', 'service', 'severity', 'message']

def db_server():
    ''' Crear una base de datos '''
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            service TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            received_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

db_server()

@app.route('/logs', methods=['POST']) #Defino la URL como endpoint y solo acepto peticiones HTTP POST

def recibir_log():
    '''Le estás enviando (POST) al servidor un nuevo conjunto de datos de usuario'''
    autentificador = request.headers.get('Authorization','') #Obtiene el valor de la cabecera Authorization de la petición HTTP
    token = autentificador.split(' ', 1)[1].strip() if autentificador.startswith('Token ') else '' #Divide los tokens entre comas y verifica si es un token

    if token not in validar_tokens: #Verifica si el token esta dentro de la lista de tokens validos
        return jsonify({"error": "Quien sos, bro?"}), 401 # 401 Unauthorized
    
    try:
        dato = request.json #Obtener el cuerpo de la solicitud HTTP como objeto JSON
        if not isinstance(dato, list): #Pregunta si el dato es una lista, si no lo es lo convierte
            dato = [dato]
        
        logs_insert = []
        recibir_tiempo = datetime.now(timezone.utc).isoformat() #Marcador de tiempo, se registra la hora exacta que se recibio el log
        
        for log in dato:
            if not all(archivo in log for archivo in log_requeridos): #Verifica si estan todos los campos necesarios para un log
                print(f"Log invalido encontrado y omitido: {log}") 
                continue

            logs_insert.append((
                log['timestamp'], log['service'], log['severity'], log['message'], recibir_tiempo
            )) #Se añaden los datos almacenados correctos
        
        if not logs_insert: #Si no tiene nada, es porque ningun logs es valido
            return jsonify({"ERROR":"No se recibieron logs validos"}), 400


        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        cur.executemany(
            "INSERT INTO logs (timestamp, service, severity, message, received_at) VALUES (?, ?, ?, ?, ?)",
            logs_insert
        )
        conn.commit()
        conn.close()

        return jsonify({"status": f"{len(logs_insert)} logs recibidos y guardados con éxito"}), 201
    except Exception as e:
        return jsonify({"error": f"Error en el procesamiento del lote de logs: {str(e)}"}), 500 #Internal Server Error
    

@app.route('/logs', methods=['GET'])
def get_logs():
    '''Su propósito principal es consultar y filtrar registros (logs)'''
    filters = request.args #Obtiene los parametros de la query de la solicitud HTTP
    condiciones = []
    parametros = []

    if 'service' in filters:
        # Implementación del Desafío 2 (filtrar por el nombre del servicio)
        condiciones.append("service = ?")
        parametros.append(filters['service'])

    if 'severity' in filters:
        # La columna 'severity' debe ser igual al valor pasado por el usuario
        condiciones.append("severity = ?") 
        parametros.append(filters['severity']) # Accedes al valor usando la clave 'severity'

    sql_where = " AND ".join(condiciones) #Convierte mi lista a un cadena separada por la palabra AND
    
    if sql_where:
        sql_where = " WHERE " + sql_where
        
    sql_query = f"SELECT timestamp, service, severity, message, received_at FROM logs {sql_where} ORDER BY timestamp DESC"

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute(sql_query, parametros)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        
        # Devolvemos los logs ordenados y la cantidad de resultados para claridad (legible y ordenado)
        return jsonify({
            "count": len(results),
            "logs": results
        }), 200 #

    except Exception as e:
        return jsonify({"error": f"Error al consultar logs: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5001)
    