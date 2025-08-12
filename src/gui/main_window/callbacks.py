# callbacks.py: Callbacks y eventos migrados desde BMSGeneratorApp

import dearpygui.dearpygui as dpg
from pathlib import Path
from models import BMSProject, BMSMap, BMSField, FieldType, FieldAttribute

def new_project(app):
    """Crea un nuevo proyecto"""
    # Limpiar estado de selección anterior
    app.deselect_field()
    
    app.current_project = BMSProject(name="Nuevo Proyecto")
    app.current_map = None  # Limpiar mapa actual también
    app.current_file_path = None  # Limpiar archivo actual
    app.update_project_tree()
    app.update_status("Nuevo proyecto creado")

def new_map(app):
    """Crea un nuevo mapa BMS"""
    # Limpiar estado de selección anterior
    app.deselect_field()
    
    if app.current_project:
        new_map_obj = BMSMap(name="NUEVO_MAPA", mapset_name="MAPSET01")
        app.current_project.add_map(new_map_obj)
        app.current_map = new_map_obj
        app.update_project_tree()
        app.update_map_properties()
        app.update_visual_editor()
        app.update_bms_code_display()
        app.update_status("Nuevo mapa creado")
    else:
        app.update_status("Primero debe crear un proyecto")

def new_field(app):
    """Crea un nuevo campo"""
    if app.current_map:
        field_count = len(app.current_map.fields) + 1
        new_field_obj = BMSField(
            name=f"CAMPO{field_count:02d}",
            line=1,
            column=1,
            length=10
        )
        app.current_map.add_field(new_field_obj)
        app.update_project_tree()
        app.update_visual_editor()
        app.update_bms_code_display()
        app.update_status("Nuevo campo añadido")
    else:
        app.update_status("Primero debe crear un mapa")

def open_project(app):
    """Abre un proyecto existente"""
    # Verificar si ya existe un diálogo y eliminarlo
    if dpg.does_item_exist("open_project_dialog"):
        dpg.delete_item("open_project_dialog")
    
    # Crear diálogo de archivo para abrir (acepta cualquier extensión)
    with dpg.file_dialog(
        directory_selector=False,
        show=True,
        callback=lambda sender, app_data: _open_project_callback(app, sender, app_data),
        tag="open_project_dialog",
        width=700,
        height=400,
        default_path=".",
        modal=False
    ):
        # Solo usar el filtro "todos los archivos" para evitar problemas con extensiones
        dpg.add_file_extension(".*", color=(255, 255, 255, 255), custom_text="[Todos los archivos]")

def _open_project_callback(app, sender, app_data):
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
            _load_project_from_file(app, file_path)
    except Exception as e:
        app.update_status(f"Error al abrir archivo: {e}")

def _load_project_from_file(app, file_path):
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
                app.update_status(f"Error al leer archivo {file_name}: No se puede decodificar")
                return
        
        # Verificar si el contenido parece ser BMS válido
        if app._is_valid_bms_content(content):
            # Cargar como archivo BMS
            _load_bms_file_with_content(app, file_path, content)
        elif file_extension == ".json":
            # Cargar proyecto JSON
            _load_json_project(app, file_path)
        else:
            # Mostrar alerta de que no es un mapa BMS válido
            _show_invalid_bms_alert(app, file_name)
            return
            
        app.update_status(f"Archivo cargado: {file_name}")
        
    except Exception as e:
        app.update_status(f"Error al cargar archivo: {e}")

def _load_bms_file_with_content(app, file_path, content):
    """Carga un archivo BMS con contenido ya leído"""
    try:
        # Limpiar estado de selección anterior
        app.deselect_field()
        
        # Guardar la ruta del archivo actual
        app.current_file_path = file_path
        
        # Crear un nuevo proyecto para el archivo BMS
        # Usar el nombre del archivo sin extensión, pero validar que sea un nombre válido
        file_name = Path(file_path).stem
        project_name = file_name if file_name else "PROYECTO_BMS"
        app.current_project = BMSProject(name=project_name)
        
        # Crear un mapa basado en el archivo BMS
        # Usar el nombre del archivo como base, asegurando que sea válido para COBOL
        map_name = app._sanitize_name_for_cobol(file_name) if file_name else "MAPA01"
        new_map = BMSMap(name=map_name, mapset_name="MAPSET01")
        
        # Parsear el contenido BMS básico
        app._parse_bms_content(new_map, content)
        
        app.current_project.add_map(new_map)
        app.current_map = new_map
        
        app.update_project_tree()
        app.update_map_properties()
        app.update_visual_editor()
        app.update_bms_code_display()
        
        # Validar el mapa cargado
        errors = app.bms_generator.validate_map(new_map)
        if errors:
            error_count = len(errors)
            app.update_status(f"Mapa cargado con {error_count} advertencia(s) de validación")
        else:
            app.update_status(f"Mapa BMS cargado y validado correctamente")
        
    except Exception as e:
        raise Exception(f"Error al procesar archivo BMS: {e}")

def _show_invalid_bms_alert(app, file_name):
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
                callback=lambda: _force_load_as_bms(app, file_name),
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

def _force_load_as_bms(app, file_path):
    """Fuerza la carga de un archivo como BMS aunque no parezca válido"""
    try:
        dpg.delete_item("invalid_bms_alert")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        _load_bms_file_with_content(app, file_path, content)
        app.update_status(f"Archivo cargado forzadamente: {Path(file_path).name}")
    except Exception as e:
        app.update_status(f"Error al cargar archivo forzadamente: {e}")

