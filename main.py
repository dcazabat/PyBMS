#!/usr/bin/env python3
"""
PyBMS - Python BMS Generator

Punto de entrada principal de la aplicación
"""

import sys
import os
from pathlib import Path

# Añadir src al path para imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.gui import BMSGeneratorApp


def main():
    """Función principal para ejecutar la aplicación"""
    try:
        app = BMSGeneratorApp()
        app.run()
    except Exception as e:
        print(f"Error al ejecutar la aplicación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
