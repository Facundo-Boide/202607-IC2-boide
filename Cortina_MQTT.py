import machine
import network
import json
import utime
from machine import ADC, Pin
from umqtt.simple import MQTTClient

# --- CONFIGURACIÓN DE RED ---
WIFI_SSID = "UNRaf_Libre"
WIFI_PASS = "unraf2021"

# --- CONFIGURACIÓN MQTT ---
CLIENT_ID = "ESP32_Luflex_Hibrido_Test"
MQTT_BROKER = "10.103.30.91"  # Tu IP de la Raspberry de hoy

# Tópicos
TOPIC_SENSORES = "facu/luflex/ldr"
TOPIC_STATUS   = "facu/luflex/status"
TOPIC_MODO     = "facu/luflex/modo"
TOPIC_COMANDO  = "facu/luflex/comando"
TOPIC_POSICION = "facu/luflex/posicion"

# --- 1. CONFIGURACIÓN DE HARDWARE ---
step_pin = Pin(25, Pin.OUT)
dir_pin = Pin(27, Pin.OUT)
enable_pin = Pin(12, Pin.OUT)

enable_pin.value(1) # Motor apagado al inicio

ldr1 = ADC(Pin(33)); ldr2 = ADC(Pin(32)); ldr3 = ADC(Pin(35))
ldr1.atten(ADC.ATTN_11DB); ldr2.atten(ADC.ATTN_11DB); ldr3.atten(ADC.ATTN_11DB)

hall_0 = Pin(17, Pin.IN, Pin.PULL_UP) 

# --- 2. VARIABLES DE CONTROL ---
pasos_actuales = 0
pasos_totales = 0  
modo = "manual"  # Forzamos inicio en manual estricto
delay_paso_us = 2000
delay_paso_cal = 4000

ultima_sugerencia = 0
contador_estabilidad = 0
TIEMPO_CONFIRMACION = 5 

# --- 3. CONECTIVIDAD WI-FI ---
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando a UNRaf_Libre...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        intentos = 0
        while not wlan.isconnected() and intentos < 15:
            utime.sleep(1)
            intentos += 1
    if wlan.isconnected():
        print("\n[Wi-Fi OK] Conectado con éxito a la facultad.")
        print("IP asignada por la red:", wlan.ifconfig()[0])

# --- 4. FUNCIONES DEL MOTOR ---
def motor_on():
    enable_pin.value(0)
    utime.sleep_ms(10)

def motor_off():
    enable_pin.value(1)

def dar_paso_fisico():
    step_pin.value(1)
    utime.sleep_us(delay_paso_us)
    step_pin.value(0)
    utime.sleep_us(delay_paso_us)

def dar_paso_fisico_calibracion():
    step_pin.value(1)
    utime.sleep_us(delay_paso_cal)
    step_pin.value(0)
    utime.sleep_us(delay_paso_cal)

def viajar_a_porcentaje(porcentaje_objetivo):
    global pasos_actuales, pasos_totales
    if pasos_totales == 0: return 

    porcentaje_objetivo = max(0, min(100, porcentaje_objetivo))
    target_pasos = int((porcentaje_objetivo * pasos_totales) / 100)
    
    if target_pasos == pasos_actuales: return

    print("-> EJECUTANDO MOVIMIENTO: Yendo al {}% (Pasos: {})".format(porcentaje_objetivo, target_pasos))
    motor_on()
    dir_pin.value(1 if target_pasos > pasos_actuales else 0)

    while pasos_actuales != target_pasos:
        dar_paso_fisico()
        if target_pasos > pasos_actuales:
            pasos_actuales += 1
        else:
            pasos_actuales -= 1
        
        if pasos_actuales < 150 and hall_0.value() == 0:
            for _ in range(40): dar_paso_fisico()
            pasos_actuales = 0
            break

    motor_off()
    print("-> MOVIMIENTO FINALIZADO.")
    try:
        client.publish(TOPIC_STATUS, "Cortina reubicada al {}%".format(porcentaje_objetivo))
    except:
        pass