def _load_json_project(app, file_path):
    """Carga un proyecto desde un archivo JSON"""
    try:
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # Crear el proyecto
        project_name = project_data.get('name', 'Proyecto Sin Nombre')
        app.current_project = BMSProject(name=project_name)
        
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
                    app.update_status(f"Error al cargar campo: {e}")
                    continue
            
            app.current_project.add_map(bms_map)
        
        # Establecer el primer mapa como actual si existe
        if app.current_project.maps:
            app.current_map = app.current_project.maps[0]
        else:
            app.current_map = None
        
        # Actualizar la interfaz
        app.update_project_tree()
        app.update_map_properties()
        app.update_visual_editor()
        app.update_bms_code_display()
        
        app.update_status(f"Proyecto JSON cargado: {project_name}")
        
    except json.JSONDecodeError as e:
        app.update_status(f"Error: El archivo no es un JSON válido - {e}")
    except Exception as e:
        app.update_status(f"Error al cargar proyecto JSON: {e}")

def save_bms(app):
    """Guarda el mapa BMS actual en su archivo original"""
    if not app.current_map:
        app.update_status("No hay mapa para guardar")
        return
        
    if not app.current_file_path:
        # Si no hay archivo original, hacer "Guardar Como"
        save_bms_as(app)
        return
        
    try:
        # Obtener el código BMS directamente del generador
        bms_code = app.get_bms_code_content()
        
        # Verificar que hay contenido válido
        if not bms_code or bms_code.strip() == "// No hay mapa seleccionado":
            app.update_status("Error: No hay código BMS válido para guardar")
            return
        
        # Sobrescribir el archivo original
        with open(app.current_file_path, 'w', encoding='utf-8') as f:
            f.write(bms_code)
        
        app.update_status(f"Mapa guardado: {Path(app.current_file_path).name}")
        
    except Exception as e:
        app.update_status(f"Error al guardar mapa: {e}")

def save_bms_as(app):
    """Guarda el mapa BMS actual con un nuevo nombre"""
    if not app.current_map:
        app.update_status("No hay mapa para guardar")
        return
        
    # Verificar si ya existe un diálogo y eliminarlo
    if dpg.does_item_exist("save_bms_as_dialog"):
        dpg.delete_item("save_bms_as_dialog")
        
    # Crear diálogo para guardar como
    with dpg.file_dialog(
        directory_selector=False,
        show=True,
        callback=lambda sender, app_data: _save_bms_as_callback(app, sender, app_data),
        tag="save_bms_as_dialog",
        width=700,
        height=400,
        default_path=".",
        default_filename=f"{app.current_map.name}.bms"
    ):
        dpg.add_file_extension(".bms", color=(0, 255, 0, 255), custom_text="[BMS]")
        dpg.add_file_extension(".txt", color=(255, 255, 0, 255), custom_text="[TXT]")
        dpg.add_file_extension(".*", color=(255, 255, 255, 255), custom_text="[Todos los archivos]")

def _save_bms_as_callback(app, sender, app_data):
    """Callback para guardar como"""
    try:
        # Limpiar el diálogo
        if dpg.does_item_exist("save_bms_as_dialog"):
            dpg.delete_item("save_bms_as_dialog")
            
        if not app.current_map:
            app.update_status("Error: No hay mapa para guardar")
            return
            
        file_path = app_data["file_path_name"]
        if file_path:
            # Asegurar que tenga extensión .bms si no se especificó otra
            if not any(file_path.endswith(ext) for ext in ['.bms', '.txt']):
                file_path += '.bms'
                
            # Obtener el código BMS directamente del generador
            bms_code = app.get_bms_code_content()
            
            # Verificar que hay contenido válido
            if not bms_code or bms_code.strip() == "// No hay mapa seleccionado":
                app.update_status("Error: No hay código BMS válido para guardar")
                return
            
            # Guardar el archivo BMS
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(bms_code)
            
            # Actualizar la ruta del archivo actual
            app.current_file_path = file_path
            
            app.update_status(f"Mapa guardado como: {Path(file_path).name}")
            
    except Exception as e:
        app.update_status(f"Error al guardar mapa: {e}")

def apply_field_changes(app):
    """Aplica los cambios del panel de propiedades al campo seleccionado"""
    if not app.selected_field:
        app.update_status("No hay campo seleccionado para aplicar cambios")
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
        
        # Actualizar el campo
        app.selected_field.name = name
        app.selected_field.line = line
        app.selected_field.column = column
        app.selected_field.length = length
        app.selected_field.initial_value = initial_value
        app.selected_field.picin = picin if picin.strip() else None
        app.selected_field.picout = picout if picout.strip() else None
        app.selected_field.color = color if color else None
        app.selected_field.hilight = hilight if hilight else None
        
        # Actualizar tipo de campo
        for ft in FieldType:
            if ft.value == field_type:
                app.selected_field.field_type = ft
                break
                
        # Actualizar atributos - LIMPIAR PRIMERO
        app.selected_field.attributes.clear()
        
        # Aplicar solo los atributos marcados actualmente
        for attr in FieldAttribute:
            attr_id = f"attr_{attr.value}"
            if dpg.does_item_exist(attr_id) and dpg.get_value(attr_id):
                app.selected_field.attributes.append(attr)
        
        # Lógica especial para campos INPUT: agregar UNPROT automáticamente si no tiene otros atributos de protección
        if app.selected_field.field_type == FieldType.INPUT:
            has_protection_attr = any(attr in [FieldAttribute.PROT, FieldAttribute.UNPROT] for attr in app.selected_field.attributes)
            if not has_protection_attr:
                # Asegurarse de que UNPROT esté marcado en la UI
                if dpg.does_item_exist("attr_UNPROT"):
                    dpg.set_value("attr_UNPROT", True)
                app.selected_field.attributes.append(FieldAttribute.UNPROT)
                
        # Actualizar visualización
        app.update_visual_editor()
        app.update_bms_code_display()
        app.update_project_tree()
        
        app.update_status(f"Cambios aplicados al campo: {name}")
        
    except Exception as e:
        app.update_status(f"Error al aplicar cambios: {e}")

