# parsing.py: Funciones de parseo de archivos BMS según especificaciones IBM

import re
from typing import List, Optional, Tuple, Dict
from models import BMSProject, BMSMap, BMSField, FieldType, FieldAttribute

def parse_bms_content(app, bms_map: BMSMap, content: str):
    """
    Parsea el contenido de un archivo BMS completo según especificaciones IBM:
    - Pos 1-9: Nombre del label (vacío para labels, 8 caracteres para campos)
    - Pos 10-15: DFHMSD, DFHMDI, DFHMDF según corresponda
    - Pos 16-71: Parámetros y valores
    - Pos 72: '*' o '-' para continuación en línea siguiente (pos 15)
    """
    lines = content.split('\n')
    
    i = 0
    current_mapset_name = None
    
    while i < len(lines):
        line = lines[i] if i < len(lines) else ""
        
        # Ignorar líneas vacías y comentarios (líneas que empiezan con * en pos 1)
        if not line.strip() or (line.startswith('*') and len(line.strip()) > 0):
            i += 1
            continue
            
        # Analizar la estructura de la línea según posiciones BMS
        line_info = _parse_bms_line_structure(line)
        
        if not line_info:
            i += 1
            continue
            
        # Procesar líneas con continuación
        if _has_continuation(line):
            continuation_lines = [line]
            i += 1
            
            # Recopilar todas las líneas de continuación
            while i < len(lines) and _is_continuation_line(lines[i]):
                continuation_lines.append(lines[i])
                if not _has_continuation(lines[i]):
                    break
                i += 1
            
            # Unir líneas de continuación
            full_line = _join_bms_continuation_lines(continuation_lines)
            line_info = _parse_bms_line_structure(full_line)
            
            # Procesar la línea completa aquí y continuar sin avanzar más el índice
            if line_info:
                directive = line_info['directive']
                
                if directive == 'DFHMSD':
                    # Parsear mapset y propiedades generales
                    current_mapset_name = _parse_mapset_definition(line_info, bms_map)
                    
                elif directive == 'DFHMDI':
                    # Parsear propiedades del mapa
                    _parse_map_definition(line_info, bms_map, current_mapset_name)
                    
                elif directive == 'DFHMDF':
                    # Parsear definición de campo
                    _parse_field_definition_structured(app, bms_map, line_info)
                    
            continue
        
        # Para líneas sin continuación
        if line_info:
            directive = line_info['directive']
            
            if directive == 'DFHMSD':
                # Parsear mapset y propiedades generales
                current_mapset_name = _parse_mapset_definition(line_info, bms_map)
                
            elif directive == 'DFHMDI':
                # Parsear propiedades del mapa
                _parse_map_definition(line_info, bms_map, current_mapset_name)
                
            elif directive == 'DFHMDF':
                # Parsear definición de campo
                _parse_field_definition_structured(app, bms_map, line_info)
                
        i += 1

def _parse_bms_line_structure(line: str) -> Optional[Dict]:
    """
    Analiza la estructura de una línea BMS según posiciones específicas:
    Maneja dos formatos:
    1. Con nombre: "NOMBRE   DFHMDF ..." (nombre en pos 1-9, DFHMDF en pos 10-15)
    2. Sin nombre: "         DFHMDF ..." o "DFHMDF ..." (DFHMDF en pos 10-15 o pos 1)
    """
    if len(line) < 6:  # Mínimo para contener DFHMDF/DFHMDI/DFHMSD
        return None
    
    # Primer intento: formato estándar con nombre (pos 1-9, DFHMDF en pos 10-15)
    if len(line) >= 15:
        label_section = line[0:9].strip()
        directive_section = line[9:16].strip() if len(line) > 15 else line[9:15].strip()
        
        if directive_section in ['DFHMSD', 'DFHMDI', 'DFHMDF']:
            # Para líneas unidas (continuaciones), extraer todos los parámetros sin límite de posición 71
            if len(line) > 200:  # Línea probablemente unida de continuaciones
                parameters_section = line[16:].strip()
                continuation_marker = ""  # Las líneas unidas ya no tienen marcador
            else:
                # Línea normal, respetar límite de posición 71
                parameters_section = line[16:71].strip() if len(line) > 71 else line[16:].strip()
                continuation_marker = line[71:72] if len(line) > 71 else ""
            
            return {
                'label': label_section,
                'directive': directive_section,
                'parameters': parameters_section,
                'continuation': continuation_marker in ['*', '-'],
                'raw_line': line
            }
    
    # Segundo intento: DFHMDF al inicio de la línea (formato compacto)
    if line.strip().startswith(('DFHMSD', 'DFHMDI', 'DFHMDF')):
        parts = line.strip().split(None, 1)  # Dividir en máximo 2 partes
        directive_section = parts[0]
        parameters_section = parts[1] if len(parts) > 1 else ""
        
        # Buscar marcador de continuación al final
        continuation = False
        if len(line) > 71 and line[71] in ['*', '-']:
            continuation = True
        elif parameters_section.endswith(('*', '-')):
            continuation = True
            
        return {
            'label': "",  # Sin nombre de campo
            'directive': directive_section,
            'parameters': parameters_section,
            'continuation': continuation,
            'raw_line': line
        }
        
    return None

