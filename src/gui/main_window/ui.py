# Métodos de UI migrados desde BMSGeneratorApp
def create_main_window(self):
	# ...migrar el contenido de create_main_window desde app.py...
	pass

def create_visual_editor(self):
	# ...migrar el contenido de create_visual_editor desde app.py...
	pass

def create_properties_panel(self):
	# ...migrar el contenido de create_properties_panel desde app.py...
	pass

def draw_screen_grid(self):
	# ...migrar el contenido de draw_screen_grid desde app.py...
	pass

def draw_field_on_canvas(self, field):
	# ...migrar el contenido de draw_field_on_canvas desde app.py...
	pass

def update_visual_editor(self):
	# ...migrar el contenido de update_visual_editor desde app.py...
	pass

def update_bms_code_display(self):
	# ...migrar el contenido de update_bms_code_display desde app.py...
	pass

def display_bms_code_with_colors(self, bms_code):
	# ...migrar el contenido de display_bms_code_with_colors desde app.py...
	pass

def create_colored_line_monospace(self, line, line_tag):
	# ...migrar el contenido de create_colored_line_monospace desde app.py...
	pass

def add_colored_text_segments(self, text, colors):
	# ...migrar el contenido de add_colored_text_segments desde app.py...
	pass
# ui.py: Creación de ventanas, menús, paneles y layouts para PyBMS

import dearpygui.dearpygui as dpg
from models import FieldType, FieldAttribute

def create_main_window(app):
    """Crea la ventana principal de la aplicación"""
    
    # Crear tema para editor de código BMS 
    with dpg.theme() as app.codigo_bms_theme:
        with dpg.theme_component(dpg.mvInputText):
            # Color de fondo más oscuro para mejor contraste
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (30, 30, 35, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (35, 35, 40, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (40, 40, 45, 255))
            # Texto más claro para mejor legibilidad
            dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220, 255))
    
    with dpg.window(label="PyBMS - BMS Generator", tag="main_window"):
        
        # Barra de menú
        with dpg.menu_bar():
            with dpg.menu(label="Archivo"):
                # Elementos básicos que NO están en botones
                dpg.add_menu_item(label="Guardar Como...", callback=app.save_bms_as)
                dpg.add_separator()
                dpg.add_menu_item(label="Exportar a JSON", callback=app.export_to_json)
                dpg.add_menu_item(label="Importar BMS", callback=app.import_bms)
                dpg.add_separator()
                dpg.add_menu_item(label="Salir", callback=app.exit_app)
                
            with dpg.menu(label="Ayuda"):
                dpg.add_menu_item(label="Acerca de", callback=app.show_about)
        
        # Barra de herramientas
        with dpg.group(horizontal=True):
            # Botones de archivo - azul
            with dpg.theme() as nuevo_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 130, 180, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (100, 149, 237, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 90, 140, 255))
            dpg.add_button(label="[+] Nuevo Proyecto", callback=app.new_project)
            dpg.bind_item_theme(dpg.last_item(), nuevo_theme)
            
            with dpg.theme() as abrir_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 130, 180, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (100, 149, 237, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 90, 140, 255))
            dpg.add_button(label="[O] Abrir", callback=app.open_project)
            dpg.bind_item_theme(dpg.last_item(), abrir_theme)
            
            dpg.add_separator()
            
            # Botones de creación - púrpura
            with dpg.theme() as mapa_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (138, 43, 226, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (160, 70, 255, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 20, 180, 255))
            dpg.add_button(label="[M] Nuevo Mapa", callback=app.new_map)
            dpg.bind_item_theme(dpg.last_item(), mapa_theme)
            
            with dpg.theme() as campo_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (138, 43, 226, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (160, 70, 255, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 20, 180, 255))
            dpg.add_button(label="[F] Nuevo Campo", callback=app.new_field)
            dpg.bind_item_theme(dpg.last_item(), campo_theme)
            
            dpg.add_separator()
            
            # Botón generar - rojo
            with dpg.theme() as generar_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (220, 20, 60, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 69, 0, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (178, 34, 34, 255))
            dpg.add_button(label="[G] Generar BMS", callback=app.generate_bms_with_confirmation)
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
                        app.create_visual_editor()
                        
                    # Pestaña del código BMS
                    with dpg.tab(label="Código BMS", tag="bms_code_tab"):
                        # Crear contenedor para código con syntax highlighting
                        with dpg.child_window(width=-1, height=-1, tag="bms_code_container", border=False):
                            dpg.add_text("// Código BMS se mostrará aquí", tag="bms_syntax_content")
            
            # Panel derecho - Propiedades
            with dpg.child_window(width=280, height=-1, tag="properties_panel"):
                dpg.add_text("Propiedades")
                dpg.add_separator()
                app.create_properties_panel()
        
        # Barra de estado
        with dpg.group(horizontal=True):
            dpg.add_text("Listo", tag="status_text")
            
        # Configurar handler para interceptar cierre de ventana
        with dpg.handler_registry():
            dpg.add_key_press_handler(dpg.mvKey_F4, callback=lambda: app._on_alt_f4())
            