def apply_field_changes_with_confirmation(app):
    """Aplica cambios al campo seleccionado con confirmación"""
    if not app.selected_field:
        app.update_status("No hay campo seleccionado para aplicar cambios")
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
        dpg.add_text(f"¿Está seguro de aplicar los cambios al campo '{app.selected_field.name}'?")
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
                callback=lambda: _confirm_apply_changes(app),
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

def _confirm_apply_changes(app):
    """Confirma y aplica los cambios al campo"""
    dpg.delete_item("confirm_changes_modal")
    apply_field_changes(app)

def export_to_json(app):
    """Exporta el proyecto actual a un archivo JSON"""
    if not app.current_project:
        app.update_status("No hay proyecto para exportar")
        return
        
    # Verificar si ya existe un diálogo y eliminarlo
    if dpg.does_item_exist("export_json_dialog"):
        dpg.delete_item("export_json_dialog")
        
    # Crear diálogo para exportar el proyecto
    with dpg.file_dialog(
        directory_selector=False,
        show=True,
        callback=lambda sender, app_data: _export_json_callback(app, sender, app_data),
        tag="export_json_dialog",
        width=700,
        height=400,
        default_path=".",
        default_filename=f"{app.current_project.name}.json"
    ):
        dpg.add_file_extension(".json", color=(0, 255, 255, 255), custom_text="[JSON]")
        dpg.add_file_extension(".*", color=(255, 255, 255, 255), custom_text="[Todos los archivos]")

def _export_json_callback(app, sender, app_data):
    """Callback para exportar el proyecto a JSON"""
    try:
        # Limpiar el diálogo
        if dpg.does_item_exist("export_json_dialog"):
            dpg.delete_item("export_json_dialog")
            
        if not app.current_project:
            app.update_status("Error: No hay proyecto para exportar")
            return
            
        file_path = app_data["file_path_name"]
        if file_path:
            # Asegurar que tenga extensión .json
            if not file_path.endswith('.json'):
                file_path += '.json'
                
            # Convertir el proyecto a JSON
            project_data = {
                "name": app.current_project.name,
                "maps": []
            }
            
            for bms_map in app.current_project.maps:
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
            
            app.update_status(f"Proyecto exportado a JSON: {file_path}")
            
    except Exception as e:
        app.update_status(f"Error al exportar proyecto: {e}")

def import_bms(app):
    """Importa un archivo BMS existente"""
    # Verificar si ya existe un diálogo y eliminarlo
    if dpg.does_item_exist("import_bms_dialog"):
        dpg.delete_item("import_bms_dialog")
    
    # Crear diálogo de archivo para importar BMS
    with dpg.file_dialog(
        directory_selector=False,
        show=True,
        callback=lambda sender, app_data: _import_bms_callback(app, sender, app_data),
        tag="import_bms_dialog",
        width=700,
        height=400,
        default_path="."
    ):
        dpg.add_file_extension(".bms", color=(0, 255, 0, 255))
        dpg.add_file_extension(".*", color=(255, 255, 255, 255))