def _has_continuation(line: str) -> bool:
    """
    Verifica si una línea tiene marcador de continuación.
    Busca * o - al final de la línea (preferiblemente en pos 72, pero puede estar en otras posiciones)
    """
    line_stripped = line.rstrip()
    
    # Si la línea termina con * o -, tiene continuación
    if line_stripped.endswith('*') or line_stripped.endswith('-'):
        return True
        
    # Verificación adicional: si hay exactamente posición 72 con marcador
    if len(line) > 71 and line[71] in ['*', '-']:
        return True
        
    return False

def _is_continuation_line(line: str) -> bool:
    """
    Verifica si una línea es continuación de la anterior.
    Las líneas de continuación tienen:
    - Posiciones 1-15: espacios en blanco
    - Posición 16+: contenido de continuación
    """
    if not line.strip():
        return False
    
    # Una línea de continuación debe tener espacios en posiciones 1-15 y contenido después
    if len(line) >= 16:
        return line[0:15].strip() == "" and line[15:].strip() != ""
    
    return False

def _join_bms_continuation_lines(lines: List[str]) -> str:
    """
    Une líneas de continuación BMS respetando las posiciones:
    - Primera línea: completa
    - Líneas siguientes: desde posición 15, separadas por comas
    """
    if not lines:
        return ""
        
    if len(lines) == 1:
        # Remover marcador de continuación si existe
        line = lines[0]
        if len(line) > 71 and line[71] in ['*', '-']:
            return line[:71].rstrip()
        return line
        
    # Primera línea (sin marcador de continuación)
    result = lines[0][:71].rstrip() if len(lines[0]) > 71 else lines[0].rstrip()
    
    # Líneas de continuación (desde posición 15)
    for cont_line in lines[1:]:
        if len(cont_line) >= 15:
            # Extraer contenido completo de continuación (sin límite de posición 71)
            cont_content = cont_line[14:].strip()
            if cont_content:
                # Agregar coma si no está presente y hay contenido
                if not result.endswith(',') and not cont_content.startswith(','):
                    result += ","
                result += cont_content
                
    return result

def _parse_mapset_definition(line_info: Dict, bms_map: BMSMap) -> Optional[str]:
    """Parsea definición DFHMSD para obtener nombre del mapset y propiedades"""
    try:
        mapset_name = line_info['label'] if line_info['label'] else "MAPSET01"
        parameters = line_info['parameters']
        
        # Actualizar el mapset del mapa
        if mapset_name:
            bms_map.mapset_name = mapset_name
            
        # Parsear parámetros adicionales del mapset si es necesario
        # TYPE=&SYSPARM, MODE=INOUT, LANG=COBOL, etc.
        
        return mapset_name
        
    except Exception as e:
        return None

def _parse_map_definition(line_info: Dict, bms_map: BMSMap, mapset_name: Optional[str]):
    """Parsea definición DFHMDI para obtener nombre del mapa y propiedades"""
    try:
        map_name = line_info['label'] if line_info['label'] else bms_map.name
        parameters = line_info['parameters']
        
        # Actualizar nombre del mapa
        if map_name:
            bms_map.name = map_name
            
        # Parsear SIZE si está presente
        size_match = re.search(r'SIZE=\((\d+),(\d+)\)', parameters)
        if size_match:
            rows = int(size_match.group(1))
            cols = int(size_match.group(2))
            bms_map.size = (rows, cols)
            
        # Asignar mapset si está disponible
        if mapset_name:
            bms_map.mapset_name = mapset_name
            
    except Exception as e:
        pass

