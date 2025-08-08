"""
Utilidades y configuración para el BMS Generator
"""

import configparser
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AppConfig:
    """Configuración de la aplicación"""
    # Configuración de ventana
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    
    # Directorios
    last_project_dir: str = ""
    last_export_dir: str = ""
    
    # Configuración del editor
    show_grid: bool = True
    snap_to_grid: bool = True
    auto_save: bool = True
    auto_save_interval: int = 300  # segundos
    
    # Configuración BMS
    default_mapset_name: str = "MAPSET01"
    default_map_mode: str = "INOUT"
    default_map_lang: str = "COBOL"
    default_map_term: str = "3270-2"
    default_map_storage: str = "AUTO"
    
    # Colores del editor visual
    grid_color: tuple = (100, 100, 100, 255)
    input_field_color: tuple = (0, 255, 0, 100)
    output_field_color: tuple = (0, 0, 255, 100)
    label_field_color: tuple = (255, 255, 0, 100)
    protected_field_color: tuple = (128, 128, 128, 100)


class Config:
    """Manejador de configuración de la aplicación"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_file()
        self.config = configparser.ConfigParser()
        self.app_config = AppConfig()
        
        # Cargar configuración
        self.load()
        
    def _get_default_config_file(self) -> str:
        """Obtiene la ruta del archivo de configuración por defecto"""
        # Usar directorio home del usuario
        home_dir = Path.home()
        config_dir = home_dir / ".pybms"
        
        # Crear directorio si no existe
        config_dir.mkdir(exist_ok=True)
        
        return str(config_dir / "config.ini")
        
    def load(self) -> bool:
        """Carga la configuración desde archivo"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
                return True
            else:
                return True
                
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            return False