def _import_bms_callback(app, sender, app_data):
    """Callback para importar archivo BMS"""
    try:
        # Limpiar el diálogo
        if dpg.does_item_exist("import_bms_dialog"):
            dpg.delete_item("import_bms_dialog")
            
        file_path = app_data["file_path_name"]
        if file_path and file_path.endswith('.bms'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            _load_bms_file_with_content(app, file_path, content)
        else:
            app.update_status("Por favor selecciona un archivo .bms válido")
    except Exception as e:
        app.update_status(f"Error al importar BMS: {e}")

def export_bms(app):
    """Exporta una copia del mapa actual como archivo BMS"""
    if not app.current_map:
        app.update_status("No hay mapa para exportar")
        return
        
    # Verificar si ya existe un diálogo y eliminarlo
    if dpg.does_item_exist("export_bms_dialog"):
        dpg.delete_item("export_bms_dialog")
        
    # Crear diálogo para exportar BMS
    with dpg.file_dialog(
        directory_selector=False,
        show=True,
        callback=lambda sender, app_data: _export_bms_callback(app, sender, app_data),
        tag="export_bms_dialog",
        width=700,
        height=400,
        default_path=".",
        default_filename=f"{app.current_map.name}_copy.bms"
    ):
        dpg.add_file_extension(".bms", color=(0, 255, 0, 255), custom_text="[BMS]")
        dpg.add_file_extension(".txt", color=(255, 255, 0, 255), custom_text="[TXT]")
        dpg.add_file_extension(".*", color=(255, 255, 255, 255), custom_text="[Todos los archivos]")

def _export_bms_callback(app, sender, app_data):
    """Callback para exportar el mapa BMS"""
    try:
        # Limpiar el diálogo
        if dpg.does_item_exist("export_bms_dialog"):
            dpg.delete_item("export_bms_dialog")
            
        if not app.current_map:
            app.update_status("Error: No hay mapa para exportar")
            return
            
        file_path = app_data["file_path_name"]
        if file_path:
            # Asegurar que tenga extensión .bms si no se especificó otra
            if not any(file_path.endswith(ext) for ext in ['.bms', '.txt']):
                file_path += '.bms'
                
            # Generar el código BMS
            bms_code = app.bms_generator.generate_map_code(app.current_map)
            
            # Guardar el archivo BMS
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(bms_code)
            
            app.update_status(f"Mapa BMS exportado como copia: {file_path}")
            
    except Exception as e:
        app.update_status(f"Error al exportar copia del mapa BMS: {e}")

def show_about(app):
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

def exit_app(app): 
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
                callback=lambda: _confirm_exit(app),
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

def _confirm_exit(app):
    """Confirma y ejecuta la salida de la aplicación"""
    dpg.delete_item("exit_confirmation_dialog")
    app.should_exit = True  # Marcar para permitir salida
    dpg.stop_dearpygui()  # Forzar cierre de la aplicación

# ========== CALLBACKS DEL ÁRBOL DE PROYECTO ==========

def on_project_tree_selection(app, sender, app_data):
    """Callback para cuando se selecciona un elemento en el árbol del proyecto"""
    try:
        selected_item = app_data
        
        # Si el item seleccionado no existe, salir
        if not dpg.does_item_exist(selected_item):
            return
            
        # Obtener el tipo de item usando user_data
        user_data = dpg.get_item_user_data(selected_item)
        if not user_data:
            return
            
        item_type = user_data.get("type")
        
        if item_type == "project":
            # Seleccionar proyecto - limpiar selecciones de mapa y campo
            app.current_map = None
            app.deselect_field()
            app.update_map_properties()
            app.update_visual_editor()
            app.update_bms_code_display()
            app.update_status("Proyecto seleccionado")
            
        elif item_type == "map":
            # Seleccionar mapa
            map_index = user_data.get("index", 0)
            if 0 <= map_index < len(app.current_project.maps):
                app.current_map = app.current_project.maps[map_index]
                app.deselect_field()  # Limpiar selección de campo
                app.update_map_properties()
                app.update_visual_editor()
                app.update_bms_code_display()
                app.update_status(f"Mapa seleccionado: {app.current_map.name}")
                
        elif item_type == "field":
            # Seleccionar campo
            map_index = user_data.get("map_index", 0)
            field_index = user_data.get("field_index", 0)
            
            if (0 <= map_index < len(app.current_project.maps) and
                0 <= field_index < len(app.current_project.maps[map_index].fields)):
                
                target_map = app.current_project.maps[map_index]
                target_field = target_map.fields[field_index]
                
                # Cambiar mapa si es necesario
                if app.current_map != target_map:
                    app.current_map = target_map
                    app.update_map_properties()
                    app.update_visual_editor()
                    
                # Seleccionar el campo
                app.select_field(target_field)
                app.update_status(f"Campo seleccionado: {target_field.name}")
                
    except Exception as e:
        app.update_status(f"Error en selección de árbol: {e}")

def on_project_tree_double_click(app, sender, app_data):
    """Callback para doble clic en el árbol del proyecto"""
    try:
        selected_item = app_data
        
        # Si el item seleccionado no existe, salir
        if not dpg.does_item_exist(selected_item):
            return
            
        # Obtener el tipo de item usando user_data
        user_data = dpg.get_item_user_data(selected_item)
        if not user_data:
            return
            
        item_type = user_data.get("type")
        
        if item_type == "field":
            # Doble clic en campo - mostrar propiedades y centrar en editor visual
            map_index = user_data.get("map_index", 0)
            field_index = user_data.get("field_index", 0)
            
            if (0 <= map_index < len(app.current_project.maps) and
                0 <= field_index < len(app.current_project.maps[map_index].fields)):
                
                target_map = app.current_project.maps[map_index]
                target_field = target_map.fields[field_index]
                
                # Cambiar mapa si es necesario
                if app.current_map != target_map:
                    app.current_map = target_map
                    app.update_map_properties()
                    app.update_visual_editor()
                    
                # Seleccionar el campo
                app.select_field(target_field)
                
                # Enfocar el panel de propiedades del campo
                if dpg.does_item_exist("field_properties_panel"):
                    dpg.focus_item("field_properties_panel")
                    
                app.update_status(f"Editando campo: {target_field.name}")
                
        elif item_type == "map":
            # Doble clic en mapa - enfocar propiedades del mapa
            map_index = user_data.get("index", 0)
            if 0 <= map_index < len(app.current_project.maps):
                app.current_map = app.current_project.maps[map_index]
                app.deselect_field()
                app.update_map_properties()
                app.update_visual_editor()
                app.update_bms_code_display()
                
                # Enfocar el panel de propiedades del mapa
                if dpg.does_item_exist("map_properties_panel"):
                    dpg.focus_item("map_properties_panel")
                    
                app.update_status(f"Editando mapa: {app.current_map.name}")
                
    except Exception as e:
        app.update_status(f"Error en doble clic de árbol: {e}")

# ========== CALLBACKS DEL EDITOR VISUAL ==========

def on_visual_editor_click(app, sender, app_data):
    """Callback para clics en el editor visual"""
    try:
        if not app.current_map:
            return
            
        # Obtener posición del clic en el canvas
        mouse_pos = dpg.get_mouse_pos(local=False)
        
        # Ajustar coordenadas considerando la posición del canvas
        if dpg.does_item_exist("visual_editor_canvas"):
            canvas_pos = dpg.get_item_pos("visual_editor_canvas")
            relative_x = mouse_pos[0] - canvas_pos[0]
            relative_y = mouse_pos[1] - canvas_pos[1]
            
            # Convertir coordenadas de píxeles a línea/columna
            # Usar el tamaño de carácter aproximado (10x15 píxeles)
            char_width = 10
            char_height = 15
            
            grid_col = max(1, int(relative_x // char_width) + 1)
            grid_line = max(1, int(relative_y // char_height) + 1)
            
            # Buscar si hay un campo en esa posición
            clicked_field = None
            for field in app.current_map.fields:
                if (field.line == grid_line and 
                    grid_col >= field.column and 
                    grid_col < field.column + field.length):
                    clicked_field = field
                    break
                    
            if clicked_field:
                # Seleccionar el campo encontrado
                app.select_field(clicked_field)
                app.update_status(f"Campo seleccionado: {clicked_field.name}")
            else:
                # Deseleccionar si no se encontró campo
                app.deselect_field()
                app.update_status(f"Posición: línea {grid_line}, columna {grid_col}")
                
    except Exception as e:
        app.update_status(f"Error en clic del editor visual: {e}")

def on_visual_editor_double_click(app, sender, app_data):
    """Callback para doble clic en el editor visual"""
    try:
        # Si hay un campo seleccionado, editar sus propiedades
        if app.selected_field:
            # Enfocar el panel de propiedades del campo
            if dpg.does_item_exist("field_properties_panel"):
                dpg.focus_item("field_properties_panel")
            app.update_status(f"Editando campo: {app.selected_field.name}")
        else:
            # Si no hay campo seleccionado, crear uno nuevo en esa posición
            if app.current_map:
                new_field(app)
                
    except Exception as e:
        app.update_status(f"Error en doble clic del editor visual: {e}")

def on_visual_editor_right_click(app, sender, app_data):
    """Callback para clic derecho en el editor visual"""
    try:
        if not app.current_map:
            return
            
        # Obtener posición del clic
        mouse_pos = dpg.get_mouse_pos(local=False)
        
        # Buscar si hay un campo en esa posición (similar a on_visual_editor_click)
        if dpg.does_item_exist("visual_editor_canvas"):
            canvas_pos = dpg.get_item_pos("visual_editor_canvas")
            relative_x = mouse_pos[0] - canvas_pos[0]
            relative_y = mouse_pos[1] - canvas_pos[1]
            
            char_width = 10
            char_height = 15
            
            grid_col = max(1, int(relative_x // char_width) + 1)
            grid_line = max(1, int(relative_y // char_height) + 1)
            
            # Buscar campo en esa posición
            right_clicked_field = None
            for field in app.current_map.fields:
                if (field.line == grid_line and 
                    grid_col >= field.column and 
                    grid_col < field.column + field.length):
                    right_clicked_field = field
                    break
            
            # Mostrar menú contextual
            _show_visual_editor_context_menu(app, mouse_pos, right_clicked_field, grid_line, grid_col)
                
    except Exception as e:
        app.update_status(f"Error en clic derecho del editor visual: {e}")

def _show_visual_editor_context_menu(app, mouse_pos, field, line, column):
    """Muestra un menú contextual en el editor visual"""
    try:
        # Eliminar menú anterior si existe
        if dpg.does_item_exist("visual_editor_context_menu"):
            dpg.delete_item("visual_editor_context_menu")
            
        # Crear ventana de menú contextual
        with dpg.window(
            label="",
            width=180,
            height=120,
            no_title_bar=True,
            no_resize=True,
            no_move=True,
            modal=True,
            pos=mouse_pos,
            tag="visual_editor_context_menu"
        ):
            if field:
                # Opciones para campo existente
                dpg.add_text(f"Campo: {field.name}")
                dpg.add_separator()
                dpg.add_button(
                    label="[📝] Editar Campo",
                    callback=lambda: _context_edit_field(app, field),
                    width=-1
                )
                dpg.add_button(
                    label="[🗑️] Eliminar Campo", 
                    callback=lambda: _context_delete_field(app, field),
                    width=-1
                )
                dpg.add_separator()
                dpg.add_button(
                    label="[➕] Nuevo Campo Aquí",
                    callback=lambda: _context_new_field_at(app, line, column),
                    width=-1
                )
            else:
                # Opciones para posición vacía
                dpg.add_text(f"Pos: L{line} C{column}")
                dpg.add_separator()
                dpg.add_button(
                    label="[➕] Nuevo Campo Aquí",
                    callback=lambda: _context_new_field_at(app, line, column),
                    width=-1
                )
                if app.selected_field:
                    dpg.add_button(
                        label="[📋] Mover Campo Aquí",
                        callback=lambda: _context_move_field_to(app, line, column),
                        width=-1
                    )
                    
            dpg.add_separator()
            dpg.add_button(
                label="[❌] Cerrar",
                callback=lambda: dpg.delete_item("visual_editor_context_menu"),
                width=-1
            )
            
    except Exception as e:
        app.update_status(f"Error al mostrar menú contextual: {e}")

def _context_edit_field(app, field):
    """Edita un campo desde el menú contextual"""
    dpg.delete_item("visual_editor_context_menu")
    app.select_field(field)
    if dpg.does_item_exist("field_properties_panel"):
        dpg.focus_item("field_properties_panel")

def _context_delete_field(app, field):
    """Elimina un campo desde el menú contextual"""
    dpg.delete_item("visual_editor_context_menu")
    if field in app.current_map.fields:
        app.current_map.fields.remove(field)
        if app.selected_field == field:
            app.deselect_field()
        app.update_project_tree()
        app.update_visual_editor()
        app.update_bms_code_display()
        app.update_status(f"Campo eliminado: {field.name}")

def _context_new_field_at(app, line, column):
    """Crea un nuevo campo en la posición especificada"""
    dpg.delete_item("visual_editor_context_menu")
    if app.current_map:
        field_count = len(app.current_map.fields) + 1
        new_field_obj = BMSField(
            name=f"CAMPO{field_count:02d}",
            line=line,
            column=column,
            length=10
        )
        app.current_map.add_field(new_field_obj)
        app.select_field(new_field_obj)
        app.update_project_tree()
        app.update_visual_editor()
        app.update_bms_code_display()
        app.update_status(f"Nuevo campo añadido en L{line} C{column}")

def _context_move_field_to(app, line, column):
    """Mueve el campo seleccionado a la posición especificada"""
    dpg.delete_item("visual_editor_context_menu")
    if app.selected_field:
        app.selected_field.line = line
        app.selected_field.column = column
        app.update_field_properties()
        app.update_visual_editor()
        app.update_bms_code_display()
        app.update_status(f"Campo {app.selected_field.name} movido a L{line} C{column}")

# ========== CALLBACKS DE PROPIEDADES DEL MAPA ==========

def apply_map_changes(app):
    """Aplica los cambios de las propiedades del mapa"""
    if not app.current_map:
        app.update_status("No hay mapa seleccionado para aplicar cambios")
        return
        
    try:
        # Obtener valores del panel de propiedades del mapa
        name = dpg.get_value("map_name_input")
        mapset_name = dpg.get_value("map_mapset_input")
        size = dpg.get_value("map_size_combo")
        lang = dpg.get_value("map_lang_combo")
        
        # Actualizar el mapa
        app.current_map.name = name
        app.current_map.mapset_name = mapset_name
        app.current_map.size = size
        app.current_map.lang = lang
        
        # Actualizar visualización
        app.update_project_tree()
        app.update_visual_editor()
        app.update_bms_code_display()
        
        app.update_status(f"Propiedades del mapa actualizadas: {name}")
        
    except Exception as e:
        app.update_status(f"Error al aplicar cambios del mapa: {e}")

def apply_map_changes_with_confirmation(app):
    """Aplica cambios del mapa con confirmación"""
    if not app.current_map:
        app.update_status("No hay mapa seleccionado para aplicar cambios")
        return
    
    # Crear modal de confirmación
    if dpg.does_item_exist("confirm_map_changes_modal"):
        dpg.delete_item("confirm_map_changes_modal")
        
    with dpg.window(
        label="Confirmar Cambios del Mapa",
        modal=True,
        show=True,
        tag="confirm_map_changes_modal",
        width=400,
        height=150,
        pos=[400, 300]
    ):
        dpg.add_text(f"¿Está seguro de aplicar los cambios al mapa '{app.current_map.name}'?")
        dpg.add_separator()
        
        with dpg.group(horizontal=True):
            # Botón confirmar - verde
            with dpg.theme() as map_confirm_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 167, 69, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 205, 50, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 130, 50, 255))
            dpg.add_button(
                label="[*] Si, Aplicar", 
                callback=lambda: _confirm_apply_map_changes(app),
                width=120
            )
            dpg.bind_item_theme(dpg.last_item(), map_confirm_theme)
            
            # Botón cancelar - rojo
            with dpg.theme() as map_cancel_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (220, 53, 69, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 69, 0, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (178, 34, 34, 255))
            dpg.add_button(
                label="[X] Cancelar", 
                callback=lambda: dpg.delete_item("confirm_map_changes_modal"),
                width=100
            )
            dpg.bind_item_theme(dpg.last_item(), map_cancel_theme)

def _confirm_apply_map_changes(app):
    """Confirma y aplica los cambios del mapa"""
    dpg.delete_item("confirm_map_changes_modal")
    apply_map_changes(app)

# ========== CALLBACKS DE VALIDACIÓN Y HERRAMIENTAS ==========

def validate_current_map(app):
    """Valida el mapa actual y muestra los resultados"""
    if not app.current_map:
        app.update_status("No hay mapa para validar")
        return
        
    try:
        # Usar el generador para validar
        errors = app.bms_generator.validate_map(app.current_map)
        
        if not errors:
            app.update_status("✅ Mapa validado correctamente - Sin errores")
            _show_validation_success(app)
        else:
            app.update_status(f"⚠️ Validación completada - {len(errors)} advertencia(s) encontrada(s)")
            _show_validation_errors(app, errors)
            
    except Exception as e:
        app.update_status(f"Error durante la validación: {e}")

def _show_validation_success(app):
    """Muestra ventana de validación exitosa"""
    if dpg.does_item_exist("validation_success_dialog"):
        dpg.delete_item("validation_success_dialog")
        
    with dpg.window(
        label="✅ Validación Exitosa",
        width=350,
        height=200,
        modal=True,
        tag="validation_success_dialog"
    ):
        dpg.add_text("🎉 ¡Validación Completada!")
        dpg.add_separator()
        dpg.add_text(f"Mapa: {app.current_map.name}")
        dpg.add_text(f"Campos: {len(app.current_map.fields)}")
        dpg.add_text("")
        dpg.add_text("✅ Sin errores de validación")
        dpg.add_text("✅ Estructura BMS correcta")
        dpg.add_text("✅ Listo para generar código")
        dpg.add_separator()
        
        # Botón cerrar - verde
        with dpg.theme() as success_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 167, 69, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 205, 50, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 130, 50, 255))
        dpg.add_button(
            label="[✓] Cerrar",
            callback=lambda: dpg.delete_item("validation_success_dialog"),
            width=-1
        )
        dpg.bind_item_theme(dpg.last_item(), success_theme)

def _show_validation_errors(app, errors):
    """Muestra ventana con errores de validación"""
    if dpg.does_item_exist("validation_errors_dialog"):
        dpg.delete_item("validation_errors_dialog")
        
    # Calcular tamaño de ventana según cantidad de errores
    window_height = min(500, 200 + len(errors) * 25)
        
    with dpg.window(
        label="⚠️ Advertencias de Validación",
        width=600,
        height=window_height,
        modal=True,
        tag="validation_errors_dialog"
    ):
        dpg.add_text(f"📋 Se encontraron {len(errors)} advertencia(s):")
        dpg.add_separator()
        
        # Lista de errores
        with dpg.child_window(height=window_height-120, border=True):
            for i, error in enumerate(errors, 1):
                dpg.add_text(f"{i}. ⚠️ {error}")
                
        dpg.add_separator()
        
        with dpg.group(horizontal=True):
            # Botón continuar - amarillo
            with dpg.theme() as warning_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (255, 193, 7, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 215, 0, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (218, 165, 32, 255))
            dpg.add_button(
                label="[!] Continuar de todos modos",
                callback=lambda: dpg.delete_item("validation_errors_dialog"),
                width=200
            )
            dpg.bind_item_theme(dpg.last_item(), warning_theme)
            
            # Espaciador
            dpg.add_spacer(width=50)
            
            # Botón cerrar - azul
            with dpg.theme() as errors_close_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 130, 180, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (100, 149, 237, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 90, 140, 255))
            dpg.add_button(
                label="[X] Cerrar",
                callback=lambda: dpg.delete_item("validation_errors_dialog"),
                width=150
            )
            dpg.bind_item_theme(dpg.last_item(), errors_close_theme)

def generate_preview(app):
    """Genera y muestra una vista previa del código BMS"""
    if not app.current_map:
        app.update_status("No hay mapa para generar vista previa")
        return
        
    try:
        # Generar el código BMS
        bms_code = app.bms_generator.generate_map_code(app.current_map)
        
        # Mostrar en ventana de vista previa
        _show_code_preview(app, bms_code)
        
        app.update_status("Vista previa generada")
        
    except Exception as e:
        app.update_status(f"Error al generar vista previa: {e}")

def _show_code_preview(app, bms_code):
    """Muestra ventana con vista previa del código"""
    if dpg.does_item_exist("code_preview_dialog"):
        dpg.delete_item("code_preview_dialog")
        
    # Calcular posición centrada
    viewport_width = dpg.get_viewport_width()
    viewport_height = dpg.get_viewport_height()
    window_width = min(800, viewport_width - 100)
    window_height = min(600, viewport_height - 100)
    pos_x = (viewport_width - window_width) // 2
    pos_y = (viewport_height - window_height) // 2
        
    with dpg.window(
        label="📋 Vista Previa del Código BMS",
        width=window_width,
        height=window_height,
        modal=True,
        tag="code_preview_dialog",
        pos=[pos_x, pos_y]
    ):
        dpg.add_text(f"Mapa: {app.current_map.name}")
        dpg.add_separator()
        
        # Área de texto con el código
        with dpg.child_window(height=window_height-120, border=True):
            dpg.add_input_text(
                default_value=bms_code,
                multiline=True,
                readonly=True,
                width=-1,
                height=-1,
                tag="preview_code_text"
            )
            
        dpg.add_separator()
        
        with dpg.group(horizontal=True):
            # Botón copiar - verde
            with dpg.theme() as copy_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 167, 69, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 205, 50, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 130, 50, 255))
            dpg.add_button(
                label="[📋] Copiar Código",
                callback=lambda: _copy_code_to_clipboard(app, bms_code),
                width=150
            )
            dpg.bind_item_theme(dpg.last_item(), copy_theme)
            
            # Espaciador
            dpg.add_spacer(width=50)
            
            # Botón guardar como - azul
            with dpg.theme() as save_preview_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 130, 180, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (100, 149, 237, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 90, 140, 255))
            dpg.add_button(
                label="[💾] Guardar Como...",
                callback=lambda: (_close_preview_and_save_as(app)),
                width=150
            )
            dpg.bind_item_theme(dpg.last_item(), save_preview_theme)
            
            # Espaciador
            dpg.add_spacer(width=50)
            
            # Botón cerrar - gris
            dpg.add_button(
                label="[X] Cerrar",
                callback=lambda: dpg.delete_item("code_preview_dialog"),
                width=100
            )

def _copy_code_to_clipboard(app, code):
    """Copia el código al portapapeles"""
    try:
        # Intentar usar el portapapeles del sistema
        import subprocess
        
        # Linux: usar xclip o xsel
        try:
            subprocess.run(['xclip', '-selection', 'clipboard'], input=code.encode(), check=True)
            app.update_status("✅ Código copiado al portapapeles")
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(['xsel', '--clipboard', '--input'], input=code.encode(), check=True)
                app.update_status("✅ Código copiado al portapapeles")
            except (subprocess.CalledProcessError, FileNotFoundError):
                app.update_status("❌ No se pudo copiar al portapapeles (instalar xclip o xsel)")
                
    except Exception as e:
        app.update_status(f"Error al copiar al portapapeles: {e}")

def _close_preview_and_save_as(app):
    """Cierra la vista previa y abre guardar como"""
    dpg.delete_item("code_preview_dialog")
    save_bms_as(app)

def delete_selected_field(app):
    """Elimina el campo seleccionado"""
    if not app.selected_field or not app.current_map:
        app.update_status("No hay campo seleccionado para eliminar")
        return
        
    # Crear confirmación de eliminación
    if dpg.does_item_exist("delete_field_confirmation"):
        dpg.delete_item("delete_field_confirmation")
        
    with dpg.window(
        label="Confirmar Eliminación",
        width=350,
        height=150,
        modal=True,
        tag="delete_field_confirmation"
    ):
        dpg.add_text(f"¿Está seguro de eliminar el campo '{app.selected_field.name}'?")
        dpg.add_text("Esta acción no se puede deshacer.")
        dpg.add_separator()
        
        with dpg.group(horizontal=True):
            # Botón confirmar - rojo
            with dpg.theme() as delete_confirm_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (220, 53, 69, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 69, 0, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (178, 34, 34, 255))
            dpg.add_button(
                label="[🗑️] Eliminar", 
                callback=lambda: _confirm_delete_field(app),
                width=120
            )
            dpg.bind_item_theme(dpg.last_item(), delete_confirm_theme)
            
            # Botón cancelar - verde
            with dpg.theme() as delete_cancel_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 167, 69, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 205, 50, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (30, 130, 50, 255))
            dpg.add_button(
                label="[X] Cancelar", 
                callback=lambda: dpg.delete_item("delete_field_confirmation"),
                width=120
            )
            dpg.bind_item_theme(dpg.last_item(), delete_cancel_theme)