def _parse_field_definition_structured(app, bms_map: BMSMap, line_info: Dict):
    """
    Parsea una definición de campo DFHMDF usando estructura posicional:
    - Label: nombre del campo (pos 1-9)
    - Parameters: POS, LENGTH, INITIAL, ATTRB, COLOR (pos 16-71)
    """
    try:
        # Nombre del campo desde el label o generar uno
        field_name = line_info['label'] if line_info['label'] else _generate_field_name(bms_map)
        
        # Validar nombre del campo
        if not field_name or len(field_name) > 8:
            field_name = _generate_field_name(bms_map)
            
        parameters = line_info['parameters']
        
        # Valores por defecto
        line_num = 1
        column = 1
        length = 1
        field_type = FieldType.LABEL
        initial_value = ""
        attributes = []
        color = None
        hilight = None
        picin = None
        picout = None
        
        # Parsear parámetros específicos
        pos_result = _extract_pos_structured(parameters)
        if pos_result:
            line_num, column = pos_result
            
        length = _extract_length_structured(parameters)
        initial_value = _extract_initial_structured(parameters)
        has_name = bool(line_info['label'])  # Verificar si tiene nombre de campo
        field_type = _determine_field_type_structured(parameters, initial_value, has_name)
        attributes = _extract_attributes_structured(parameters)
        color = _extract_color_structured(parameters)
        hilight = _extract_hilight_structured(parameters)
        picin = _extract_picin_structured(parameters)
        picout = _extract_picout_structured(parameters)
        
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
            
            # Asignar PICIN y PICOUT si están disponibles
            if picin:
                field.picin = picin
            if picout:
                field.picout = picout
                
            bms_map.add_field(field)
            
    except Exception as e:
        # Si hay error en el parseo, continuar con el siguiente campo
        pass

def _generate_field_name(bms_map: BMSMap) -> str:
    """Genera un nombre único para un campo"""
    field_count = len(bms_map.fields) + 1
    return f"FIELD{field_count:02d}"

# ========== FUNCIONES DE EXTRACCIÓN ESTRUCTURADA ==========

def _extract_pos_structured(parameters: str) -> Optional[Tuple[int, int]]:
    """Extrae POS=(línea,columna) de los parámetros"""
    try:
        pos_match = re.search(r'POS=\((\d+),(\d+)\)', parameters)
        if pos_match:
            line_num = int(pos_match.group(1))
            column = int(pos_match.group(2))
            return (line_num, column)
    except:
        pass
    return None

def _extract_length_structured(parameters: str) -> int:
    """Extrae LENGTH=valor de los parámetros"""
    try:
        length_match = re.search(r'LENGTH=(\d+)', parameters)
        if length_match:
            return int(length_match.group(1))
    except:
        pass
    return 1

def _extract_initial_structured(parameters: str) -> str:
    """Extrae INITIAL='valor' de los parámetros"""
    try:
        # Buscar INITIAL='...' o INITIAL="..."
        initial_match = re.search(r"INITIAL=['\"]([^'\"]*)['\"]", parameters)
        if initial_match:
            return initial_match.group(1)
    except Exception:
        pass
    return ""

def _extract_attributes_structured(parameters: str) -> List[FieldAttribute]:
    """Extrae ATTRB=(lista,de,atributos) de los parámetros"""
    attributes = []
    try:
        # Buscar ATTRB=(atrib1,atrib2,atrib3) o ATTRB=atrib
        attrb_match = re.search(r'ATTRB=\(([^)]+)\)', parameters)
        if not attrb_match:
            # Buscar ATTRB=atributo_simple
            attrb_match = re.search(r'ATTRB=([A-Z]+)', parameters)
            
        if attrb_match:
            attrb_text = attrb_match.group(1)
            # Dividir por comas y procesar cada atributo
            attr_list = [attr.strip() for attr in attrb_text.split(',')]
            
            for attr_str in attr_list:
                attr_str = attr_str.strip().upper()
                # Mapear a FieldAttribute
                if attr_str == 'ASKIP':
                    attributes.append(FieldAttribute.ASKIP)
                elif attr_str == 'PROT':
                    attributes.append(FieldAttribute.PROT)
                elif attr_str == 'UNPROT':
                    attributes.append(FieldAttribute.UNPROT)
                elif attr_str == 'NUM':
                    attributes.append(FieldAttribute.NUM)
                elif attr_str == 'BRT':
                    attributes.append(FieldAttribute.BRT)
                elif attr_str == 'NORM':
                    attributes.append(FieldAttribute.NORM)
                elif attr_str == 'DRK':
                    attributes.append(FieldAttribute.DRK)
                elif attr_str == 'IC':
                    attributes.append(FieldAttribute.IC)
                elif attr_str == 'FSET':
                    attributes.append(FieldAttribute.FSET)
    except:
        pass
        
    return attributes

def _extract_color_structured(parameters: str) -> Optional[str]:
    """Extrae COLOR=valor de los parámetros"""
    try:
        color_match = re.search(r'COLOR=([A-Z]+)', parameters)
        if color_match:
            return color_match.group(1).upper()
    except:
        pass
    return None

