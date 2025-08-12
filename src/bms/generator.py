"""
Generador de código BMS desde modelos
"""
from typing import List, Optional
import sys
import os
from pathlib import Path

# Añadir src al path para imports  
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from models import BMSProject, BMSMap, BMSField
import re


class BMSGenerator:
    """Clase para generar código BMS desde modelos"""
    
    def __init__(self):
        self.templates = self._load_templates()
        
    def _load_templates(self) -> dict:
        """Carga plantillas de código BMS"""
        return {
            "mapset_header": "{mapset_name:<8} DFHMSD TYPE=&SYSPARM,MODE={mode},LANG={lang},          *\n               TERM={term},CTRL=({ctrl}),STORAGE={storage}",
            "map_header": "{map_name:<8} DFHMDI SIZE=({lines},{cols})",
            "mapset_footer": "         DFHMSD TYPE=FINAL\n         END"
        }
        
    def generate_map_code(self, bms_map: BMSMap) -> str:
        """Genera el código BMS para un mapa específico"""
        if not bms_map:
            return ""
            
        lines = []
        
        # Cabecera del mapset
        ctrl_str = ",".join(bms_map.ctrl) if bms_map.ctrl else "FREEKB,FRSET"
        header = self.templates["mapset_header"].format(
            mapset_name=bms_map.mapset_name,
            mode=bms_map.mode,
            lang=bms_map.lang,
            term=bms_map.term,
            ctrl=ctrl_str,
            storage=bms_map.storage
        ).strip()
        lines.append(header)
        
        # Cabecera del mapa
        map_header = self.templates["map_header"].format(
            map_name=bms_map.name,
            lines=bms_map.size[0],
            cols=bms_map.size[1]
        ).strip()
        lines.append(map_header)
        
        # Título si existe
        if bms_map.title:
            lines.append(f"*        TITLE: {bms_map.title}")
            
        # Campos ordenados por posición
        sorted_fields = sorted(bms_map.fields, key=lambda f: (f.line, f.column))
        
        for field in sorted_fields:
            field_code = self.generate_field_code(field)
            lines.append(field_code)
            
        # Pie del mapset
        footer = self.templates["mapset_footer"].strip()
        lines.append(footer)
        
        return "\n".join(lines)
        
    def generate_field_code(self, field: BMSField) -> str:
        """Genera el código BMS para un campo específico"""
        if not field:
            return ""
            
        # Determinar si el nombre es automático (generado por la aplicación)
        is_auto_generated_name = self._is_auto_generated_name(field.name)
        
        # Usar nombre solo si no es generado automáticamente
        field_name = "" if is_auto_generated_name else field.name
        
        # Construir la línea completa del campo
        return self._build_field_line(field_name, field)
        
    def _build_field_line(self, field_name: str, field: BMSField) -> str:
        """Construye la línea BMS para un campo, manejando continuaciones"""
        
        # Construir parámetros base
        pos_param = f"POS=({field.line},{field.column})"
        length_param = f"LENGTH={field.length}"
        
        # Construir parámetros adicionales
        params = []
        
        # INITIAL siempre va primero después de LENGTH
        if field.initial_value:
            escaped_value = field.initial_value.replace("'", "''")
            params.append(f"INITIAL='{escaped_value}'")
            
        # ATTRB
        if field.attributes:
            attrs = []
            for attr in field.attributes:
                if hasattr(attr, 'value'):
                    attrs.append(attr.value)
                else:
                    attrs.append(str(attr))
            if attrs:
                params.append(f"ATTRB=({','.join(attrs)})")
                
        # PICIN y PICOUT
        if field.picin:
            params.append(f"PICIN='{field.picin}'")
        if field.picout:
            params.append(f"PICOUT='{field.picout}'")
            
        # COLOR
        if field.color:
            params.append(f"COLOR={field.color}")
            
        # HILIGHT
        if field.hilight:
            params.append(f"HILIGHT={field.hilight}")
        
        # Construir línea base
        base_params = f"{pos_param},{length_param}"
        if params:
            all_params = base_params + "," + ",".join(params)
        else:
            all_params = base_params
            
        # Determinar formato según nombre y longitud
        if field_name:
            # Campo con nombre: "NOMBRE   DFHMDF ..."
            prefix = f"{field_name:<8} DFHMDF "
        else:
            # Campo sin nombre: "         DFHMDF ..."
            prefix = "         DFHMDF "
            
        full_line = prefix + all_params
        
        # Verificar si necesita continuación (línea > 71 caracteres)
        if len(full_line) > 71:
            # Necesita continuación - dividir los parámetros
            return self._build_continuation_line(prefix, base_params, params)
        else:
            return full_line
            
    def _build_continuation_line(self, prefix: str, base_params: str, additional_params: list) -> str:
        """Construye una línea con continuación BMS"""
        
        # Primera línea: DFHMDF + parámetros básicos + primer parámetro adicional si cabe
        first_line = prefix + base_params
        
        remaining_params = additional_params[:]
        
        # Intentar agregar parámetros a la primera línea hasta llegar al límite
        while remaining_params:
            next_param = remaining_params[0]
            test_line = first_line + "," + next_param
            
            # Dejar espacio para ",          *" (12 caracteres)
            if len(test_line) + 12 <= 71:
                first_line = test_line
                remaining_params.pop(0)
            else:
                break
        
        # Si quedan parámetros, crear línea de continuación
        if remaining_params:
            first_line += ",          *"
            continuation_line = f"               {','.join(remaining_params)}"
            return first_line + "\n" + continuation_line
        else:
            return first_line
        
    def validate_map(self, bms_map: BMSMap) -> List[str]:
        """Valida un mapa BMS y retorna lista de errores"""
        errors = []
        
        if not bms_map:
            errors.append("Mapa no puede ser None")
            return errors
            
        # Validar nombre del mapa
        if not bms_map.name or not self._is_valid_name(bms_map.name):
            errors.append("Nombre del mapa inválido (debe ser alfanumérico, máximo 8 caracteres)")
            
        # Validar nombre del mapset
        if not bms_map.mapset_name or not self._is_valid_name(bms_map.mapset_name):
            errors.append("Nombre del mapset inválido (debe ser alfanumérico, máximo 8 caracteres)")
            
        # Validar tamaño
        if bms_map.size[0] < 1 or bms_map.size[0] > 24:
            errors.append("Número de líneas debe estar entre 1 y 24")
            
        if bms_map.size[1] < 1 or bms_map.size[1] > 80:
            errors.append("Número de columnas debe estar entre 1 y 80")
            
        # Validar campos
        field_names = set()
        for i, field in enumerate(bms_map.fields):
            field_errors = self.validate_field(field, bms_map.size)
            errors.extend([f"Campo {i+1}: {err}" for err in field_errors])
            
            # Verificar nombres únicos
            if field.name in field_names:
                errors.append(f"Nombre de campo duplicado: {field.name}")
            field_names.add(field.name)
            
        return errors
        
    def validate_field(self, field: BMSField, map_size: tuple) -> List[str]:
        """Valida un campo BMS"""
        errors = []
        
        if not field:
            errors.append("Campo no puede ser None")
            return errors
            
        # Validar nombre
        if not field.name or not self._is_valid_name(field.name):
            errors.append("Nombre del campo inválido")
            
        # Validar posición
        if field.line < 1 or field.line > map_size[0]:
            errors.append(f"Línea fuera de rango (1-{map_size[0]})")
            
        if field.column < 1 or field.column > map_size[1]:
            errors.append(f"Columna fuera de rango (1-{map_size[1]})")
            
        # Validar longitud
        if field.length < 1:
            errors.append("Longitud debe ser mayor a 0")
            
        # Verificar que el campo no se salga de la pantalla
        if field.column + field.length - 1 > map_size[1]:
            errors.append("Campo se extiende más allá del ancho de la pantalla")
            
        return errors
        
    def _is_valid_name(self, name: str) -> bool:
        """Valida si un nombre es válido para BMS (alfanumérico, max 8 chars)"""
        if not name or len(name) > 8:
            return False
        return re.match(r'^[A-Za-z][A-Za-z0-9]*$', name) is not None

    def _is_auto_generated_name(self, name: str) -> bool:
        """Determina si un nombre de campo es generado automáticamente por la aplicación"""
        if not name:
            return True
            
        # Patrones de nombres automáticos generados por la aplicación:
        
        # 1. FIELD01, FIELD02, etc. (del parser estructurado)
        if re.match(r'^FIELD\d{2}$', name):
            return True
            
        # 2. CAMPO01, CAMPO02, etc. (de nuevo campo manual)
        if re.match(r'^CAMPO\d{2}$', name):
            return True
            
        # 3. FIELD_línea_columna (de parsing legacy sin nombre)
        if re.match(r'^FIELD_\d+_\d+$', name):
            return True
            
        # 4. Nombres genéricos
        if name in ['UNNAMED', 'UNNAMED_FIELD', 'FIELD', 'CAMPO']:
            return True
            
        # 5. Nombres que empiecen con prefijos específicos de generación automática
        # Solo consideramos patrones específicos, no cualquier cosa que empiece con estos prefijos
        if re.match(r'^AUTO_[A-Z0-9_]+$', name):
            return True
            
        if re.match(r'^GEN_[A-Z0-9_]+$', name):
            return True
            
        return False
