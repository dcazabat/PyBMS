"""
Generador de código BMS
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
            "mapset_header": """
{mapset_name} DFHMSD TYPE=&SYSPARM,MODE={mode},LANG={lang},
           TERM={term},CTRL=({ctrl}),STORAGE={storage}
""",
            "map_header": """
{map_name} DFHMDI SIZE=({lines},{cols})
""",
            "field_template": """
         {name} DFHMDF POS=({line},{col}),LENGTH={length}{attributes}{initial}{picture}
""",
            "mapset_footer": """
         DFHMSD TYPE=FINAL
         END
"""
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
        is_auto_generated_name = (
            field.name.startswith("FIELD_") and 
            "_" in field.name and 
            all(part.isdigit() for part in field.name.split("_")[1:])
        )
        
        # Usar nombre solo si no es generado automáticamente
        field_name = "" if is_auto_generated_name else field.name
        
        # Construir atributos
        attributes_str = ""
        if field.attributes:
            attrs = [attr.value for attr in field.attributes]
            attributes_str = f",ATTRB=({','.join(attrs)})"
            
        # Valor inicial
        initial_str = ""
        if field.initial_value:
            # Escapar comillas simples
            escaped_value = field.initial_value.replace("'", "''")
            initial_str = f",INITIAL='{escaped_value}'"
            
        # Picture (PICIN y PICOUT)
        picture_str = ""
        if field.picin:
            picture_str += f",PICIN='{field.picin}'"
        if field.picout:
            picture_str += f",PICOUT='{field.picout}'"
            
        # Color
        color_str = ""
        if field.color:
            color_str = f",COLOR={field.color}"
            
        # Hilight
        hilight_str = ""
        if field.hilight:
            hilight_str = f",HILIGHT={field.hilight}"
            
        # Determinar si necesitamos línea de continuación
        base_line = f"DFHMDF POS=({field.line},{field.column}),LENGTH={field.length}{attributes_str}{initial_str}{picture_str}{color_str}{hilight_str}"
        
        # Si la línea es muy larga (>72 caracteres), usar continuación
        if len(base_line) > 65:  # Dejar espacio para nombre y continuación
            # Línea principal
            main_parts = f"DFHMDF POS=({field.line},{field.column}),LENGTH={field.length}"
            if field.initial_value:
                main_parts += initial_str
            
            # Línea de continuación
            continuation_parts = []
            if field.attributes:
                continuation_parts.append(attributes_str.lstrip(','))
            if field.picin:
                continuation_parts.append(f"PICIN='{field.picin}'")
            if field.picout:
                continuation_parts.append(f"PICOUT='{field.picout}'")
            if field.color:
                continuation_parts.append(color_str.lstrip(','))
            if field.hilight:
                continuation_parts.append(hilight_str.lstrip(','))
                
            if field_name:
                # Campo con nombre real y continuación
                field_line = f"{field_name:8} {main_parts}"
                if continuation_parts:
                    field_line += ",          *\n"
                    field_line += f"               {','.join(continuation_parts)}"
            else:
                # Campo sin nombre y continuación
                field_line = f"         {main_parts}"
                if continuation_parts:
                    field_line += ",          *\n"
                    field_line += f"               {','.join(continuation_parts)}"
        else:
            # Línea simple
            if field_name:
                # Campo con nombre real
                field_line = f"{field_name:8} {base_line}"
            else:
                # Campo sin nombre (usar espacios para alineación)
                field_line = f"         {base_line}"
            
        return field_line
        
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
