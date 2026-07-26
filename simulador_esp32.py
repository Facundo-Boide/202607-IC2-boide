import time
import json
import random
import math
import paho.mqtt.client as mqtt

# --- CONFIGURACIÓN MQTT ---
BROKER = "localhost"
PORT = 1883

TOPIC_SENSORES = "facu/luflex/ldr"
TOPIC_STATUS   = "facu/luflex/status"
TOPIC_MODO     = "facu/luflex/modo"
TOPIC_COMANDO  = "facu/luflex/comando"
TOPIC_POSICION = "facu/luflex/posicion"

# --- VARIABLES DE ESTADO DEL ESP32 SIMULADO ---
pasos_actuales = 0
pasos_totales = 12000
modo = "manual"  # Inicio en manual estricto

ultima_sugerencia = 0
contador_estabilidad = 0
TIEMPO_CONFIRMACION = 5  # 5 ciclos de confirmación

def viajar_a_porcentaje(porcentaje_objetivo, client):
    global pasos_actuales, pasos_totales
    if pasos_totales == 0: return

    porcentaje_objetivo = max(0, min(100, porcentaje_objetivo))
    target_pasos = int((porcentaje_objetivo * pasos_totales) / 100)
    
    if target_pasos == pasos_actuales: return

    print(f"-> EJECUTANDO MOVIMIENTO: Yendo al {porcentaje_objetivo}% (Pasos: {target_pasos})")
    pasos_actuales = target_pasos
    print("-> MOVIMIENTO FINALIZADO.")
    
    try:
        client.publish(TOPIC_STATUS, f"Cortina reubicada al {porcentaje_objetivo}%")
    except Exception as e:
        print("Error publicando status:", e)

def al_recibir_mqtt(client, userdata, msg):
    global modo
    topico = msg.topic
    payload = msg.payload.decode('utf-8').strip()
    
    print(f"\n[INTERRUPCIÓN MQTT] Llegó algo al bróker!")
    print(f"Tópico: {topico} | Mensaje: {payload}")
    
    if topico == TOPIC_MODO:
        modo = payload
        print(f"-> Modo cambiado a: [{modo}]")
        
    elif topico == TOPIC_COMANDO and modo == "manual":
        if payload == "ABRIR":
            viajar_a_porcentaje(100, client)
        elif payload == "CERRAR":
            viajar_a_porcentaje(0, client)
            
    elif topico == TOPIC_POSICION and modo == "manual":
        try:
            porcentaje = int(payload)
            viajar_a_porcentaje(porcentaje, client)
        except Exception as e:
            print("Error al procesar el valor del slider:", e)

# Conexión adaptativa para soporte de paho-mqtt 1.x y 2.x
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "ESP32_Luflex_Simulado")
except AttributeError:
    client = mqtt.Client(client_id="ESP32_Luflex_Simulado")

client.on_connect = lambda c, u, f, rc: print("\n[MQTT OK] Conexión establecida de forma exitosa.")
client.on_message = al_recibir_mqtt

try:
    client.connect(BROKER, PORT, 60)
    client.subscribe(TOPIC_MODO)
    client.subscribe(TOPIC_COMANDO)
    client.subscribe(TOPIC_POSICION)
except Exception as e:
    print("[MQTT ERR] Error al conectar:", e)
    exit(1)

client.loop_start()

# Secuencia de arranque simulada
print("Iniciando secuencia de calibración inicial...")
time.sleep(1)
print(f"[Calibración OK] Recorrido máximo medido: {pasos_totales} pasos.")
print("\n--- LUFLEX RUNNING (SIMULADOR PROTEGIDO) ---")

t = 0
try:
    while True:
        # Simular lectura analógica de LDR (0 a 4095 con ciclo senoidal)
        luz_actual = int(2000 + 1500 * math.sin(t) + random.randint(-30, 30))
        luz_actual = max(0, min(4095, luz_actual))

        # Lógica Automática mediante LDR (Idéntica a tu ESP32)
        if modo in ["auto1", "auto2"]:
            luz = luz_actual
            
            if modo == "auto1":
                if luz < 1800: sug = 0
                elif 1800 <= luz < 3400: sug = 50
                else: sug = 100
            else: # auto2
                if luz > 3400: sug = 0
                elif 1800 <= luz < 3400: sug = 50
                else: sug = 100

            pos_actual_porcentaje = int((pasos_actuales * 100) / pasos_totales if pasos_totales > 0 else 0)
            
            if sug != pos_actual_porcentaje:
                if sug == ultima_sugerencia:
                    contador_estabilidad += 1
                else:
                    ultima_sugerencia = sug
                    contador_estabilidad = 0
                
                if contador_estabilidad >= TIEMPO_CONFIRMACION:
                    viajar_a_porcentaje(sug, client)
                    contador_estabilidad = 0
            else:
                contador_estabilidad = 0

        # Transmitir telemetría cada 1 segundo
        paquete_ldr = {"promedio": luz_actual}
        try:
            client.publish(TOPIC_SENSORES, json.dumps(paquete_ldr))
            print(f"[Telemetría] Transmitiendo LDR: {luz_actual} | Modo: {modo} | Posición: {int((pasos_actuales*100)/pasos_totales)}%")
        except Exception as e:
            print("Error transmitiendo telemetría:", e)

        t += 0.1
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[SIMULADOR] Deteniendo...")
    client.loop_stop()
    client.disconnect()