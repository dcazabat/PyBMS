"""
Ventana principal del BMS Generator usando DearPyGUI
"""

import dearpygui.dearpygui as dpg
from typing import Optional, List
import os
from pathlib import Path

import sys
import os
from pathlib import Path

# Añadir src al path para imports
src_path = Path(__file__).parent.parent
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
        
    def create_main_window(self):
        """Crea la ventana principal de la aplicación"""
        
        with dpg.window(label="PyBMS - BMS Generator", tag="main_window"):
            
            # Barra de menú
            with dpg.menu_bar():
                with dpg.menu(label="Archivo"):
                    # Elementos básicos que NO están en botones
                    dpg.add_menu_item(label="Guardar Como...", callback=self.save_bms_as)
                    dpg.add_separator()
                    dpg.add_menu_item(label="Exportar a JSON", callback=self.export_to_json)
                    dpg.add_menu_item(label="Importar BMS", callback=self.import_bms)
                    dpg.add_separator()
                    dpg.add_menu_item(label="Salir", callback=self.exit_app)
                    
                # Comentar menú Editar ya que sus funciones están en botones
                # with dpg.menu(label="Editar"):
                #     dpg.add_menu_item(label="Nuevo Mapa", callback=self.new_map)  # Ya está en botón
                #     dpg.add_menu_item(label="Nuevo Campo", callback=self.new_field)  # Ya está en botón
                    
                # Comentar menú Herramientas ya que sus funciones están en botones  
                # with dpg.menu(label="Herramientas"):
                #     dpg.add_menu_item(label="Generar BMS", callback=self.generate_bms)  # Ya está en botón
                    
                # Comentar el menú Vista ya que las funciones no están implementadas
                # with dpg.menu(label="Vista"):
                #     dpg.add_menu_item(label="Editor Visual", callback=self.show_visual_editor)
                #     dpg.add_menu_item(label="Código BMS", callback=self.show_bms_code)
                #     dpg.add_menu_item(label="Propiedades", callback=self.show_properties)
                    
                with dpg.menu(label="Ayuda"):
                    dpg.add_menu_item(label="Acerca de", callback=self.show_about)
            
            # Barra de herramientas
            with dpg.group(horizontal=True):
                # Botones de archivo - azul
                with dpg.theme() as nuevo_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 130, 180, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (100, 149, 237, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 90, 140, 255))
                dpg.add_button(label="[+] Nuevo", callback=self.new_project)
                dpg.bind_item_theme(dpg.last_item(), nuevo_theme)
                
                with dpg.theme() as abrir_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 130, 180, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (100, 149, 237, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 90, 140, 255))
                dpg.add_button(label="[O] Abrir", callback=self.open_project)
                dpg.bind_item_theme(dpg.last_item(), abrir_theme)
                
                with dpg.theme() as guardar_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (34, 139, 34, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 205, 50, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (20, 100, 20, 255))
                dpg.add_button(label="[S] Guardar", callback=self.save_bms)
                dpg.bind_item_theme(dpg.last_item(), guardar_theme)
                
                dpg.add_separator()
                
                # Botón aplicar cambios - naranja
                with dpg.theme() as aplicar_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (255, 140, 0, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 165, 0, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (205, 110, 0, 255))
                dpg.add_button(label="[*] Aplicar Cambios", callback=self.apply_field_changes_with_confirmation)
                dpg.bind_item_theme(dpg.last_item(), aplicar_theme)
                
                dpg.add_separator()
                
                # Botones de creación - púrpura
                with dpg.theme() as mapa_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (138, 43, 226, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (160, 70, 255, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 20, 180, 255))
                dpg.add_button(label="[M] Nuevo Mapa", callback=self.new_map)
                dpg.bind_item_theme(dpg.last_item(), mapa_theme)
                
                with dpg.theme() as campo_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (138, 43, 226, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (160, 70, 255, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 20, 180, 255))
                dpg.add_button(label="[F] Nuevo Campo", callback=self.new_field)
                dpg.bind_item_theme(dpg.last_item(), campo_theme)
                
                dpg.add_separator()
                
                # Botón generar - rojo
                with dpg.theme() as generar_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (220, 20, 60, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 69, 0, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (178, 34, 34, 255))
                dpg.add_button(label="[G] Generar BMS", callback=self.generate_bms)
                dpg.bind_item_theme(dpg.last_item(), generar_theme)
            
            dpg.add_separator()
            
            # Panel principal dividido
            with dpg.group(horizontal=True):
                
                # Panel izquierdo - Explorador de proyecto
                with dpg.child_window(width=300, height=-1, tag="project_explorer"):
                    dpg.add_text("Explorador de Proyecto")
                    dpg.add_separator()
                    
                    # Árbol del proyecto
                    with dpg.tree_node(label="Proyecto", default_open=True, tag="project_tree"):
                        dpg.add_text("(Sin proyecto)")
                        
                # Panel central - Editor
                with dpg.child_window(width=-300, height=-1, tag="main_editor"):
                    
                    # Pestañas del editor
                    with dpg.tab_bar(tag="editor_tabs"):
                        
                        # Pestaña del editor visual
                        with dpg.tab(label="Editor Visual", tag="visual_editor_tab"):
                            self.create_visual_editor()
                            
                        # Pestaña del código BMS
                        with dpg.tab(label="Código BMS", tag="bms_code_tab"):
                            dpg.add_input_text(
                                multiline=True,
                                width=-1,
                                height=-1,
                                tag="bms_code_text",
                                readonly=True
                            )
                
                # Panel derecho - Propiedades
                with dpg.child_window(width=280, height=-1, tag="properties_panel"):
                    dpg.add_text("Propiedades")
                    dpg.add_separator()
                    self.create_properties_panel()
            
            # Barra de estado
            with dpg.group(horizontal=True):
                dpg.add_text("Listo", tag="status_text")
                
    def create_visual_editor(self):
        """Crea el editor visual de mapas BMS"""
        with dpg.group():
            dpg.add_text("Editor Visual de Mapa BMS")
            dpg.add_separator()
            
            # Canvas para el mapa (simulando pantalla 24x80)
            with dpg.drawlist(width=self.canvas_width, height=self.canvas_height, tag="map_canvas"):
                # Dibujar grid de la pantalla
                self.draw_screen_grid()
                
    def create_properties_panel(self):
        """Crea el panel de propiedades"""
        with dpg.collapsing_header(label="Mapa", default_open=True):
            dpg.add_input_text(label="Nombre", tag="map_name_input")
            dpg.add_input_text(label="Mapset", tag="mapset_name_input") 
            dpg.add_combo(
                label="Modo",
                items=["INOUT", "IN", "OUT"],
                default_value="INOUT",
                tag="map_mode_combo"
            )
            dpg.add_combo(
                label="Lenguaje",
                items=["COBOL", "PLI", "ASM"],
                default_value="COBOL",
                tag="map_lang_combo"
            )
            
        with dpg.collapsing_header(label="Campo Seleccionado", default_open=True, tag="field_section_header"):
            dpg.add_input_text(label="Nombre", tag="field_name_input")
            dpg.add_input_int(label="Línea", tag="field_line_input", min_value=1, max_value=24)
            dpg.add_input_int(label="Columna", tag="field_column_input", min_value=1, max_value=80)
            dpg.add_input_int(label="Longitud", tag="field_length_input", min_value=1, max_value=80)
            dpg.add_combo(
                label="Tipo",
                items=[ft.value for ft in FieldType],
                tag="field_type_combo"
            )
            dpg.add_input_text(label="Valor inicial", tag="field_initial_input")
            
            # PICIN y PICOUT para campos INPUT/OUTPUT
            dpg.add_input_text(label="PICIN (entrada)", tag="field_picin_input", hint="Ej: 9(8)")
            dpg.add_input_text(label="PICOUT (salida)", tag="field_picout_input", hint="Ej: ZZ,ZZ9.99")
            
            # Color y Hilight
            dpg.add_combo(
                label="Color",
                items=["", "RED", "BLUE", "GREEN", "YELLOW", "TURQUOISE", "PINK", "NEUTRAL"],
                tag="field_color_combo"
            )
            dpg.add_combo(
                label="Hilight",
                items=["", "UNDERLINE", "BLINK", "REVERSE"],
                tag="field_hilight_combo"
            )
            
            # Atributos del campo
            dpg.add_text("Atributos:")
            for attr in FieldAttribute:
                dpg.add_checkbox(label=attr.value, tag=f"attr_{attr.value}")
                
            dpg.add_separator()
            
            # Botones de acción
            with dpg.group(horizontal=True):
                # Botón aplicar - verde
                with dpg.theme() as prop_aplicar_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (34, 139, 34, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 205, 50, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (20, 100, 20, 255))
                dpg.add_button(label="[*] Aplicar Cambios", callback=self.apply_field_changes, width=140)
                dpg.bind_item_theme(dpg.last_item(), prop_aplicar_theme)
                
                # Botón seleccionar - azul claro
                with dpg.theme() as prop_select_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 144, 255, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (70, 170, 255, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (10, 120, 200, 255))
                dpg.add_button(label="[>] Seleccionar Campo", callback=self.show_field_selector, width=140)
                dpg.bind_item_theme(dpg.last_item(), prop_select_theme)
            
        # Configurar handler para interceptar cierre de ventana
        with dpg.handler_registry():
            dpg.add_key_press_handler(dpg.mvKey_F4, callback=self._on_alt_f4)
                
    def _on_alt_f4(self):
        """Intercepta Alt+F4 para mostrar confirmación"""
        if dpg.is_key_down(dpg.mvKey_ModAlt):
            self.exit_app()
    def draw_screen_grid(self):
        """Dibuja la cuadrícula de la pantalla 24x80"""
        # Colores
        grid_color = (100, 100, 100, 255)  # Gris claro
        
        # Líneas verticales
        for i in range(81):  # 0 a 80
            x = i * self.cell_width
            dpg.draw_line(
                (x, 0), (x, self.canvas_height),
                color=grid_color,
                thickness=1 if i % 10 == 0 else 0.5,
                parent="map_canvas"
            )
            
        # Líneas horizontales  
        for i in range(25):  # 0 a 24
            y = i * self.cell_height
            dpg.draw_line(
                (0, y), (self.canvas_width, y),
                color=grid_color,
                thickness=1 if i % 5 == 0 else 0.5,
                parent="map_canvas"
            )
            
    def update_project_tree(self):
        """Actualiza el árbol del proyecto"""
        # Limpiar árbol existente
        dpg.delete_item("project_tree", children_only=True)
        # Limpiar referencias a selectables anteriores
        self.field_selectables.clear()
        
        if self.current_project:
            with dpg.tree_node(label=f"📁 {self.current_project.name}", parent="project_tree", default_open=True):
                with dpg.tree_node(label="📋 Mapas", default_open=True):
                    for bms_map in self.current_project.maps:
                        with dpg.tree_node(label=f"📄 {bms_map.name}", leaf=True):
                            for field in bms_map.fields:
                                selectable_id = dpg.add_selectable(
                                    label=f"🔢 {field.name}",
                                    callback=self._create_field_select_tree_callback(field),
                                    default_value=False
                                )
                                # Guardar referencia para poder deseleccionar después
                                self.field_selectables[field.name] = selectable_id
        else:
            dpg.add_text("(Sin proyecto)", parent="project_tree")
    
    # Callbacks para los menús y botones
    
    def new_project(self):
        """Crea un nuevo proyecto"""
        # Limpiar estado de selección anterior
        self.deselect_field()
        
        self.current_project = BMSProject(name="Nuevo Proyecto")
        self.current_map = None  # Limpiar mapa actual también
        self.current_file_path = None  # Limpiar archivo actual
        self.update_project_tree()
        self.update_status("Nuevo proyecto creado")
        
    def open_project(self):
        """Abre un proyecto existente"""
        # Verificar si ya existe un diálogo y eliminarlo
        if dpg.does_item_exist("open_project_dialog"):
            dpg.delete_item("open_project_dialog")
        
        # Crear diálogo de archivo para abrir (acepta cualquier extensión)
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            callback=self._open_project_callback,
            tag="open_project_dialog",
            width=700,
            height=400,
            default_path=".",
            modal=False
        ):
            # Solo usar el filtro "todos los archivos" para evitar problemas con extensiones
            dpg.add_file_extension(".*", color=(255, 255, 255, 255), custom_text="[Todos los archivos]")
            
    def _open_project_callback(self, sender, app_data):
        """Callback para cuando se selecciona un archivo"""
        try:
            # Limpiar el diálogo
            if dpg.does_item_exist("open_project_dialog"):
                dpg.delete_item("open_project_dialog")
                
            # Usar la ruta real del archivo desde selections en lugar de file_path_name
            file_path = None
            if "selections" in app_data and app_data["selections"]:
                # Tomar el primer archivo seleccionado
                file_path = list(app_data["selections"].values())[0]
            else:
                # Fallback al file_path_name si no hay selections
                file_path = app_data["file_path_name"]
                
            if file_path:
                self._load_project_from_file(file_path)
        except Exception as e:
            self.update_status(f"Error al abrir archivo: {e}")
            
    def _load_project_from_file(self, file_path: str):
        """Carga un proyecto desde un archivo"""
        try:
            file_extension = Path(file_path).suffix.lower()
            file_name = Path(file_path).name
            
            # Leer el contenido del archivo primero
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Intentar con diferentes codificaciones
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except Exception as e:
                    self.update_status(f"Error al leer archivo {file_name}: No se puede decodificar")
                    return
            
            # Verificar si el contenido parece ser BMS válido
            if self._is_valid_bms_content(content):
                # Cargar como archivo BMS
                self._load_bms_file_with_content(file_path, content)
            elif file_extension == ".json":
                # Cargar proyecto JSON
                self._load_json_project(file_path)
            else:
                # Mostrar alerta de que no es un mapa BMS válido
                self._show_invalid_bms_alert(file_name)
                return
                
            self.update_status(f"Archivo cargado: {file_name}")
            
        except Exception as e:
            self.update_status(f"Error al cargar archivo: {e}")
    
    def _is_valid_bms_content(self, content: str) -> bool:
        """Verifica si el contenido parece ser un mapa BMS válido"""
        if not content or not content.strip():
            return False
        
        lines = content.split('\n')
        bms_indicators = 0
        has_mapset = False
        has_map = False
        has_fields = False
        
        # Buscar indicadores de que es un archivo BMS
        for line in lines:
            line_upper = line.strip().upper()
            
            # Ignorar líneas vacías y comentarios
            if not line_upper or line_upper.startswith('*'):
                continue
            
            # Buscar palabras clave específicas de BMS (más permisivo)
            if 'DFHMSD' in line_upper:
                has_mapset = True
                bms_indicators += 2  # DFHMSD es muy indicativo
            elif 'DFHMDI' in line_upper:
                has_map = True
                bms_indicators += 2  # DFHMDI es muy indicativo
            elif 'DFHMDF' in line_upper:
                has_fields = True
                bms_indicators += 1
            
            # Buscar patrones típicos de BMS
            if 'POS=' in line_upper:
                bms_indicators += 1
            if 'LENGTH=' in line_upper:
                bms_indicators += 1
            if 'ATTRB=' in line_upper:
                bms_indicators += 1
            if 'INITIAL=' in line_upper:
                bms_indicators += 1
            if 'PICIN=' in line_upper or 'PICOUT=' in line_upper:
                bms_indicators += 1
            
            # Buscar otros patrones BMS comunes
            if any(pattern in line_upper for pattern in ['TYPE=&SYSPARM', 'MODE=INOUT', 'MODE=IN', 'MODE=OUT', 'LANG=COBOL', 'LANG=PLI', 'CTRL=', 'SIZE=']):
                bms_indicators += 1
                
            # Buscar atributos BMS típicos
            if any(attr in line_upper for attr in ['ASKIP', 'PROT', 'UNPROT', 'NUM', 'BRT', 'NORM', 'DRK', 'IC', 'FSET']):
                bms_indicators += 1
                
            # Buscar colores BMS
            if any(color in line_upper for color in ['COLOR=RED', 'COLOR=BLUE', 'COLOR=YELLOW', 'COLOR=GREEN']):
                bms_indicators += 1
                
            # Buscar HILIGHT
            if 'HILIGHT=' in line_upper:
                bms_indicators += 1
        
        # Para ser considerado BMS válido necesitamos:
        # - Al menos 3 indicadores en total, O
        # - Al menos una definición DFHMSD/DFHMDI/DFHMDF
        is_valid = bms_indicators >= 3 or has_mapset or has_map or has_fields
        
        return is_valid
    
    def _show_invalid_bms_alert(self, file_name: str):
        """Muestra una alerta cuando el archivo no es un mapa BMS válido"""
        # Crear ventana de alerta
        with dpg.window(label="Archivo No Válido", width=400, height=200, modal=True, tag="invalid_bms_alert"):
            dpg.add_text("⚠️ Archivo no válido")
            dpg.add_separator()
            dpg.add_text(f"El archivo '{file_name}' no parece ser un mapa BMS válido.")
            dpg.add_text("")
            dpg.add_text("Un archivo BMS válido debe contener:")
            dpg.add_text("• Definiciones DFHMSD, DFHMDI o DFHMDF")
            dpg.add_text("• Posiciones (POS=) y atributos de campo")
            dpg.add_text("• Estructura de mapset y mapa")
            dpg.add_separator()
            
            # Botones
            with dpg.group(horizontal=True):
                # Botón cargar forzado - amarillo/naranja (advertencia)
                with dpg.theme() as warning_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (255, 193, 7, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 215, 0, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (218, 165, 32, 255))
                dpg.add_button(
                    label="[!] Cargar de todos modos",
                    callback=lambda: self._force_load_as_bms(file_name),
                    width=170
                )
                dpg.bind_item_theme(dpg.last_item(), warning_theme)
                
                # Botón cancelar - rojo
                with dpg.theme() as cancel_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (220, 53, 69, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 69, 0, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (178, 34, 34, 255))
                dpg.add_button(
                    label="[X] Cancelar",
                    callback=lambda: dpg.delete_item("invalid_bms_alert"),
                    width=120
                )
                dpg.bind_item_theme(dpg.last_item(), cancel_theme)
    
    def _force_load_as_bms(self, file_path: str):
        """Fuerza la carga de un archivo como BMS aunque no parezca válido"""
        try:
            dpg.delete_item("invalid_bms_alert")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self._load_bms_file_with_content(file_path, content)
            self.update_status(f"Archivo cargado forzadamente: {Path(file_path).name}")
        except Exception as e:
            self.update_status(f"Error al cargar archivo forzadamente: {e}")
            
    def _load_bms_file(self, file_path: str):
        """Carga un archivo BMS existente"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self._load_bms_file_with_content(file_path, content)
            
        except Exception as e:
            raise Exception(f"Error al cargar archivo BMS: {e}")
    
    def _load_bms_file_with_content(self, file_path: str, content: str):
        """Carga un archivo BMS con contenido ya leído"""
        try:
            # Limpiar estado de selección anterior
            self.deselect_field()
            
            # Guardar la ruta del archivo actual
            self.current_file_path = file_path
            
            # Crear un nuevo proyecto para el archivo BMS
            # Usar el nombre del archivo sin extensión, pero validar que sea un nombre válido
            file_name = Path(file_path).stem
            project_name = file_name if file_name else "PROYECTO_BMS"
            self.current_project = BMSProject(name=project_name)
            
            # Crear un mapa basado en el archivo BMS
            # Usar el nombre del archivo como base, asegurando que sea válido para COBOL
            map_name = self._sanitize_name_for_cobol(file_name) if file_name else "MAPA01"
            new_map = BMSMap(name=map_name, mapset_name="MAPSET01")
            
            # Parsear el contenido BMS básico
            self._parse_bms_content(new_map, content)
            
            self.current_project.add_map(new_map)
            self.current_map = new_map
            
            self.update_project_tree()
            self.update_map_properties()
            self.update_visual_editor()
            self.update_bms_code_display()
            
            # Validar el mapa cargado
            errors = self.bms_generator.validate_map(new_map)
            if errors:
                error_count = len(errors)
                self.update_status(f"Mapa cargado con {error_count} advertencia(s) de validación")
            else:
                self.update_status(f"Mapa BMS cargado y validado correctamente")
            
        except Exception as e:
            raise Exception(f"Error al procesar archivo BMS: {e}")
            
    def _sanitize_name_for_cobol(self, name: str) -> str:
        """Convierte un nombre de archivo a un nombre válido para COBOL/BMS"""
        # Convertir a mayúsculas
        clean_name = name.upper()
        
        # Reemplazar caracteres no válidos con guiones bajos
        import re
        clean_name = re.sub(r'[^A-Z0-9]', '_', clean_name)
        
        # Asegurar que empiece con letra
        if clean_name and not clean_name[0].isalpha():
            clean_name = 'M' + clean_name
            
        # Limitar longitud (máximo 8 caracteres para BMS)
        clean_name = clean_name[:8]
        
        # Si queda vacío, usar nombre por defecto
        if not clean_name:
            clean_name = "MAPA01"
            
        return clean_name
            
    def _load_json_project(self, file_path: str):
        """Carga un proyecto desde un archivo JSON"""
        try:
            import json
            from src.models import BMSProject, BMSMap, BMSField, FieldType, FieldAttribute
            
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Crear el proyecto
            project_name = project_data.get('name', 'Proyecto Sin Nombre')
            self.current_project = BMSProject(name=project_name)
            
            # Cargar los mapas
            for map_data in project_data.get('maps', []):
                bms_map = BMSMap(
                    name=map_data.get('name', 'MAPA_SIN_NOMBRE'),
                    mapset_name=map_data.get('mapset_name', 'MAPSET01')
                )
                
                # Establecer propiedades del mapa
                bms_map.size = map_data.get('size', bms_map.size)
                bms_map.lang = map_data.get('lang', bms_map.lang)
                
                # Cargar los campos
                for field_data in map_data.get('fields', []):
                    try:
                        # Crear el campo
                        field = BMSField(
                            name=field_data.get('name', 'CAMPO'),
                            line=field_data.get('line', 1),
                            column=field_data.get('column', 1),
                            length=field_data.get('length', 1)
                        )
                        
                        # Establecer tipo de campo
                        field_type_str = field_data.get('field_type', 'INPUT')
                        try:
                            field.field_type = FieldType(field_type_str)
                        except ValueError:
                            field.field_type = FieldType.INPUT
                        
                        # Establecer valor inicial
                        field.initial_value = field_data.get('initial_value', '')
                        
                        # Establecer atributos
                        attributes_list = field_data.get('attributes', [])
                        field.attributes = []
                        for attr_str in attributes_list:
                            try:
                                field.attributes.append(FieldAttribute(attr_str))
                            except ValueError:
                                pass  # Ignorar atributos inválidos
                        
                        bms_map.add_field(field)
                        
                    except Exception as e:
                        self.update_status(f"Error al cargar campo: {e}")
                        continue
                
                self.current_project.add_map(bms_map)
            
            # Establecer el primer mapa como actual si existe
            if self.current_project.maps:
                self.current_map = self.current_project.maps[0]
            else:
                self.current_map = None
            
            # Actualizar la interfaz
            self.update_project_tree()
            self.update_map_properties()
            self.update_visual_editor()
            self.update_bms_code_display()
            
            self.update_status(f"Proyecto JSON cargado: {project_name}")
            
        except json.JSONDecodeError as e:
            self.update_status(f"Error: El archivo no es un JSON válido - {e}")
        except Exception as e:
            self.update_status(f"Error al cargar proyecto JSON: {e}")
        
    def _parse_bms_content(self, bms_map: BMSMap, content: str):
        """Parsea el contenido de un archivo BMS completo"""
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Ignorar líneas vacías y comentarios
            if not line or line.startswith('*'):
                i += 1
                continue
                
            # Si contiene DFHMDF, procesar como campo
            if 'DFHMDF' in line:
                # Recopilar todas las líneas del campo (incluyendo continuaciones)
                field_lines = [line]
                
                # Mientras la línea actual termine en * hay continuación
                while line.endswith('*') and i + 1 < len(lines):
                    i += 1
                    line = lines[i].strip()
                    if line:  # Solo agregar líneas no vacías
                        field_lines.append(line)
                
                # Unir todas las líneas del campo y procesarlo
                full_field_line = self._join_continuation_lines(field_lines)
                self._parse_field_definition(bms_map, full_field_line)
                
            elif 'DFHMDI' in line:
                # Parsear propiedades del mapa
                self._parse_map_properties(bms_map, line)
                
            i += 1
            
    def _join_continuation_lines(self, lines: List[str]) -> str:
        """Une líneas de continuación BMS removiendo * y ajustando espacios"""
        if not lines:
            return ""
            
        result_parts = []
        for line in lines:
            # Remover * al final si existe
            clean_line = line.rstrip('*').strip()
            if clean_line:
                result_parts.append(clean_line)
                
        return ' '.join(result_parts)
                
    def _parse_map_properties(self, bms_map: BMSMap, line: str):
        """Parsea las propiedades del mapa desde DFHMDI"""
        try:
            # Extraer SIZE si está disponible
            if 'SIZE=' in line:
                size_start = line.find('SIZE=(') + 6
                size_end = line.find(')', size_start)
                if size_end != -1:
                    size_str = line[size_start:size_end]
                    if ',' in size_str:
                        rows_str, cols_str = size_str.split(',')
                        rows = int(rows_str.strip())
                        cols = int(cols_str.strip())
                        bms_map.size = (rows, cols)
        except:
            pass
            
    def _parse_field_definition(self, bms_map: BMSMap, line: str):
        """Parsea una definición de campo BMS mejorada"""
        try:
            # Determinar el nombre del campo
            field_name = self._extract_field_name(line)
            
            # Valores por defecto
            line_num = 1
            column = 1
            length = 1
            field_type = FieldType.LABEL
            initial_value = ""
            attributes = []
            
            # Extraer POS
            pos_match = self._extract_pos(line)
            if pos_match:
                line_num, column = pos_match
            
            # Extraer LENGTH
            length_match = self._extract_length(line)
            if length_match:
                length = length_match
                
            # Extraer INITIAL
            initial_match = self._extract_initial(line)
            if initial_match:
                initial_value = initial_match
                
            # Determinar tipo de campo
            field_type = self._determine_field_type(line, initial_value)
            
            # Extraer atributos
            attributes = self._extract_attributes(line)
            
            # Extraer COLOR
            color = self._extract_color(line)
            
            # Extraer HILIGHT
            hilight = self._extract_hilight(line)
            
            # Crear el campo solo si tiene información válida
            if line_num > 0 and column > 0 and length > 0:
                field = BMSField(
                    name=field_name,
                    line=line_num,
                    column=column,
                    length=length,
                    field_type=field_type,
                    initial_value=initial_value,
                    attributes=attributes,
                    color=color,
                    hilight=hilight
                )
                
                bms_map.add_field(field)
                
        except Exception as e:
            # Si hay error en el parseo, continuar con el siguiente campo
            pass
            
    def _extract_field_name(self, line: str) -> str:
        """Extrae el nombre del campo de una línea BMS"""
        try:
            # Buscar el patrón: NOMBRE DFHMDF
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'DFHMDF':
                    if i > 0:
                        # El nombre está antes de DFHMDF
                        potential_name = parts[i-1]
                        # Verificar que no sea un keyword BMS y que sea un nombre válido
                        if (potential_name not in ['', 'POS', 'LENGTH', 'ATTRB', 'INITIAL', 'PICIN', 'PICOUT', 'COLOR', 'HILIGHT'] 
                            and len(potential_name) <= 8 
                            and potential_name.replace('_', '').replace('-', '').isalnum()):
                            return potential_name
                    break
            
            # Si la línea empieza con un nombre seguido de espacios y DFHMDF
            line_trimmed = line.strip()
            if line_trimmed and not line_trimmed.startswith('DFHMDF'):
                # Buscar el primer token antes de DFHMDF
                first_word = line_trimmed.split()[0]
                if (first_word != 'DFHMDF' 
                    and len(first_word) <= 8 
                    and first_word not in ['POS', 'LENGTH', 'ATTRB', 'INITIAL', 'PICIN', 'PICOUT', 'COLOR', 'HILIGHT']
                    and first_word.replace('_', '').replace('-', '').isalnum()):
                    return first_word
            
            # Solo generar nombre automático si no hay nombre real
            pos_match = self._extract_pos(line)
            if pos_match:
                line_num, column = pos_match
                return f"FIELD_{line_num}_{column}"
            
            # Si no hay posición, usar índice
            field_count = len(self.current_map.fields) if self.current_map else 0
            return f"FIELD_{field_count + 1}"
        except Exception as e:
            return "UNNAMED_FIELD"
            
    def _extract_pos(self, line: str) -> tuple[int, int] | None:
        """Extrae la posición (línea, columna) de una línea BMS"""
        try:
            pos_idx = line.find('POS=(')
            if pos_idx != -1:
                pos_end = line.find(')', pos_idx)
                if pos_end != -1:
                    pos_str = line[pos_idx + 5:pos_end]
                    if ',' in pos_str:
                        line_num_str, column_str = pos_str.split(',')
                        line_num = int(line_num_str.strip())
                        column = int(column_str.strip())
                        return (line_num, column)
        except:
            pass
        return None
        
    def _extract_length(self, line: str) -> int:
        """Extrae la longitud de una línea BMS"""
        try:
            len_idx = line.find('LENGTH=')
            if len_idx != -1:
                # Buscar el valor después de LENGTH=
                remaining = line[len_idx + 7:]
                # Tomar hasta la primera coma o espacio
                len_str = ""
                for char in remaining:
                    if char.isdigit():
                        len_str += char
                    elif char in [',', ' ', ')']:
                        break
                    
                if len_str:
                    return int(len_str)
        except:
            pass
        return 1
        
    def _extract_initial(self, line: str) -> str:
        """Extrae el valor inicial de una línea BMS"""
        try:
            init_idx = line.find("INITIAL='")
            if init_idx != -1:
                start = init_idx + 9
                end = line.find("'", start)
                if end != -1:
                    return line[start:end]
        except:
            pass
        return ""
        
    def _determine_field_type(self, line: str, initial_value: str) -> FieldType:
        """Determina el tipo de campo basado en la línea BMS"""
        line_upper = line.upper()
        
        # Si tiene PICIN, es un campo de entrada
        if 'PICIN=' in line_upper:
            return FieldType.INPUT
            
        # Si tiene PICOUT pero no PICIN, es de salida
        if 'PICOUT=' in line_upper and 'PICIN=' not in line_upper:
            return FieldType.OUTPUT
            
        # Si tiene valor inicial, probablemente es una etiqueta
        if initial_value:
            return FieldType.LABEL
            
        # Si tiene ATTRB=UNPROT o similar, es desprotegido (tipo INPUT por defecto)
        if 'ATTRB=UNPROT' in line_upper or 'ATTRB=(UNPROT' in line_upper:
            return FieldType.INPUT
            
        # Por defecto, campos sin características especiales son etiquetas
        return FieldType.LABEL
        
    def _extract_attributes(self, line: str) -> list:
        """Extrae los atributos de una línea BMS"""
        attributes = []
        line_upper = line.upper()
        
        # Buscar atributos comunes
        if 'ASKIP' in line_upper:
            attributes.append(FieldAttribute.ASKIP)
        if 'PROT' in line_upper:
            attributes.append(FieldAttribute.PROT)
        if 'UNPROT' in line_upper:
            attributes.append(FieldAttribute.UNPROT)
        if 'NUM' in line_upper:
            attributes.append(FieldAttribute.NUM)
        if 'BRT' in line_upper:
            attributes.append(FieldAttribute.BRT)
        if 'NORM' in line_upper:
            attributes.append(FieldAttribute.NORM)
        if 'DRK' in line_upper:
            attributes.append(FieldAttribute.DRK)
        if 'IC' in line_upper:
            attributes.append(FieldAttribute.IC)
        if 'FSET' in line_upper:
            attributes.append(FieldAttribute.FSET)
            
        return attributes
        
    def _extract_color(self, line: str) -> Optional[str]:
        """Extrae el COLOR de una línea BMS"""
        try:
            line_upper = line.upper()
            if 'COLOR=' in line_upper:
                color_start = line_upper.find('COLOR=') + 6
                # Buscar hasta el siguiente delimitador (coma, paréntesis, espacio)
                color_end = color_start
                while color_end < len(line) and line[color_end] not in [',', ')', ' ', '\t']:
                    color_end += 1
                return line[color_start:color_end].strip()
        except:
            pass
        return None
        
    def _extract_hilight(self, line: str) -> Optional[str]:
        """Extrae el HILIGHT de una línea BMS"""
        try:
            line_upper = line.upper()
            if 'HILIGHT=' in line_upper:
                hilight_start = line_upper.find('HILIGHT=') + 8
                # Buscar hasta el siguiente delimitador (coma, paréntesis, espacio)
                hilight_end = hilight_start
                while hilight_end < len(line) and line[hilight_end] not in [',', ')', ' ', '\t']:
                    hilight_end += 1
                return line[hilight_start:hilight_end].strip()
        except:
            pass
        return None
        
    def export_to_json(self):
        """Exporta el proyecto actual a un archivo JSON"""
        if not self.current_project:
            self.update_status("No hay proyecto para exportar")
            return
            
        # Verificar si ya existe un diálogo y eliminarlo
        if dpg.does_item_exist("export_json_dialog"):
            dpg.delete_item("export_json_dialog")
            
        # Crear diálogo para exportar el proyecto
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            callback=self._export_json_callback,
            tag="export_json_dialog",
            width=700,
            height=400,
            default_path=".",
            default_filename=f"{self.current_project.name}.json"
        ):
            dpg.add_file_extension(".json", color=(0, 255, 255, 255), custom_text="[JSON]")
            dpg.add_file_extension(".*", color=(255, 255, 255, 255), custom_text="[Todos los archivos]")
            
    def _export_json_callback(self, sender, app_data):
        """Callback para exportar el proyecto a JSON"""
        try:
            # Limpiar el diálogo
            if dpg.does_item_exist("export_json_dialog"):
                dpg.delete_item("export_json_dialog")
                
            if not self.current_project:
                self.update_status("Error: No hay proyecto para exportar")
                return
                
            file_path = app_data["file_path_name"]
            if file_path:
                # Asegurar que tenga extensión .json
                if not file_path.endswith('.json'):
                    file_path += '.json'
                    
                # Convertir el proyecto a JSON
                project_data = {
                    "name": self.current_project.name,
                    "maps": []
                }
                
                for bms_map in self.current_project.maps:
                    map_data = {
                        "name": bms_map.name,
                        "mapset_name": bms_map.mapset_name,
                        "size": bms_map.size,
                        "lang": bms_map.lang,
                        "fields": []
                    }
                    
                    for field in bms_map.fields:
                        field_data = {
                            "name": field.name,
                            "line": field.line,
                            "column": field.column,
                            "length": field.length,
                            "field_type": field.field_type.value,
                            "initial_value": field.initial_value,
                            "attributes": [attr.value for attr in field.attributes]
                        }
                        map_data["fields"].append(field_data)
                    
                    project_data["maps"].append(map_data)
                
                # Guardar el archivo JSON
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, indent=2, ensure_ascii=False)
                
                self.update_status(f"Proyecto exportado a JSON: {file_path}")
                
        except Exception as e:
            self.update_status(f"Error al exportar proyecto: {e}")
    
    def save_bms(self):
        """Guarda el mapa BMS actual en su archivo original"""
        if not self.current_map:
            self.update_status("No hay mapa para guardar")
            return
            
        if not self.current_file_path:
            # Si no hay archivo original, hacer "Guardar Como"
            self.save_bms_as()
            return
            
        try:
            # Obtener el código BMS directamente del editor
            if not dpg.does_item_exist("bms_code_text"):
                self.update_status("Error: Editor de código BMS no disponible")
                return
                
            bms_code = dpg.get_value("bms_code_text")
            
            # Verificar que hay contenido válido
            if not bms_code or bms_code.strip() == "// No hay mapa seleccionado":
                self.update_status("Error: No hay código BMS válido para guardar")
                return
            
            print(f"=== GUARDANDO CÓDIGO DESDE EDITOR ===")
            print(f"Primeras líneas del código:")
            for line in bms_code.split('\n')[:5]:
                print(f"  {repr(line)}")
            print("===================================")
            
            # Sobrescribir el archivo original
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(bms_code)
            
            self.update_status(f"Mapa guardado: {Path(self.current_file_path).name}")
            
        except Exception as e:
            self.update_status(f"Error al guardar mapa: {e}")
    
    def save_bms_as(self):
        """Guarda el mapa BMS actual con un nuevo nombre"""
        if not self.current_map:
            self.update_status("No hay mapa para guardar")
            return
            
        # Verificar si ya existe un diálogo y eliminarlo
        if dpg.does_item_exist("save_bms_as_dialog"):
            dpg.delete_item("save_bms_as_dialog")
            
        # Crear diálogo para guardar como
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            callback=self._save_bms_as_callback,
            tag="save_bms_as_dialog",
            width=700,
            height=400,
            default_path=".",
            default_filename=f"{self.current_map.name}.bms"
        ):
            dpg.add_file_extension(".bms", color=(0, 255, 0, 255), custom_text="[BMS]")
            dpg.add_file_extension(".txt", color=(255, 255, 0, 255), custom_text="[TXT]")
            dpg.add_file_extension(".*", color=(255, 255, 255, 255), custom_text="[Todos los archivos]")
            
    def _save_bms_as_callback(self, sender, app_data):
        """Callback para guardar como"""
        try:
            # Limpiar el diálogo
            if dpg.does_item_exist("save_bms_as_dialog"):
                dpg.delete_item("save_bms_as_dialog")
                
            if not self.current_map:
                self.update_status("Error: No hay mapa para guardar")
                return
                
            file_path = app_data["file_path_name"]
            if file_path:
                # Asegurar que tenga extensión .bms si no se especificó otra
                if not any(file_path.endswith(ext) for ext in ['.bms', '.txt']):
                    file_path += '.bms'
                    
                # Obtener el código BMS directamente del editor
                if not dpg.does_item_exist("bms_code_text"):
                    self.update_status("Error: Editor de código BMS no disponible")
                    return
                    
                bms_code = dpg.get_value("bms_code_text")
                
                # Verificar que hay contenido válido
                if not bms_code or bms_code.strip() == "// No hay mapa seleccionado":
                    self.update_status("Error: No hay código BMS válido para guardar")
                    return
                
                print(f"=== GUARDANDO COMO - CÓDIGO DESDE EDITOR ===")
                print(f"Archivo: {file_path}")
                print(f"Primeras líneas del código:")
                for line in bms_code.split('\n')[:5]:
                    print(f"  {repr(line)}")
                print("==========================================")
                
                # Guardar el archivo BMS
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(bms_code)
                
                # Actualizar la ruta del archivo actual
                self.current_file_path = file_path
                
                self.update_status(f"Mapa guardado como: {Path(file_path).name}")
                
        except Exception as e:
            self.update_status(f"Error al guardar mapa: {e}")
            
    def new_map(self):
        """Crea un nuevo mapa BMS"""
        # Limpiar estado de selección anterior
        self.deselect_field()
        
        if self.current_project:
            new_map = BMSMap(name="NUEVO_MAPA", mapset_name="MAPSET01")
            self.current_project.add_map(new_map)
            self.current_map = new_map
            self.update_project_tree()
            self.update_map_properties()
            self.update_visual_editor()
            self.update_bms_code_display()
            self.update_status("Nuevo mapa creado")
        else:
            self.update_status("Primero debe crear un proyecto")
            
    def new_field(self):
        """Crea un nuevo campo"""
        if self.current_map:
            field_count = len(self.current_map.fields) + 1
            new_field = BMSField(
                name=f"CAMPO{field_count:02d}",
                line=1,
                column=1,
                length=10
            )
            self.current_map.add_field(new_field)
            self.update_project_tree()
            self.update_visual_editor()
            self.update_bms_code_display()
            self.update_status("Nuevo campo añadido")
        else:
            self.update_status("Primero debe crear un mapa")
            
    def select_field(self, field_name: str):
        """Selecciona un campo para edición"""
        if self.current_map:
            field = self.current_map.get_field(field_name)
            if field:
                # Deseleccionar el campo anterior si existe
                if self.selected_field and self.selected_field.name in self.field_selectables:
                    dpg.set_value(self.field_selectables[self.selected_field.name], False)
                
                # Seleccionar el nuevo campo
                self.selected_field = field
                if field_name in self.field_selectables:
                    dpg.set_value(self.field_selectables[field_name], True)
                
                # Encontrar el índice del campo para mantener compatibilidad
                for i, f in enumerate(self.current_map.fields):
                    if f.name == field_name:
                        self.selected_field_index = i
                        break
                
                self.update_field_properties(field)
                self.update_visual_editor()  # Actualizar editor visual
                self.update_status(f"Campo seleccionado: {field_name}")
    
    def _create_field_select_tree_callback(self, field: BMSField):
        """Crea un callback para la selección de campo desde el árbol"""
        def callback(sender, app_data, user_data):
            # Solo procesar si el elemento fue seleccionado (no deseleccionado)
            if app_data:
                self.select_field(field.name)
            # Si se deselecciona, no hacer nada (mantener la selección actual)
            else:
                # Reseleccionar el elemento si es el campo actualmente seleccionado
                if self.selected_field and self.selected_field.name == field.name:
                    dpg.set_value(sender, True)
        return callback
                
    def update_map_properties(self):
        """Actualiza las propiedades del mapa en el panel"""
        if self.current_map:
            # Verificar que los elementos existen antes de establecer valores
            if dpg.does_item_exist("map_name_input"):
                dpg.set_value("map_name_input", self.current_map.name)
            if dpg.does_item_exist("mapset_name_input"):
                dpg.set_value("mapset_name_input", self.current_map.mapset_name)
            if dpg.does_item_exist("map_mode_combo"):
                dpg.set_value("map_mode_combo", self.current_map.mode)
            if dpg.does_item_exist("map_lang_combo"):
                dpg.set_value("map_lang_combo", self.current_map.lang)
            
    def update_field_properties(self, field: BMSField):
        """Actualiza las propiedades del campo en el panel"""
        # Actualizar título de la sección con el nombre del campo
        if dpg.does_item_exist("field_section_header"):
            dpg.set_item_label("field_section_header", f"Campo Seleccionado: {field.name}")
        
        # Verificar que cada elemento existe antes de establecer valores
        if dpg.does_item_exist("field_name_input"):
            dpg.set_value("field_name_input", field.name)
        if dpg.does_item_exist("field_line_input"):
            dpg.set_value("field_line_input", field.line)
        if dpg.does_item_exist("field_column_input"):
            dpg.set_value("field_column_input", field.column)
        if dpg.does_item_exist("field_length_input"):
            dpg.set_value("field_length_input", field.length)
        if dpg.does_item_exist("field_type_combo"):
            dpg.set_value("field_type_combo", field.field_type.value)
        if dpg.does_item_exist("field_initial_input"):
            dpg.set_value("field_initial_input", field.initial_value)
        if dpg.does_item_exist("field_picin_input"):
            dpg.set_value("field_picin_input", field.picin or "")
            print(f"Cargando PICIN: '{field.picin}'")
        if dpg.does_item_exist("field_picout_input"):
            dpg.set_value("field_picout_input", field.picout or "")
            print(f"Cargando PICOUT: '{field.picout}'")
        if dpg.does_item_exist("field_color_combo"):
            dpg.set_value("field_color_combo", field.color or "")
        if dpg.does_item_exist("field_hilight_combo"):
            dpg.set_value("field_hilight_combo", field.hilight or "")
        
        # Actualizar checkboxes de atributos
        for attr in FieldAttribute:
            attr_id = f"attr_{attr.value}"
            if dpg.does_item_exist(attr_id):
                dpg.set_value(attr_id, attr in field.attributes)
            
    def update_visual_editor(self):
        """Actualiza el editor visual con los campos del mapa actual"""
        # Verificar que el canvas existe
        if not dpg.does_item_exist("map_canvas"):
            return
            
        # Limpiar canvas
        dpg.delete_item("map_canvas", children_only=True)
        
        # Redibujar grid
        self.draw_screen_grid()
        
        # Dibujar campos
        if self.current_map:
            for field in self.current_map.fields:
                self.draw_field_on_canvas(field)
                
    def draw_field_on_canvas(self, field: BMSField):
        """Dibuja un campo en el canvas visual"""
        x = (field.column - 1) * self.cell_width
        y = (field.line - 1) * self.cell_height
        width = field.length * self.cell_width
        height = self.cell_height
        
        # Color según si está seleccionado o tipo de campo
        if field == self.selected_field:
            color = (255, 255, 0, 200)  # Amarillo brillante para seleccionado
            border_color = (255, 165, 0, 255)  # Borde naranja
            border_thickness = 3
        else:
            # Color según tipo de campo
            if field.field_type == FieldType.INPUT:
                color = (0, 255, 0, 100)  # Verde claro
            elif field.field_type == FieldType.OUTPUT:
                color = (0, 0, 255, 100)  # Azul claro
            elif field.field_type == FieldType.LABEL:
                color = (255, 255, 0, 100)  # Amarillo claro
            else:
                color = (128, 128, 128, 100)  # Gris claro
            border_color = (64, 64, 64, 255)  # Borde gris oscuro
            border_thickness = 1
            
        # Dibujar rectángulo del campo
        dpg.draw_rectangle(
            (x, y), (x + width, y + height),
            color=color,
            fill=color,
            parent="map_canvas"
        )
        
        # Dibujar borde
        dpg.draw_rectangle(
            (x, y), (x + width, y + height),
            color=border_color,
            thickness=border_thickness,
            parent="map_canvas"
        )
        
        # Dibujar texto del campo
        dpg.draw_text(
            (x + 2, y + 2),
            field.name,
            color=(0, 0, 0, 255),
            size=10,
            parent="map_canvas"
        )
        
    def update_bms_code_display(self):
        """Actualiza la visualización del código BMS generado"""
        # Verificar que el elemento existe antes de establecer el valor
        if not dpg.does_item_exist("bms_code_text"):
            return
            
        if self.current_map:
            try:
                # Generar código BMS usando el generador
                bms_code = self.bms_generator.generate_map_code(self.current_map)
                dpg.set_value("bms_code_text", bms_code)
            except Exception as e:
                dpg.set_value("bms_code_text", f"Error al generar código BMS: {e}")
        else:
            dpg.set_value("bms_code_text", "// No hay mapa seleccionado")
        
    # Métodos de selección simplificados - sin funcionalidad de click en canvas
    
    def deselect_field(self):
        """Deselecciona el campo actual"""
        self.selected_field = None
        self.selected_field_index = -1
        self.is_dragging = False
        
        # Verificar que el elemento existe antes de establecer el valor
        if dpg.does_item_exist("current_field_label"):
            dpg.set_value("current_field_label", "Campo actual: Ninguno")
        
        # Resetear título de la sección
        dpg.set_item_label("field_section_header", "Campo Seleccionado: Ninguno")
        
        # Deseleccionar todos los elementos en el explorador
        for selectable_id in self.field_selectables.values():
            if dpg.does_item_exist(selectable_id):
                dpg.set_value(selectable_id, False)
        
        # Limpiar panel de propiedades
        dpg.set_value("field_name_input", "")
        dpg.set_value("field_line_input", 1)
        dpg.set_value("field_column_input", 1)
        dpg.set_value("field_length_input", 1)
        dpg.set_value("field_type_combo", "")
        dpg.set_value("field_initial_input", "")
        dpg.set_value("field_picin_input", "")
        dpg.set_value("field_picout_input", "")
        dpg.set_value("field_color_combo", "")
        dpg.set_value("field_hilight_combo", "")
        
        # Limpiar checkboxes
        for attr in FieldAttribute:
            dpg.set_value(f"attr_{attr.value}", False)
        
    def generate_bms(self):
        """Genera el código BMS del mapa actual"""
        if self.current_map:
            self.update_bms_code_display()
            self.update_status("Código BMS generado")
        else:
            self.update_status("No hay mapa para generar")
            
    def update_status(self, message: str):
        """Actualiza la barra de estado"""
        dpg.set_value("status_text", message)
        
    def apply_field_changes(self):
        """Aplica los cambios del panel de propiedades al campo seleccionado"""
        if not self.selected_field:
            self.update_status("No hay campo seleccionado para aplicar cambios")
            return
            
        try:
            # Obtener valores del panel con verificaciones de seguridad
            name = dpg.get_value("field_name_input")
            line = dpg.get_value("field_line_input")
            column = dpg.get_value("field_column_input")
            length = dpg.get_value("field_length_input")
            field_type = dpg.get_value("field_type_combo")
            initial_value = dpg.get_value("field_initial_input")
            
            # Obtener PICIN y PICOUT con verificaciones
            picin = ""
            picout = ""
            if dpg.does_item_exist("field_picin_input"):
                picin = dpg.get_value("field_picin_input")
            if dpg.does_item_exist("field_picout_input"):
                picout = dpg.get_value("field_picout_input")
                
            color = dpg.get_value("field_color_combo")
            hilight = dpg.get_value("field_hilight_combo")
            
            print(f"Aplicando cambios - PICIN: '{picin}', PICOUT: '{picout}'")
            
            # Actualizar el campo
            self.selected_field.name = name
            self.selected_field.line = line
            self.selected_field.column = column
            self.selected_field.length = length
            self.selected_field.initial_value = initial_value
            self.selected_field.picin = picin if picin.strip() else None
            self.selected_field.picout = picout if picout.strip() else None
            self.selected_field.color = color if color else None
            self.selected_field.hilight = hilight if hilight else None
            
            print(f"Campo actualizado - PICIN: {self.selected_field.picin}, PICOUT: {self.selected_field.picout}")
            
            # Actualizar tipo de campo
            for ft in FieldType:
                if ft.value == field_type:
                    self.selected_field.field_type = ft
                    break
                    
            # Actualizar atributos - LIMPIAR PRIMERO
            old_attributes = [attr.value for attr in self.selected_field.attributes]
            self.selected_field.attributes.clear()
            
            # Aplicar solo los atributos marcados actualmente
            new_attributes = []
            for attr in FieldAttribute:
                attr_id = f"attr_{attr.value}"
                if dpg.does_item_exist(attr_id) and dpg.get_value(attr_id):
                    self.selected_field.attributes.append(attr)
                    new_attributes.append(attr.value)
            
            # Lógica especial para campos INPUT: agregar UNPROT automáticamente si no tiene otros atributos de protección
            if self.selected_field.field_type == FieldType.INPUT:
                has_protection_attr = any(attr in [FieldAttribute.PROT, FieldAttribute.UNPROT] for attr in self.selected_field.attributes)
                if not has_protection_attr:
                    # Asegurarse de que UNPROT esté marcado en la UI
                    if dpg.does_item_exist("attr_UNPROT"):
                        dpg.set_value("attr_UNPROT", True)
                    self.selected_field.attributes.append(FieldAttribute.UNPROT)
                    new_attributes.append("UNPROT")
            
            print(f"Atributos cambiados: {old_attributes} -> {new_attributes}")
            print(f"Tipo de campo: {self.selected_field.field_type.value}")
                    
            # Actualizar visualización
            self.update_visual_editor()
            self.update_bms_code_display()
            self.update_project_tree()
            
            # Debug: Verificar código BMS generado
            if self.current_map:
                try:
                    bms_code = self.bms_generator.generate_map_code(self.current_map)
                    print("=== CÓDIGO BMS ACTUALIZADO ===")
                    # Buscar líneas que contengan el nombre del campo actual
                    lines = bms_code.split('\n')
                    found_field = False
                    for i, line in enumerate(lines):
                        if name.upper() in line:
                            print(f"Línea del campo {name}:")
                            print(repr(line))  # Mostrar caracteres especiales
                            # Si hay línea de continuación, mostrarla también
                            if line.strip().endswith('*') and i + 1 < len(lines):
                                print("Línea de continuación:")
                                print(repr(lines[i + 1]))
                            found_field = True
                            break
                    if not found_field:
                        print(f"No se encontró el campo {name} en el código generado")
                    print("=============================")
                except Exception as e:
                    print(f"Error al generar código BMS para debug: {e}")
            
            self.update_status(f"Cambios aplicados al campo: {name}")
            
        except Exception as e:
            self.update_status(f"Error al aplicar cambios: {e}")
    
    def apply_field_changes_with_confirmation(self):
        """Aplica cambios al campo seleccionado con confirmación"""
        if not self.selected_field:
            self.update_status("No hay campo seleccionado para aplicar cambios")
            return
        
        # Crear modal de confirmación
        if dpg.does_item_exist("confirm_changes_modal"):
            dpg.delete_item("confirm_changes_modal")
            
        with dpg.window(
            label="Confirmar Cambios",
            modal=True,
            show=True,
            tag="confirm_changes_modal",
            width=400,
            height=150,
            pos=[400, 300]
        ):
            dpg.add_text(f"¿Está seguro de aplicar los cambios al campo '{self.selected_field.name}'?")
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                # Botón confirmar - verde
                with dpg.theme() as confirm_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 167, 69, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 205, 50, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 130, 50, 255))
                dpg.add_button(
                    label="[*] Si, Aplicar", 
                    callback=self._confirm_apply_changes,
                    width=120
                )
                dpg.bind_item_theme(dpg.last_item(), confirm_theme)
                
                # Botón cancelar - rojo
                with dpg.theme() as modal_cancel_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (220, 53, 69, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 69, 0, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (178, 34, 34, 255))
                dpg.add_button(
                    label="[X] Cancelar", 
                    callback=lambda: dpg.delete_item("confirm_changes_modal"),
                    width=100
                )
                dpg.bind_item_theme(dpg.last_item(), modal_cancel_theme)
                
    def _confirm_apply_changes(self):
        """Confirma y aplica los cambios al campo"""
        dpg.delete_item("confirm_changes_modal")
        self.apply_field_changes()
            
    def show_field_selector(self):
        """Muestra un diálogo para seleccionar un campo"""
        if not self.current_map or not self.current_map.fields:
            self.update_status("No hay campos disponibles para seleccionar")
            return
            
        # Crear ventana de selección
        with dpg.window(label="Seleccionar Campo", width=300, height=400, modal=True, tag="field_selector_window"):
            dpg.add_text("Seleccione un campo:")
            dpg.add_separator()
            
            # Lista de campos
            for i, field in enumerate(self.current_map.fields):
                # Crear callback específico para cada botón
                callback_func = self._create_field_select_callback(i)
                # Botones de campos - azul claro
                with dpg.theme() as field_select_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (72, 139, 194, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (100, 149, 237, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (50, 100, 150, 255))
                dpg.add_button(
                    label=f"[F] {field.name} (L{field.line}:C{field.column})",
                    callback=callback_func,
                    width=-1
                )
                dpg.bind_item_theme(dpg.last_item(), field_select_theme)
                
            dpg.add_separator()
            # Botón cancelar - rojo
            with dpg.theme() as selector_cancel_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (220, 53, 69, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 69, 0, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (178, 34, 34, 255))
            dpg.add_button(label="[X] Cancelar", callback=lambda: dpg.delete_item("field_selector_window"), width=-1)
            dpg.bind_item_theme(dpg.last_item(), selector_cancel_theme)
            
    def _create_field_select_callback(self, field_index: int):
        """Crea una función callback para seleccionar un campo específico"""
        def callback(sender, app_data):
            self.select_field_by_index(field_index)
        return callback
            
    def select_field_by_index(self, index: int):
        """Selecciona un campo por su índice"""
        # Verificar que el índice es válido
        if index is None:
            self.update_status("Error: índice de campo inválido")
            return
            
        if self.current_map and 0 <= index < len(self.current_map.fields):
            field = self.current_map.fields[index]
            
            # Deseleccionar el campo anterior si existe
            if self.selected_field and self.selected_field.name in self.field_selectables:
                dpg.set_value(self.field_selectables[self.selected_field.name], False)
            
            # Seleccionar el nuevo campo
            self.selected_field = field
            self.selected_field_index = index
            
            # Actualizar el árbol del proyecto
            if field.name in self.field_selectables:
                dpg.set_value(self.field_selectables[field.name], True)
            
            self.update_field_properties(self.selected_field)
            self.update_visual_editor()
            dpg.set_value("current_field_label", f"Campo actual: {self.selected_field.name}")
            self.update_status(f"Campo seleccionado: {self.selected_field.name}")
            
            # Cerrar ventana de selección
            if dpg.does_item_exist("field_selector_window"):
                dpg.delete_item("field_selector_window")
        else:
            self.update_status(f"Error: índice de campo fuera de rango: {index}")
        
    # Placeholders para otras funcionalidades - comentados los no implementados
    # def delete_map(self): pass  # TODO: Implementar eliminación de mapas
    # def edit_field(self): pass  # TODO: Implementar edición de campos
    # def delete_field(self): pass  # TODO: Implementar eliminación de campos  
    # def validate_map(self): pass  # TODO: Implementar validación de mapas
    # def show_visual_editor(self): pass  # TODO: Implementar cambio de vista
    # def show_bms_code(self): pass  # TODO: Implementar cambio de vista
    # def show_properties(self): pass  # TODO: Implementar cambio de vista
    
    def show_about(self):
        """Muestra el diálogo Acerca de"""
        if dpg.does_item_exist("about_dialog"):
            dpg.delete_item("about_dialog")
            
        # Calcular posición centrada
        viewport_width = dpg.get_viewport_width()
        viewport_height = dpg.get_viewport_height()
        window_width = 400
        window_height = 300
        pos_x = (viewport_width - window_width) // 2
        pos_y = (viewport_height - window_height) // 2
            
        with dpg.window(
            label="Acerca de PyBMS", 
            width=window_width, 
            height=window_height, 
            modal=True, 
            tag="about_dialog",
            pos=[pos_x, pos_y]
        ):
            dpg.add_text("PyBMS - Python BMS Generator")
            dpg.add_separator()
            dpg.add_text("Versión: 1.0.0")
            dpg.add_text("")
            dpg.add_text("Una herramienta completa para generar mapas BMS")
            dpg.add_text("(Basic Mapping Support) para sistemas mainframe CICS.")
            dpg.add_text("")
            dpg.add_text("Características:")
            dpg.add_text("• Editor visual de mapas BMS")
            dpg.add_text("• Generación automática de código") 
            dpg.add_text("• Soporte para campos con atributos")
            dpg.add_text("• Validación de contenido BMS")
            dpg.add_text("• Exportación a JSON")
            dpg.add_text("")
            dpg.add_text("Desarrollado con Python y DearPyGUI")
            dpg.add_separator()
            
            # Botón cerrar
            with dpg.theme() as about_close_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 130, 180, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (100, 149, 237, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 90, 140, 255))
            dpg.add_button(label="[X] Cerrar", callback=lambda: dpg.delete_item("about_dialog"), width=-1)
            dpg.bind_item_theme(dpg.last_item(), about_close_theme)
    def import_bms(self):
        """Importa un archivo BMS existente"""
        # Verificar si ya existe un diálogo y eliminarlo
        if dpg.does_item_exist("import_bms_dialog"):
            dpg.delete_item("import_bms_dialog")
        
        # Crear diálogo de archivo para importar BMS
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            callback=self._import_bms_callback,
            tag="import_bms_dialog",
            width=700,
            height=400,
            default_path="."
        ):
            dpg.add_file_extension(".bms", color=(0, 255, 0, 255))
            dpg.add_file_extension(".*", color=(255, 255, 255, 255))
            
    def _import_bms_callback(self, sender, app_data):
        """Callback para importar archivo BMS"""
        try:
            # Limpiar el diálogo
            if dpg.does_item_exist("import_bms_dialog"):
                dpg.delete_item("import_bms_dialog")
                
            file_path = app_data["file_path_name"]
            if file_path and file_path.endswith('.bms'):
                self._load_bms_file(file_path)
            else:
                self.update_status("Por favor selecciona un archivo .bms válido")
        except Exception as e:
            self.update_status(f"Error al importar BMS: {e}")
    def export_bms(self):
        """Exporta una copia del mapa actual como archivo BMS"""
        if not self.current_map:
            self.update_status("No hay mapa para exportar")
            return
            
        # Verificar si ya existe un diálogo y eliminarlo
        if dpg.does_item_exist("export_bms_dialog"):
            dpg.delete_item("export_bms_dialog")
            
        # Crear diálogo para exportar BMS
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            callback=self._export_bms_callback,
            tag="export_bms_dialog",
            width=700,
            height=400,
            default_path=".",
            default_filename=f"{self.current_map.name}_copy.bms"
        ):
            dpg.add_file_extension(".bms", color=(0, 255, 0, 255), custom_text="[BMS]")
            dpg.add_file_extension(".txt", color=(255, 255, 0, 255), custom_text="[TXT]")
            dpg.add_file_extension(".*", color=(255, 255, 255, 255), custom_text="[Todos los archivos]")
            
    def _export_bms_callback(self, sender, app_data):
        """Callback para exportar el mapa BMS"""
        try:
            # Limpiar el diálogo
            if dpg.does_item_exist("export_bms_dialog"):
                dpg.delete_item("export_bms_dialog")
                
            if not self.current_map:
                self.update_status("Error: No hay mapa para exportar")
                return
                
            file_path = app_data["file_path_name"]
            if file_path:
                # Asegurar que tenga extensión .bms si no se especificó otra
                if not any(file_path.endswith(ext) for ext in ['.bms', '.txt']):
                    file_path += '.bms'
                    
                # Generar el código BMS
                bms_code = self.bms_generator.generate_map_code(self.current_map)
                
                # Guardar el archivo BMS
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(bms_code)
                
                self.update_status(f"Mapa BMS exportado como copia: {file_path}")
                
        except Exception as e:
            self.update_status(f"Error al exportar copia del mapa BMS: {e}")
    def exit_app(self): 
        """Muestra confirmación antes de salir de la aplicación"""
        if dpg.does_item_exist("exit_confirmation_dialog"):
            dpg.delete_item("exit_confirmation_dialog")
            
        # Calcular posición centrada
        viewport_width = dpg.get_viewport_width()
        viewport_height = dpg.get_viewport_height()
        window_width = 350
        window_height = 150
        pos_x = (viewport_width - window_width) // 2
        pos_y = (viewport_height - window_height) // 2
            
        with dpg.window(
            label="Confirmar Salida",
            width=window_width,
            height=window_height,
            modal=True,
            tag="exit_confirmation_dialog",
            pos=[pos_x, pos_y]
        ):
            dpg.add_text("¿Está seguro de que desea salir de PyBMS?")
            dpg.add_text("")
            dpg.add_text("Se perderán los cambios no guardados.")
            dpg.add_separator()
            
            # Centrar los botones horizontalmente
            dpg.add_spacer(height=5)
            with dpg.group(horizontal=True):
                # Espaciador izquierdo para centrar
                dpg.add_spacer(width=30)
                
                # Botón confirmar salida - rojo
                with dpg.theme() as exit_confirm_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (220, 53, 69, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 69, 0, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (178, 34, 34, 255))
                dpg.add_button(
                    label="[!] Sí, Salir", 
                    callback=self._confirm_exit,
                    width=120
                )
                dpg.bind_item_theme(dpg.last_item(), exit_confirm_theme)
                
                # Espaciador entre botones
                dpg.add_spacer(width=20)
                
                # Botón cancelar - verde (quedarse)
                with dpg.theme() as exit_cancel_theme:
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 167, 69, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 205, 50, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 130, 50, 255))
                dpg.add_button(
                    label="[X] Cancelar", 
                    callback=lambda: dpg.delete_item("exit_confirmation_dialog"),
                    width=120
                )
                dpg.bind_item_theme(dpg.last_item(), exit_cancel_theme)
                
    def _confirm_exit(self):
        """Confirma y ejecuta la salida de la aplicación"""
        dpg.delete_item("exit_confirmation_dialog")
        self.should_exit = True  # Marcar para permitir salida
        dpg.stop_dearpygui()  # Forzar cierre de la aplicación
        
    def _on_window_close(self):
        """Callback que se ejecuta cuando se intenta cerrar la ventana"""
        # Si ya se confirmó la salida, permitir el cierre
        if self.should_exit:
            return True
            
        # Si no se ha confirmado, mostrar diálogo y prevenir cierre
        self.exit_app()
        return False  # Prevenir el cierre hasta que se confirme
        
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