def _confirm_delete_field(app):
    """Confirma y ejecuta la eliminación del campo"""
    if app.selected_field and app.current_map:
        field_name = app.selected_field.name
        app.current_map.fields.remove(app.selected_field)
        app.deselect_field()
        
        # Actualizar interfaz
        app.update_project_tree()
        app.update_visual_editor()
        app.update_bms_code_display()
        
        app.update_status(f"Campo eliminado: {field_name}")
        
    dpg.delete_item("delete_field_confirmation")

def duplicate_selected_field(app):
    """Duplica el campo seleccionado"""
    if not app.selected_field or not app.current_map:
        app.update_status("No hay campo seleccionado para duplicar")
        return
        
    try:
        # Crear copia del campo
        original_field = app.selected_field
        field_count = len(app.current_map.fields) + 1
        
        # Crear nuevo campo con propiedades copiadas
        duplicated_field = BMSField(
            name=f"{original_field.name}_COPY",
            line=original_field.line + 1,  # Mover una línea abajo
            column=original_field.column,
            length=original_field.length
        )
        
        # Copiar propiedades
        duplicated_field.field_type = original_field.field_type
        duplicated_field.initial_value = original_field.initial_value
        duplicated_field.attributes = original_field.attributes.copy()
        duplicated_field.color = original_field.color
        duplicated_field.hilight = original_field.hilight
        duplicated_field.picin = original_field.picin
        duplicated_field.picout = original_field.picout
        
        # Añadir al mapa y seleccionar
        app.current_map.add_field(duplicated_field)
        app.select_field(duplicated_field)
        
        # Actualizar interfaz
        app.update_project_tree()
        app.update_visual_editor()
        app.update_bms_code_display()
        
        app.update_status(f"Campo duplicado: {duplicated_field.name}")
        
    except Exception as e:
        app.update_status(f"Error al duplicar campo: {e}")

