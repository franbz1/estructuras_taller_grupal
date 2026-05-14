# Simulador de planificación de procesos (caso de estudio)

## Caso de estudio

Se modela un **núcleo simplificado** donde varios procesos compiten por la CPU bajo **Round Robin (RR)**, realizan **rafagas de CPU** y se **bloquean en E/S** (disco, red, impresora) antes de volver a la cola de listos. El objetivo pedagógico es **ver en acción cuatro estructuras de datos propias** que sostienen el estado del sistema: sin ellas no hay tabla de PCBs, anillo de listos, seguimiento de syscalls ni colas de dispositivos.

## Proyecto

- **Lenguaje:** Python 3.10+ (código y comentarios del repositorio en inglés).
- **Núcleo:** `OSSimulator` integra tabla de PCBs, planificador RR, gestor de E/S y bitácora de eventos.
- **Cargas de trabajo:** planes deterministas (`cpu` / `io`) definidos en tuplas; la demo en consola y la UI usan el mismo escenario de varios procesos concurrentes.
- **Interfaz gráfica (opcional):** Tkinter muestra en tiempo real **PCB**, **anillo RR**, **colas por dispositivo** y **log** de eventos; informe vía `generate_report()`.

### Estructuras implementadas

| Estructura | Rol en el simulador |
|------------|---------------------|
| `PCBTable` (arreglo fijo) | Reserva y consulta de PCBs por PID |
| Lista circular doble | Cola de **READY** y recorrido del cursor RR |
| `CallStack` | Registro de contexto en bloqueos por syscall |
| `IOQueue` | Espera FIFO por dispositivo de E/S |

### Ejecución

```bash
python main.py
```

Interfaz gráfica (biblioteca estándar):

```bash
python ui_main.py
```

### Organización del repositorio

- `data_structures/` — ADTs anteriores.
- `models/` — `Process`, dispositivos, enums.
- `simulator/` — planificación, E/S y `OSSimulator`.
- `utils/` — registro estructurado de la línea de tiempo.
- `ui/` — ventana Tkinter sobre el mismo motor.

### Colaboración

Los commits del curso pueden rotar autoría con `git -c user.name=... -c user.email=...` para reflejar a cada integrante en el historial.
