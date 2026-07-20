# Arquitectura y Configuración del Sistema de Audio

## Descripción

El sistema de alertas de DriverDrowsGuard tiene como objetivo advertir al conductor cuando se detectan signos de somnolencia mediante mensajes de voz generados automáticamente. El módulo de audio se integra con el sistema de detección para emitir alertas oportunas cuando los valores de EAR (Eye Aspect Ratio) y MOR (Mouth Opening Ratio) superan los umbrales establecidos.

# Arquitectura del Sistema

El flujo de funcionamiento del sistema es el siguiente:

```
Webcam
   │
   ▼
Captura de video
   │
   ▼
MediaPipe FaceMesh
   │
   ▼
Cálculo de EAR y MOR
   │
   ▼
Evaluación de umbrales
   │
   ▼
Sistema de Alertas
   │
   ▼
Motor de voz (pyttsx3 / espeak)
   │
   ▼
Reproducción del mensaje al conductor
```


# Configuración del Audio

## Windows

En Windows el sistema utiliza la librería **pyttsx3**, la cual hace uso del motor de voz SAPI5 integrado en el sistema operativo.

### Requisitos

- Python 3.11 o superior.
- Librería pyttsx3 instalada.

### Instalación

```bash
pip install pyttsx3
```

No es necesario instalar software adicional, ya que Windows incorpora el motor de síntesis de voz.


## Linux

En Linux la síntesis de voz utiliza **espeak** como motor principal.

### Instalación

```bash
sudo apt update
sudo apt install espeak
pip install pyttsx3
```

Es importante verificar que espeak se encuentre correctamente instalado antes de ejecutar el sistema.


# Calibración de Umbrales

## EAR (Eye Aspect Ratio)

El EAR permite determinar el nivel de apertura de los ojos.

Cuando el valor del EAR permanece por debajo del umbral durante varios cuadros consecutivos, el sistema interpreta que el conductor presenta signos de somnolencia y genera una alerta de voz.


## MOR (Mouth Opening Ratio)

El MOR mide el grado de apertura de la boca.

Si el valor supera el umbral configurado durante un tiempo determinado, el sistema identifica un posible bostezo y activa una alerta preventiva.


# Funcionamiento General

1. La cámara captura el video en tiempo real.
2. MediaPipe detecta los puntos faciales.
3. Se calculan los valores de EAR y MOR.
4. El sistema compara dichos valores con los umbrales configurados.
5. Si se detecta fatiga o somnolencia, se genera una alerta mediante el motor de voz.
6. El conductor recibe una advertencia auditiva para mantener la atención.


# Buenas Prácticas

- Ajustar los umbrales de EAR y MOR según las condiciones de iluminación.
- Verificar el correcto funcionamiento del motor de voz antes de iniciar el monitoreo.
- Mantener actualizadas las dependencias del proyecto.
- Realizar pruebas tanto en Windows como en Linux para garantizar la compatibilidad del sistema.