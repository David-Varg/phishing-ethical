# 📡 Lab: Phishing, Telemetría y Aburrimiento

Este es un proyecto personal en **fase de desarrollo** que surgió básicamente por aburrimiento y curiosidad técnica. El objetivo no fue crear una interfaz web perfecta (el frontend es lo de menos), sino explorar qué tanta información se puede extraer de un dispositivo cuando alguien hace clic en un enlace.

> **⚠️ AVISO:** Este proyecto es una Prueba de Concepto (PoC) con fines de aprendizaje sobre ciberseguridad. No lo uses para hacer el mal. El autor no se hace responsable de cómo decidas usar este código.

---

## 🛠️ Enfoque del Proyecto
A diferencia de otros proyectos, aquí no me enfoqué en que la página de "Instagram" se vea perfecta. El verdadero trabajo está "bajo el capó":

* **Fingerprinting Agresivo:** Uso de `Canvas API` para generar un ID único del dispositivo basado en el renderizado de la GPU.
* **Extracción de Sensores:** Captura de acelerómetro (para saber si el usuario camina o tiene el móvil en la mesa), sensores de luz y estado de batería.
* **Detección de "Mentiras" (VPN):** El servidor compara la zona horaria del navegador con la ubicación de la IP. Si no coinciden, lanza una alerta de posible VPN.
* **Ingeniería Social Técnica:** Un modal de "Verificación de Seguridad" que condiciona el acceso a que el usuario entregue su GPS real.

## 🚀 Características Técnicas
* **Backend:** Python con un servidor HTTP base (sin frameworks pesados).
* **Notificaciones:** Integración directa con la API de Telegram para recibir reportes instantáneos.
* **Persistencia:** Base de datos ligera en JSON para auditoría local.
* **Túnel:** Configuración automática con `cloudflared` para obtener HTTPS y saltar firewalls.

## Hallazgos Actuales
Durante el desarrollo, me di cuenta de que:
1.  La ubicación por IP es muy poco confiable. Por eso el GPS real es el "santo grial".
2.  Muchos navegadores están empezando a bloquear la API de batería o sensores de luz por razones de privacidad, lo que devuelve valores por defecto.

## 🔧 Instalación Rápida
Si quieres probarlo en tu propio entorno:

1.  Clona esto: `git clone https://github.com/David-Varg/phishing-ethical.git`
2.  Crea un archivo `.env` con tu `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID`.
3.  Ejecuta: `python server.py` (o usa el alias que configuré si estás en Linux).

---

**Proyecto en desarrollo constante.** Si el frontend se ve feo, es porque no le dí mucha vuelta a eso.