def _on_alt_f4(app):
    """Intercepta Alt+F4 para mostrar confirmación"""
    if dpg.is_key_down(dpg.mvKey_ModAlt):
        app.exit_app()

def create_visual_editor(app):
    """Crea el editor visual de mapas BMS"""
    with dpg.group():
        dpg.add_text("Editor Visual de Mapa BMS")
        dpg.add_separator()
        
        # Canvas para el mapa (simulando pantalla 24x80)
        with dpg.drawlist(width=app.canvas_width, height=app.canvas_height, tag="map_canvas"):
            # Dibujar grid de la pantalla
            app.draw_screen_grid()
            
def create_properties_panel(app):
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
            dpg.add_button(label="[*] Aplicar Cambios", callback=app.apply_field_changes, width=140)
            dpg.bind_item_theme(dpg.last_item(), prop_aplicar_theme)

def update_field_properties(app, field):
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
    if dpg.does_item_exist("field_picout_input"):
        dpg.set_value("field_picout_input", field.picout or "")
    if dpg.does_item_exist("field_color_combo"):
        dpg.set_value("field_color_combo", field.color or "")
    if dpg.does_item_exist("field_hilight_combo"):
        dpg.set_value("field_hilight_combo", field.hilight or "")
    
    # Actualizar checkboxes de atributos
    for attr in FieldAttribute:
        attr_id = f"attr_{attr.value}"
        if dpg.does_item_exist(attr_id):
            dpg.set_value(attr_id, attr in field.attributes)

def draw_screen_grid(app):
    """Dibuja la cuadrícula de la pantalla 24x80"""
    # Colores
    grid_color = (100, 100, 100, 255)  # Gris claro
    
    # Líneas verticales
    for i in range(81):  # 0 a 80
        x = i * app.cell_width
        dpg.draw_line(
            (x, 0), (x, app.canvas_height),
            color=grid_color,
            thickness=1 if i % 10 == 0 else 0.5,
            parent="map_canvas"
        )
        
    # Líneas horizontales  
    for i in range(25):  # 0 a 24
        y = i * app.cell_height
        dpg.draw_line(
            (0, y), (app.canvas_width, y),
            color=grid_color,
            thickness=1 if i % 5 == 0 else 0.5,
            parent="map_canvas"
        )

def draw_field_on_canvas(app, field):
    """Dibuja un campo en el canvas visual"""
    x = (field.column - 1) * app.cell_width
    y = (field.line - 1) * app.cell_height
    width = field.length * app.cell_width
    height = app.cell_height
    
    # Color según si está seleccionado o tipo de campo
    if field == app.selected_field:
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

def update_visual_editor(app):
    """Actualiza el editor visual con los campos del mapa actual"""
    # Verificar que el canvas existe
    if not dpg.does_item_exist("map_canvas"):
        return
        
    # Limpiar canvas
    dpg.delete_item("map_canvas", children_only=True)
    
    # Redibujar grid
    app.draw_screen_grid()
    
    # Dibujar campos
    if app.current_map:
        for field in app.current_map.fields:
            app.draw_field_on_canvas(field)

def update_bms_code_display(app):
    """Actualiza la visualización del código BMS generado con syntax highlighting"""
    # Verificar que el contenedor existe
    if not dpg.does_item_exist("bms_code_container"):
        return
        
    if app.current_map:
        try:
            # Generar código BMS usando el generador
            bms_code = app.bms_generator.generate_map_code(app.current_map)
            app.display_bms_code_with_colors(bms_code)
        except Exception as e:
            app.display_bms_code_with_colors(f"Error al generar código BMS: {e}")
    else:
        app.display_bms_code_with_colors("// No hay mapa seleccionado")

def display_bms_code_with_colors(app, bms_code):
    """Muestra el código BMS con syntax highlighting manteniendo alineación"""
    # Limpiar contenido anterior
    if dpg.does_item_exist("bms_syntax_content"):
        dpg.delete_item("bms_syntax_content")
    
    # Crear nuevo contenido con syntax highlighting
    with dpg.group(tag="bms_syntax_content", parent="bms_code_container"):
        lines = bms_code.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                create_colored_line_monospace(app, line, f"line_{i}")
            else:
                # Línea vacía con altura fija
                dpg.add_text(" ", tag=f"line_{i}")