# ========== CALLBACKS DE TECLADO Y ATAJOS ==========

def handle_keyboard_shortcuts(app, sender, app_data):
    """Maneja atajos de teclado globales"""
    try:
        key = app_data
        
        # Ctrl+N - Nuevo proyecto
        if dpg.is_key_down(dpg.mvKey_LControl) and key == dpg.mvKey_N:
            new_project(app)
            
        # Ctrl+O - Abrir proyecto  
        elif dpg.is_key_down(dpg.mvKey_LControl) and key == dpg.mvKey_O:
            open_project(app)
            
        # Ctrl+S - Guardar mapa
        elif dpg.is_key_down(dpg.mvKey_LControl) and key == dpg.mvKey_S:
            save_bms(app)
            
        # Ctrl+Shift+S - Guardar como
        elif dpg.is_key_down(dpg.mvKey_LControl) and dpg.is_key_down(dpg.mvKey_LShift) and key == dpg.mvKey_S:
            save_bms_as(app)
            
        # F5 - Validar mapa
        elif key == dpg.mvKey_F5:
            validate_current_map(app)
            
        # F9 - Vista previa
        elif key == dpg.mvKey_F9:
            generate_preview(app)
            
        # Delete - Eliminar campo seleccionado
        elif key == dpg.mvKey_Delete and app.selected_field:
            delete_selected_field(app)
            
        # Ctrl+D - Duplicar campo
        elif dpg.is_key_down(dpg.mvKey_LControl) and key == dpg.mvKey_D and app.selected_field:
            duplicate_selected_field(app)
            
        # Escape - Deseleccionar campo
        elif key == dpg.mvKey_Escape:
            app.deselect_field()
            
        # Ctrl+Q - Salir
        elif dpg.is_key_down(dpg.mvKey_LControl) and key == dpg.mvKey_Q:
            exit_app(app)
            
    except Exception as e:
        app.update_status(f"Error en atajo de teclado: {e}")

# ========== CALLBACKS DE MOUSE GLOBAL ==========

def handle_global_mouse_click(app, sender, app_data):
    """Maneja clics globales del mouse para cerrar menús contextuales"""
    try:
        # Cerrar menú contextual si existe y el clic fue fuera de él
        if dpg.does_item_exist("visual_editor_context_menu"):
            mouse_pos = dpg.get_mouse_pos()
            menu_pos = dpg.get_item_pos("visual_editor_context_menu")
            menu_size = [180, 120]  # Tamaño aproximado del menú
            
            # Verificar si el clic fue fuera del menú
            if (mouse_pos[0] < menu_pos[0] or mouse_pos[0] > menu_pos[0] + menu_size[0] or
                mouse_pos[1] < menu_pos[1] or mouse_pos[1] > menu_pos[1] + menu_size[1]):
                dpg.delete_item("visual_editor_context_menu")
                
    except Exception as e:
        pass  # Ignorar errores de mouse global silenciosamente
# callbacks.py: Callbacks de menús, botones y diálogos para PyBMS

# Aquí irán funciones como save_bms, open_project, export_to_json, etc.
