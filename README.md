# 🏠 Luflex IoT - Infraestructura de Control MQTT

**Autor:** Facundo Boide  
**Materia / Comisión:** Ingenieria en computacion II (IC2) - Ingeniería en Computación  

---

## 📌 Descripción del Proyecto

Este repositorio contiene la arquitectura de infraestructura IoT para el sistema de automatización de cortina **Luflex**. El proyecto implementa una solución en contenedores para el Bróker MQTT, la interfaz visual y lógica de control en Node-RED, y un simulador en Python que replica el comportamiento del hardware **ESP32** para permitir pruebas completas sin necesidad de dispositivos físicos.

---

## 🛠️ Tecnologías y Versiones Utilizadas

| Componente | Tecnología | Versión | Rol en el Sistema |
| :--- | :--- | :--- | :--- |
| **Contenedor Bróker** | Eclipse Mosquitto | `2.0.18` | Gestor de mensajería Pub/Sub MQTT |
| **Contenedor Dashboard** | Node-RED | `3.1.9` | Orquestación de lógica e interfaz de usuario |
| **Interfaz Gráfica** | node-red-dashboard | `3.6.6` | Panel web interactivo (`/ui`) |
| **Simulador de Hardware**| Python / paho-mqtt | `3.x` / `1.6.1+` | Reemplazo/Simulación del firmware ESP32 |
| **Entorno de Despliegue**| Docker & Docker Compose | Engine `20.10+` | Virtualización y aislamiento de servicios |

---

## 📡 Matriz de Tópicos MQTT

| Tópico | Emisor (Publisher) | Receptor (Subscriber) | Formato / Payload | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `facu/luflex/ldr` | Simulador ESP32 | Node-RED | JSON: `{"promedio": 2150}` | Telemetría analógica del sensor de luz LDR (0-4095). |
| `facu/luflex/status` | Simulador ESP32 | Node-RED | String: `"Cortina reubicada al 50%"` | Confirmaciones de movimiento y estado de respuesta. |
| `facu/luflex/modo` | Node-RED | Simulador ESP32 | String: `"auto1"`, `"auto2"`, `"manual"` | Selección del modo de operación del sistema. |
| `facu/luflex/comando` | Node-RED | Simulador ESP32 | String: `"ABRIR"`, `"CERRAR"` | Comandos directos de apertura/cierre (solo en modo `manual`). |
| `facu/luflex/posicion` | Node-RED | Simulador ESP32 | String / Int: `"0"` a `"100"` | Ajuste porcentual de la cortina (solo en modo `manual`). |

---

## 🚀 Guía de Despliegue y Verificación

## Requisitos Previos
* Tener instalado **Docker** y **Docker Compose**.
* Tener instalado **Python 3** con la librería `paho-mqtt`:
  ```bash
  pip install paho-mqtt


## ⚡ Ejecución Rápida (TL;DR)

Si querés probar el proyecto inmediatamente en un clon limpio, ejecutá en tu terminal:

```bash
# 1. Clonar e ingresar al proyecto
git clone https://github.com/Facundo-Boide/202607-IC2-boide
cd 202607-IC2-boide

# 2. Levantar la infraestructura (Broker MQTT + Node-RED)
docker compose up -d

# 3. Ejecutar el simulador del ESP32
python simulador_esp32.py ( En consola apareceran los datos enviados y datos recibidos )

Ctrl+C para detener scrip

#4. El Dashboard y Node-Red
Dashboard "Localhost:1880/ui"
Node-Red "Localhost:1880"

#5. detener y limpiar entorno
Broker-Node-red docker compose down

