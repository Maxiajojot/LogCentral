import requests #para hacer peticiones HTTP (POST y GET).
from datetime import datetime, timedelta, timezone
import time
from servicios import SERVICIOS_SIMULADOS 

SERVER_URL = "http://127.0.0.1:5001/logs"
SERVICE_TOKEN = "token-A" 
LOG_COUNT = 10


def create_log(service, severity, message, offset_seconds=0):
    """
    Función de ayuda para crear logs con un timestamp en formato ISO 8601 (UTC).
    """
    dt = datetime.now(timezone.utc) 
    dt_offset = dt + timedelta(seconds=offset_seconds)
    
    return {
        "timestamp": dt_offset.isoformat(), 
        "service": service,
        "severity": severity,
        "message": message
    }

def enviar_lote_logs(logs_list):
    """
    Envía el lote de logs al endpoint POST.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {SERVICE_TOKEN}"
    }
    
    try:
        response = requests.post(SERVER_URL, headers=headers, json=logs_list)
        print(f"Lote enviado. Respuesta: {response.status_code} - {response.json()}")
    except requests.exceptions.ConnectionError:
        print("ERROR: No se pudo conectar al servidor. ¿Está corriendo el servidor?")

def consultar_logs(params=None):
    """
    Consulta logs del endpoint GET y muestra los resultados.
    """
    try:
        response = requests.get(SERVER_URL, params=params)
        print(f"\n--- Resultados de la Consulta (Filtros: {params}) ---")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total de logs encontrados: {data['count']}")
            
            # Solo imprimimos los primeros 5 para no llenar la consola
            for log in data['logs'][:5]: 
                print(f"[{log['timestamp']}] {log['service']} | {log['severity']} | {log['message']}")
            
            if data['count'] > 5:
                print(f"... y {data['count'] - 5} más (límite de impresión)")
        else:
            print(f"Error al consultar: {response.status_code} - {response.json()}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: No se pudo conectar al servidor.")


if __name__ == '__main__':
    print("--- 1. Prueba de Envío de Lote Grande con Severidades Variadas ---")
    
    logs_grandes = []
    start_time = time.time()
    
    num_servicios = len(SERVICIOS_SIMULADOS)

    for i in range(LOG_COUNT):
        
        service_data = SERVICIOS_SIMULADOS[i % num_servicios] 
        service_name = service_data['name']
        
       
        if i % 200 == 0:  
            severity = "CRITICAL"
        elif i % 50 == 0: 
            severity = "ERROR"
        elif i % 20 == 0: 
            severity = "WARNING"
        elif i % 5 == 0:  
            severity = "INFO"
        else:             
            severity = "DEBUG"
            
       
        message = f"[{service_data['message_prefix']}] Elemento {i+1}. Severidad: {severity}"
        

        logs_grandes.append(create_log(service_name, severity, message, offset_seconds=-i))
        
    print(f"Generados {LOG_COUNT} logs en memoria. Enviando al servidor...")

    # Enviamos el lote completo de 1000 logs
    enviar_lote_logs(logs_grandes)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nTiempo total de envío y procesamiento: {duration:.2f} segundos.")
    print(f"Velocidad: {LOG_COUNT/duration:.2f} logs/segundo.")
    
    print("\n--- 2. Verificación de Logs Totales ---")
    consultar_logs() 
    
    print("\n--- 3. Prueba de Filtro: Solo Logs de Nivel ERROR ---")
    consultar_logs(params={"severity": "ERROR"})
    
    print("\n--- 4. Prueba de Filtro: Solo Logs del Servicio 'AuthService' ---")
    consultar_logs(params={"service": "AuthService"})
    
    print("\n--- 5. Prueba de Filtro: Solo Logs CRITICAL ---")
    consultar_logs(params={"severity": "CRITICAL"})