def _extract_hilight_structured(parameters: str) -> Optional[str]:
    """Extrae HILIGHT=valor de los parámetros"""
    try:
        hilight_match = re.search(r'HILIGHT=([A-Z]+)', parameters)
        if hilight_match:
            return hilight_match.group(1).upper()
    except:
        pass
    return None

def _extract_picin_structured(parameters: str) -> Optional[str]:
    """Extrae PICIN='valor' de los parámetros"""
    try:
        picin_match = re.search(r"PICIN=['\"]([^'\"]*)['\"]", parameters)
        if picin_match:
            return picin_match.group(1)
    except Exception:
        pass
    return None

def _extract_picout_structured(parameters: str) -> Optional[str]:
    """Extrae PICOUT='valor' de los parámetros"""
    try:
        picout_match = re.search(r"PICOUT=['\"]([^'\"]*)['\"]", parameters)
        if picout_match:
            return picout_match.group(1)
    except Exception:
        pass
    return None

def _determine_field_type_structured(parameters: str, initial_value: str, has_name: bool) -> FieldType:
    """
    Determina el tipo de campo basado en la lógica propuesta:
    - Si no tiene nombre y no tiene ATTRB -> LABEL
    - Si tiene ATTRB (independiente del nombre) -> INPUT (puede cargar ATTRB, INITIAL, COLOR, HILIGHT, PICIN, PICOUT)
    - Si tiene PICIN -> INPUT
    - Si tiene valor inicial -> LABEL
    """
    parameters_upper = parameters.upper()
    
    # Si tiene PICIN, definitivamente es un campo de entrada
    if 'PICIN=' in parameters_upper:
        return FieldType.INPUT
        
    # Si tiene ATTRB, es un INPUT (independiente de si tiene nombre o no)
    if 'ATTRB=' in parameters_upper or 'ATTRB(' in parameters_upper:
        return FieldType.INPUT
        
    # Si no tiene nombre y no tiene ATTRB, es un LABEL
    if not has_name and 'ATTRB' not in parameters_upper:
        return FieldType.LABEL
        
    # Si tiene PICOUT pero no PICIN, es de salida
    if 'PICOUT=' in parameters_upper and 'PICIN=' not in parameters_upper:
        return FieldType.OUTPUT
        
    # Si tiene valor inicial, probablemente es una etiqueta
    if initial_value:
        return FieldType.LABEL
        
    # Por defecto, es etiqueta
    return FieldType.LABEL

# ========== FUNCIONES DE COMPATIBILIDAD (LEGACY) ==========
# Mantenemos las funciones antiguas para compatibilidad con código existente

def parse_field_definition(app, bms_map: BMSMap, line: str):
    """Función de compatibilidad - usa el nuevo parser estructurado"""
    # Simular estructura de línea para el nuevo parser
    line_info = {
        'label': '',
        'directive': 'DFHMDF',
        'parameters': line,
        'continuation': False,
        'raw_line': line
    }
    _parse_field_definition_structured(app, bms_map, line_info)

def extract_field_name(app, line: str) -> str:
    """Función de compatibilidad para extraer nombre de campo"""
    try:
        # Buscar patrón tradicional: NOMBRE DFHMDF
        parts = line.split()
        for i, part in enumerate(parts):
            if part == 'DFHMDF' and i > 0:
                potential_name = parts[i-1]
                if (len(potential_name) <= 8 and 
                    potential_name.replace('_', '').replace('-', '').isalnum()):
                    return potential_name
                break
        
        # Fallback: generar nombre basado en posición
        if app.current_map:
            return _generate_field_name(app.current_map)
        return "FIELD01"
        
    except:
        return "UNNAMED"

def extract_pos(app, line: str) -> Optional[Tuple[int, int]]:
    """Función de compatibilidad para extraer posición"""
    return _extract_pos_structured(line)

def extract_length(app, line: str) -> int:
    """Función de compatibilidad para extraer longitud"""
    return _extract_length_structured(line)

def extract_initial(app, line: str) -> str:
    """Función de compatibilidad para extraer valor inicial"""
    return _extract_initial_structured(line)

def determine_field_type(app, line: str, initial_value: str) -> FieldType:
    """Función de compatibilidad para determinar tipo de campo"""
    return _determine_field_type_structured(line, initial_value)

def extract_attributes(app, line: str) -> List[FieldAttribute]:
    """Función de compatibilidad para extraer atributos"""
    return _extract_attributes_structured(line)

def extract_color(app, line: str) -> Optional[str]:
    """Función de compatibilidad para extraer color"""
    return _extract_color_structured(line)

def extract_hilight(app, line: str) -> Optional[str]:
    """Función de compatibilidad para extraer hilight"""
    return _extract_hilight_structured(line)