def calibrar_inicial():
    global pasos_actuales, pasos_totales
    print("Iniciando secuencia de calibración inicial...")
    motor_on()
    dir_pin.value(0) 
    
    contador = 0
    while hall_0.value() == 1:
        dar_paso_fisico_calibracion()
        contador += 1
        if contador > 30000:
            print("[ALERTA] Calibración abortada por exceso de pasos.")
            break
    
    for _ in range(40): dar_paso_fisico_calibracion()
            
    motor_off()
    pasos_totales = contador 
    pasos_actuales = 0        
    print("[Calibración OK] Recorrido máximo medido: {} pasos.".format(pasos_totales))

# --- 5. RECEPCIÓN DE COMANDOS DESDE NODE-RED ---
def al_recibir_mqtt(topic, msg):
    global modo
    topico = topic.decode('utf-8')
    payload = msg.decode('utf-8').strip()
    
    # Esto te va a mostrar en Thonny SI ENTRA CUALQUIER COSA de la web
    print("\n[INTERRUPCIÓN MQTT] Llegó algo al bróker!")
    print("Tópico: {} | Mensaje: {}".format(topico, payload))
    
    if topico == TOPIC_MODO:
        modo = payload
        print("-> Modo cambiado a: [{}]".format(modo))
        
    elif topico == TOPIC_COMANDO and modo == "manual":
        if payload == "ABRIR":
            viajar_a_porcentaje(100)
        elif payload == "CERRAR":
            viajar_a_porcentaje(0)
            
    elif topico == TOPIC_POSICION and modo == "manual":
        try:
            porcentaje = int(payload)
            viajar_a_porcentaje(porcentaje)
        except Exception as e:
            print("Error al procesar el valor del slider:", e)

# --- 6. SECUENCIA DE ARRANQUE ---
motor_off()
calibrar_inicial() 
conectar_wifi()

client = MQTTClient(CLIENT_ID, MQTT_BROKER)
client.set_callback(al_recibir_mqtt)
try:
    client.connect()
    client.subscribe(TOPIC_MODO)
    client.subscribe(TOPIC_COMANDO)
    client.subscribe(TOPIC_POSICION)
    print("[MQTT OK] Conexión establecida de forma exitosa.")
except Exception as e:
    print("[MQTT ERR] Error al conectar:", e)

ultimo_envio = utime.ticks_ms()
print("\n--- LUFLEX RUNNING (MODO PROTEGIDO) ---")

# --- 7. BUCLE PRINCIPAL ---
while True:
    # Atajar los comandos de forma obligatoria e inmediata
    try:
        client.check_msg()
    except:
        pass
    
    # Lógica Automática mediante LDR (Solo corre si cambiás el modo en la web)
    if modo in ["auto1", "auto2"]:
        luz = (ldr1.read() + ldr2.read() + ldr3.read()) / 3
        
        if modo == "auto1":
            if luz < 1800: sug = 0        
            elif 1800 <= luz < 3400: sug = 50  
            else: sug = 100               
        else: 
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
                viajar_a_porcentaje(sug)
                contador_estabilidad = 0
        else:
            contador_estabilidad = 0
            
    # Enviar telemetría LDR cada 1 segundo sin interrumpir
    if utime.ticks_diff(utime.ticks_ms(), ultimo_envio) >= 1000:
        luz_actual = int((ldr1.read() + ldr2.read() + ldr3.read()) / 3)
        paquete_ldr = {"promedio": luz_actual}
        try:
            client.publish(TOPIC_SENSORES, json.dumps(paquete_ldr))
            print("[Telemetría] Transmitiendo LDR: {}".format(luz_actual))
        except:
            pass
        ultimo_envio = utime.ticks_ms()
        
    utime.sleep_ms(10)