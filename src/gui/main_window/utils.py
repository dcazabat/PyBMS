# utils.py: Funciones utilitarias y auxiliares para PyBMS

import re
from typing import Optional

def is_valid_bms_content(app, content: str) -> bool:
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

def sanitize_name_for_cobol(app, name: str) -> str:
    """Convierte un nombre de archivo a un nombre válido para COBOL/BMS"""
    # Convertir a mayúsculas
    clean_name = name.upper()
    
    # Reemplazar caracteres no válidos con guiones bajos
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

def get_bms_code_content(app):
    """Obtiene el contenido actual del código BMS desde el generador"""
    if app.current_map:
        try:
            return app.bms_generator.generate_map_code(app.current_map)
        except Exception as e:
            return f"Error al generar código BMS: {e}"
    else:
        return "// No hay mapa seleccionado"

def format_field_name(name: str) -> str:
    """Formatea un nombre de campo para BMS (máximo 8 caracteres, mayúsculas)"""
    formatted = name.upper().strip()
    formatted = re.sub(r'[^A-Z0-9_]', '_', formatted)
    return formatted[:8]

def validate_field_position(line: int, column: int) -> tuple[bool, str]:
    """Valida si una posición de campo es válida"""
    if line < 1 or line > 24:
        return False, "La línea debe estar entre 1 y 24"
    if column < 1 or column > 80:
        return False, "La columna debe estar entre 1 y 80"
    return True, ""

def calculate_field_end_position(line: int, column: int, length: int) -> tuple[int, int]:
    """Calcula la posición final de un campo dado su inicio y longitud"""
    end_column = column + length - 1
    end_line = line
    
    # Si se desborda, calcular en qué línea termina
    while end_column > 80:
        end_column -= 80
        end_line += 1
        
    return end_line, end_column

def detect_field_overlaps(fields, exclude_field=None) -> list:
    """Detecta superposiciones entre campos"""
    overlaps = []
    
    for i, field1 in enumerate(fields):
        if field1 == exclude_field:
            continue
            
        for j, field2 in enumerate(fields[i+1:], i+1):
            if field2 == exclude_field:
                continue
                
            # Verificar si los campos se superponen
            if fields_overlap(field1, field2):
                overlaps.append((field1, field2))
                
    return overlaps

def fields_overlap(field1, field2) -> bool:
    """Verifica si dos campos se superponen"""
    # Calcular posiciones finales
    end1_line, end1_col = calculate_field_end_position(field1.line, field1.column, field1.length)
    end2_line, end2_col = calculate_field_end_position(field2.line, field2.column, field2.length)
    
    # Si están en líneas diferentes sin solapamiento
    if field1.line > end2_line or field2.line > end1_line:
        return False
    
    # Si están en la misma línea, verificar columnas
    if field1.line == field2.line:
        return not (field1.column + field1.length <= field2.column or 
                   field2.column + field2.length <= field1.column)
    
    # Caso complejo: campos que abarcan múltiples líneas
    # Por simplicidad, considerar superposición si hay cualquier intersección
    return True

def generate_unique_field_name(existing_fields, base_name="CAMPO") -> str:
    """Genera un nombre único para un campo"""
    existing_names = {field.name for field in existing_fields}
    
    counter = 1
    while True:
        candidate = f"{base_name}{counter:02d}"
        if candidate not in existing_names:
            return candidate
        counter += 1
        if counter > 99:  # Límite de seguridad
            break
            
    # Fallback
    import random
    return f"{base_name}{random.randint(10, 99)}"

def parse_position_string(pos_str: str) -> tuple[int, int] | None:
    """Parsea una cadena de posición tipo 'L5C10' o '5,10'"""
    try:
        pos_str = pos_str.strip().upper()
        
        # Formato L5C10
        if 'L' in pos_str and 'C' in pos_str:
            l_idx = pos_str.find('L')
            c_idx = pos_str.find('C')
            if l_idx < c_idx:
                line_str = pos_str[l_idx+1:c_idx]
                col_str = pos_str[c_idx+1:]
                return int(line_str), int(col_str)
        
        # Formato 5,10
        elif ',' in pos_str:
            parts = pos_str.split(',')
            if len(parts) == 2:
                return int(parts[0].strip()), int(parts[1].strip())
                
    except:
        pass
    return None

def format_position_string(line: int, column: int) -> str:
    """Formatea una posición como string legible"""
    return f"L{line}C{column}"

def get_color_rgb(color_name: str) -> tuple[int, int, int, int]:
    """Obtiene valores RGB para colores BMS estándar"""
    colors = {
        'RED': (255, 0, 0, 255),
        'BLUE': (0, 0, 255, 255),
        'GREEN': (0, 255, 0, 255),
        'YELLOW': (255, 255, 0, 255),
        'PINK': (255, 192, 203, 255),
        'TURQUOISE': (64, 224, 208, 255),
        'WHITE': (255, 255, 255, 255),
        'NEUTRAL': (192, 192, 192, 255)
    }
    return colors.get(color_name.upper(), (255, 255, 255, 255))

def get_attribute_description(attribute) -> str:
    """Obtiene descripción legible de un atributo"""
    descriptions = {
        'ASKIP': 'Auto Skip',
        'PROT': 'Protected',
        'UNPROT': 'Unprotected', 
        'NUM': 'Numeric',
        'BRT': 'Bright',
        'NORM': 'Normal',
        'DRK': 'Dark',
        'IC': 'Insert Cursor',
        'FSET': 'Field Set'
    }
    return descriptions.get(str(attribute).upper(), str(attribute))
