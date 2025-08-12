# parsing.py: Funciones de parseo de archivos, mapas y campos para PyBMS

import re
from typing import List, Optional, Tuple
from models import BMSProject, BMSMap, BMSField, FieldType, FieldAttribute

def parse_bms_content(app, bms_map: BMSMap, content: str):
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
            full_field_line = _join_continuation_lines(field_lines)
            parse_field_definition(app, bms_map, full_field_line)
            
        elif 'DFHMDI' in line:
            # Parsear propiedades del mapa
            _parse_map_properties(bms_map, line)
            
        i += 1

def _join_continuation_lines(lines: List[str]) -> str:
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

def _parse_map_properties(bms_map: BMSMap, line: str):
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

def parse_field_definition(app, bms_map: BMSMap, line: str):
    """Parsea una definición de campo BMS mejorada"""
    try:
        # Determinar el nombre del campo
        field_name = extract_field_name(app, line)
        
        # Valores por defecto
        line_num = 1
        column = 1
        length = 1
        field_type = FieldType.LABEL
        initial_value = ""
        attributes = []
        
        # Extraer POS
        pos_match = extract_pos(app, line)
        if pos_match:
            line_num, column = pos_match
        
        # Extraer LENGTH
        length_match = extract_length(app, line)
        if length_match:
            length = length_match
            
        # Extraer INITIAL
        initial_match = extract_initial(app, line)
        if initial_match:
            initial_value = initial_match
            
        # Determinar tipo de campo
        field_type = determine_field_type(app, line, initial_value)
        
        # Extraer atributos
        attributes = extract_attributes(app, line)
        
        # Extraer COLOR
        color = extract_color(app, line)
        
        # Extraer HILIGHT
        hilight = extract_hilight(app, line)
        
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

def extract_field_name(app, line: str) -> str:
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
        pos_match = extract_pos(app, line)
        if pos_match:
            line_num, column = pos_match
            return f"FIELD_{line_num}_{column}"
        
        # Si no hay posición, usar índice
        field_count = len(app.current_map.fields) if app.current_map else 0
        return f"FIELD_{field_count + 1}"
    except Exception as e:
        return "UNNAMED_FIELD"

def extract_pos(app, line: str) -> Tuple[int, int] | None:
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

def extract_length(app, line: str) -> int:
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

def extract_initial(app, line: str) -> str:
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

def determine_field_type(app, line: str, initial_value: str) -> FieldType:
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

def extract_attributes(app, line: str) -> list:
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

def extract_color(app, line: str) -> Optional[str]:
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

def extract_hilight(app, line: str) -> Optional[str]:
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
