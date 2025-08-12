"""
app.py: Clase principal BMSGeneratorApp para PyBMS
"""

import dearpygui.dearpygui as dpg
from typing import Optional, List
import os
from pathlib import Path
import sys

# Añadir src al path para imports
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from models import BMSProject, BMSMap, BMSField, FieldType, FieldAttribute
from bms import BMSGenerator
from utils import Config

class BMSGeneratorApp:
    """Aplicación principal del BMS Generator"""
    
    def __init__(self):
        self.current_project: Optional[BMSProject] = None
        self.current_map: Optional[BMSMap] = None
        self.current_file_path: Optional[str] = None  # Ruta del archivo BMS actual
        self.bms_generator = BMSGenerator()
        self.config = Config()
        self.should_exit = False  # Control para salir del loop
        
        # Estado de la GUI
        self.selected_field_index: int = -1
        self.selected_field: Optional[BMSField] = None
        self.field_selectables: dict = {}  # Para rastrear elementos selectables del árbol
        
        # Estado del arrastre
        self.is_dragging: bool = False
        self.drag_start_pos: tuple = (0, 0)
        self.drag_offset: tuple = (0, 0)
        
        # Dimensiones del canvas
        self.canvas_width = 800
        self.canvas_height = 480
        self.cell_width = self.canvas_width / 80
        self.cell_height = self.canvas_height / 24
        
        # Configurar DearPyGUI
        dpg.create_context()
        self.setup_fonts()
        self.create_main_window()
        
    def setup_fonts(self):
        """Configura las fuentes para la aplicación"""            
        # Configuración básica de viewport
        dpg.create_viewport(
            title="PyBMS - BMS Generator",
            width=1500,
            height=800,
            min_width=800,
            min_height=600
        )
        
    def run(self):
        """Ejecuta la aplicación"""
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        
        # Configurar callback para interceptar cierre del viewport
        dpg.set_exit_callback(self._on_window_close)
        
        # Usar el método estándar de DearPyGUI
        dpg.start_dearpygui()
        dpg.destroy_context()
        
    def _on_window_close(self):
        """Callback que se ejecuta cuando se intenta cerrar la ventana"""
        # Si ya se confirmó la salida, permitir el cierre
        if self.should_exit:
            return True
            
        # Si no se ha confirmado, mostrar diálogo y prevenir cierre
        self.exit_app()
        return False  # Prevenir el cierre hasta que se confirme
        
    def update_status(self, message: str):
        """Actualiza la barra de estado"""
        dpg.set_value("status_text", message)
        
    # Métodos delegados a submódulos
    def create_main_window(self):
        from .ui import create_main_window
        create_main_window(self)
        
    def create_visual_editor(self):
        from .ui import create_visual_editor
        create_visual_editor(self)
        
    def create_properties_panel(self):
        from .ui import create_properties_panel
        create_properties_panel(self)
        
    def draw_screen_grid(self):
        from .ui import draw_screen_grid
        draw_screen_grid(self)
        
    def draw_field_on_canvas(self, field):
        from .ui import draw_field_on_canvas
        draw_field_on_canvas(self, field)
        
    def update_visual_editor(self):
        from .ui import update_visual_editor
        update_visual_editor(self)
        
    def update_bms_code_display(self):
        from .ui import update_bms_code_display
        update_bms_code_display(self)
        
    def display_bms_code_with_colors(self, bms_code):
        from .ui import display_bms_code_with_colors
        display_bms_code_with_colors(self, bms_code)
        
    def create_colored_line_monospace(self, line, line_tag):
        from .ui import create_colored_line_monospace
        create_colored_line_monospace(self, line, line_tag)
        
    def add_colored_text_segments(self, text, colors):
        from .ui import add_colored_text_segments
        add_colored_text_segments(self, text, colors)
        
    # Callbacks delegados
    def save_bms(self):
        from .callbacks import save_bms
        save_bms(self)
        
    def save_bms_as(self):
        from .callbacks import save_bms_as
        save_bms_as(self)
        
    def open_project(self):
        from .callbacks import open_project
        open_project(self)
        
    def new_project(self):
        from .callbacks import new_project
        new_project(self)
        
    def new_map(self):
        from .callbacks import new_map
        new_map(self)
        
    def new_field(self):
        from .callbacks import new_field
        new_field(self)
        
    def export_to_json(self):
        from .callbacks import export_to_json
        export_to_json(self)
        
    def import_bms(self):
        from .callbacks import import_bms
        import_bms(self)
        
    def export_bms(self):
        from .callbacks import export_bms
        export_bms(self)
        
    def apply_field_changes(self):
        from .callbacks import apply_field_changes
        apply_field_changes(self)
        
    def apply_field_changes_with_confirmation(self):
        from .callbacks import apply_field_changes_with_confirmation
        apply_field_changes_with_confirmation(self)
        
    def show_about(self):
        from .callbacks import show_about
        show_about(self)
        
    def exit_app(self):
        from .callbacks import exit_app
        exit_app(self)
        
    # Métodos de parsing delegados
    def _parse_bms_content(self, bms_map, content):
        from .parsing import parse_bms_content
        parse_bms_content(self, bms_map, content)
        
    def _parse_field_definition(self, bms_map, line):
        from .parsing import parse_field_definition
        parse_field_definition(self, bms_map, line)
        
    def _extract_field_name(self, line):
        from .parsing import extract_field_name
        return extract_field_name(self, line)
        
    def _extract_pos(self, line):
        from .parsing import extract_pos
        return extract_pos(self, line)
        
    def _extract_length(self, line):
        from .parsing import extract_length
        return extract_length(self, line)
        
    def _extract_initial(self, line):
        from .parsing import extract_initial
        return extract_initial(self, line)
        
    def _determine_field_type(self, line, initial_value):
        from .parsing import determine_field_type
        return determine_field_type(self, line, initial_value)
        
    def _extract_attributes(self, line):
        from .parsing import extract_attributes
        return extract_attributes(self, line)
        
    def _extract_color(self, line):
        from .parsing import extract_color
        return extract_color(self, line)
        
    def _extract_hilight(self, line):
        from .parsing import extract_hilight
        return extract_hilight(self, line)
        
    # Métodos utilitarios delegados
    def _is_valid_bms_content(self, content):
        from .utils import is_valid_bms_content
        return is_valid_bms_content(self, content)
        
    def _sanitize_name_for_cobol(self, name):
        from .utils import sanitize_name_for_cobol
        return sanitize_name_for_cobol(self, name)
        
    def get_bms_code_content(self):
        from .utils import get_bms_code_content
        return get_bms_code_content(self)
        
    # Métodos de UI adicionales
    def update_project_tree(self):
        from .ui import update_project_tree
        update_project_tree(self)
        
    def update_map_properties(self):
        from .ui import update_map_properties
        update_map_properties(self)
        
    def update_field_properties(self, field):
        from .ui import update_field_properties
        update_field_properties(self, field)
        
    def deselect_field(self):
        from .ui import deselect_field
        deselect_field(self)
        
    def select_field(self, field_name):
        from .ui import select_field
        select_field(self, field_name)
    
    # Callbacks adicionales de navegación y eventos
    def on_project_tree_selection(self, sender, app_data):
        from .callbacks import on_project_tree_selection
        on_project_tree_selection(self, sender, app_data)
        
    def on_project_tree_double_click(self, sender, app_data):
        from .callbacks import on_project_tree_double_click
        on_project_tree_double_click(self, sender, app_data)
        
    def on_visual_editor_click(self, sender, app_data):
        from .callbacks import on_visual_editor_click
        on_visual_editor_click(self, sender, app_data)
        
    def on_visual_editor_double_click(self, sender, app_data):
        from .callbacks import on_visual_editor_double_click
        on_visual_editor_double_click(self, sender, app_data)
        
    def on_visual_editor_right_click(self, sender, app_data):
        from .callbacks import on_visual_editor_right_click
        on_visual_editor_right_click(self, sender, app_data)
        
    def apply_map_changes(self):
        from .callbacks import apply_map_changes
        apply_map_changes(self)
        
    def apply_map_changes_with_confirmation(self):
        from .callbacks import apply_map_changes_with_confirmation
        apply_map_changes_with_confirmation(self)
        
    def validate_current_map(self):
        from .callbacks import validate_current_map
        validate_current_map(self)
        
    def generate_preview(self):
        from .callbacks import generate_preview
        generate_preview(self)
        
    def delete_selected_field(self):
        from .callbacks import delete_selected_field
        delete_selected_field(self)
        
    def duplicate_selected_field(self):
        from .callbacks import duplicate_selected_field
        duplicate_selected_field(self)
        
    def handle_keyboard_shortcuts(self, sender, app_data):
        from .callbacks import handle_keyboard_shortcuts
        handle_keyboard_shortcuts(self, sender, app_data)
        
    def handle_global_mouse_click(self, sender, app_data):
        from .callbacks import handle_global_mouse_click
        handle_global_mouse_click(self, sender, app_data)