def create_colored_line_monospace(app, line, line_tag):
    """Crea una línea con colores manteniendo alineación monoespaciada perfecta"""
    # Definir colores
    colors = {
        'keyword': (100, 149, 237),      # Azul para palabras clave BMS
        'field_name': (255, 215, 0),     # Dorado para nombres de campos
        'string': (144, 238, 144),       # Verde claro para strings
        'number': (255, 182, 193),       # Rosa claro para números
        'comment': (128, 128, 128),      # Gris para comentarios
        'default': (220, 220, 220)       # Gris claro para texto normal
    }
    
    # Si es comentario, línea completa en gris
    if line.strip().startswith('*') or line.strip().startswith('//'):
        dpg.add_text(line, color=colors['comment'], tag=line_tag)
        return
    
    # Identificar palabras clave BMS
    bms_keywords = ['DFHMSD', 'DFHMDI', 'DFHMDF', 'TYPE', 'MODE', 'LANG', 'CTRL', 
                   'STORAGE', 'TERM', 'POS', 'LENGTH', 'ATTRB', 'INITIAL', 
                   'PICIN', 'PICOUT', 'COLOR', 'HILIGHT', 'SIZE', 'FREEKB', 
                   'FRSET', 'END']
    
    # Determinar color principal de la línea
    if any(keyword in line for keyword in bms_keywords):
        dpg.add_text(line, color=colors['keyword'], tag=line_tag)
    else:
        # Línea normal
        dpg.add_text(line, color=colors['default'], tag=line_tag)

def add_colored_text_segments(app, text, colors):
    """Agrega segmentos de texto con colores apropiados"""
    import re
    
    # Buscar y colorear strings
    parts = re.split(r"('[^']*')", text)
    
    for part in parts:
        if not part:
            continue
        elif part.startswith("'") and part.endswith("'"):
            # String
            dpg.add_text(part, color=colors['string'])
        elif any(keyword in part for keyword in ['DFHMSD', 'DFHMDI', 'DFHMDF', 'TYPE', 'MODE', 'LANG']):
            # Contiene keywords
            dpg.add_text(part, color=colors['keyword'])
        else:
            # Texto normal
            dpg.add_text(part, color=colors['default'])

def update_project_tree(app):
    """Actualiza el árbol del proyecto"""
    # Limpiar árbol existente
    dpg.delete_item("project_tree", children_only=True)
    # Limpiar referencias a selectables anteriores
    app.field_selectables.clear()
    
    if app.current_project:
        with dpg.tree_node(label=f"📁 {app.current_project.name}", parent="project_tree", default_open=True):
            with dpg.tree_node(label="📋 Mapas", default_open=True):
                for bms_map in app.current_project.maps:
                    with dpg.tree_node(label=f"📄 {bms_map.name}", leaf=True):
                        for field in bms_map.fields:
                            # Crear callback con captura correcta del nombre del campo
                            def make_callback(field_name):
                                return lambda sender, app_data: select_field(app, field_name) if app_data else None
                            
                            selectable_id = dpg.add_selectable(
                                label=f"🔢 {field.name}",
                                callback=make_callback(field.name),
                                default_value=False
                            )
                            # Guardar referencia para poder deseleccionar después
                            app.field_selectables[field.name] = selectable_id
    else:
        dpg.add_text("(Sin proyecto)", parent="project_tree")

def select_field(app, field_name):
    """Selecciona un campo para edición"""
    if app.current_map:
        field = app.current_map.get_field(field_name)
        if field:
            # Deseleccionar el campo anterior si existe
            if app.selected_field and app.selected_field.name in app.field_selectables:
                dpg.set_value(app.field_selectables[app.selected_field.name], False)
            
            # Seleccionar el nuevo campo
            app.selected_field = field
            if field_name in app.field_selectables:
                dpg.set_value(app.field_selectables[field_name], True)
            
            # Encontrar el índice del campo para mantener compatibilidad
            for i, f in enumerate(app.current_map.fields):
                if f.name == field_name:
                    app.selected_field_index = i
                    break
            
            update_field_properties(app, field)
            app.update_visual_editor()  # Actualizar editor visual
            app.update_status(f"Campo seleccionado: {field_name}")

def update_map_properties(app):
    """Actualiza las propiedades del mapa en el panel"""
    if app.current_map:
        # Verificar que los elementos existen antes de establecer valores
        if dpg.does_item_exist("map_name_input"):
            dpg.set_value("map_name_input", app.current_map.name)
        if dpg.does_item_exist("mapset_name_input"):
            dpg.set_value("mapset_name_input", app.current_map.mapset_name)
        if dpg.does_item_exist("map_mode_combo"):
            dpg.set_value("map_mode_combo", app.current_map.mode)
        if dpg.does_item_exist("map_lang_combo"):
            dpg.set_value("map_lang_combo", app.current_map.lang)

def deselect_field(app):
    """Deselecciona el campo actual"""
    app.selected_field = None
    app.selected_field_index = -1
    app.is_dragging = False
    
    # Verificar que el elemento existe antes de establecer el valor
    if dpg.does_item_exist("current_field_label"):
        dpg.set_value("current_field_label", "Campo actual: Ninguno")
    
    # Resetear título de la sección
    dpg.set_item_label("field_section_header", "Campo Seleccionado: Ninguno")
    
    # Deseleccionar todos los elementos en el explorador
    for selectable_id in app.field_selectables.values():
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
