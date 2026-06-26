# Luflex - Infraestructura Base de Comunicación (Docker IoT)

Este repositorio contiene la configuración empaquetada en Docker para desplegar de forma inmediata la infraestructura de red, el bróker MQTT y el panel de control (Dashboard) del proyecto **Luflex** (Sistema Automático de Cortinas Inteligentes). 

El entorno está diseñado con volúmenes lógicos y configuraciones universales, lo que garantiza que funcione de forma idéntica tanto en la arquitectura **ARM** de una Raspberry Pi (entorno de desarrollo del proyecto) como en arquitecturas **x86/AMD64** de computadoras personales (Windows, macOS o Linux).

---

## 🛠️ Requisitos Previos

Antes de inicializar el entorno, asegúrese de tener instalado:
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (en Windows o macOS) o **Docker & Docker Compose** (en Linux / Raspberry Pi OS).

---

## 🚀 Arquitectura del Entorno

El despliegue se compone de dos servicios interconectados dentro de una red puente aislada (`luflex_net`):

1. **`broker_mqtt` (Eclipse Mosquitto)**: Servidor de mensajería encargado de centralizar el tráfico de datos. Está configurado para escuchar de forma pública en la red local a través del puerto `1883` con acceso anónimo habilitado, permitiendo el acople directo del hardware físico (ESP32) y de Node-RED.
2. **`nodered_luflex` (Node-RED)**: Motor de flujos y servidor del Dashboard web (mapeado en el puerto `1880`). Utiliza persistencia de datos indexada en volúmenes de Docker, por lo que los flujos y las configuraciones no se pierden al reiniciar o detener los contenedores. Este podras verlo reflejado en http://localhost:1880/ui

---

## 📦 Estructura del Repositorio

```text
luflex-docker/
├── docker-compose.yml       # Definición e interconexión de los servicios
├── README.md                # Guía de despliegue rápido
├── flujo_nodered.json       # Exportación del flujo/Dashboard de Node-RED
└── mosquitto/
    └── config/
        └── mosquitto.conf   # Configuración de accesos del bróker MQTT
