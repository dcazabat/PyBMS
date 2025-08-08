"""
Modelos de datos para el BMS Generator
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class FieldType(Enum):
    """Tipos de campo BMS"""
    LABEL = "LABEL"
    INPUT = "INPUT"  
    OUTPUT = "OUTPUT"
    PROTECTED = "PROTECTED"
    NUMERIC = "NUMERIC"
    UNPROTECTED = "UNPROTECTED"


class FieldAttribute(Enum):
    """Atributos de campo BMS"""
    ASKIP = "ASKIP"  # Auto skip
    PROT = "PROT"    # Protected
    UNPROT = "UNPROT"  # Unprotected
    NUM = "NUM"      # Numeric
    BRT = "BRT"      # Bright
    NORM = "NORM"    # Normal
    DRK = "DRK"      # Dark
    IC = "IC"        # Insert cursor
    FSET = "FSET"    # Field set


@dataclass
class BMSField:
    """Representa un campo en un mapa BMS"""
    name: str
    line: int
    column: int
    length: int
    field_type: FieldType = FieldType.UNPROTECTED
    attributes: List[FieldAttribute] = field(default_factory=list)
    initial_value: str = ""
    picture: Optional[str] = None
    justify: str = "LEFT"  # LEFT, RIGHT, CENTER
    color: Optional[str] = None  # COLOR=RED, COLOR=BLUE, etc.
    hilight: Optional[str] = None  # HILIGHT=UNDERLINE, HILIGHT=BLINK, etc.
    
    def to_bms_code(self) -> str:
        """Genera el código BMS para este campo"""
        attrs = ",".join([attr.value for attr in self.attributes])
        attr_str = f"ATTRB=({attrs})" if attrs else ""
        
        initial_str = f",INITIAL='{self.initial_value}'" if self.initial_value else ""
        picture_str = f",PICIN='{self.picture}'" if self.picture else ""
        
        return f"{self.name} DFHMDF POS=({self.line},{self.column}),LENGTH={self.length}{attr_str}{initial_str}{picture_str}"


@dataclass  
class BMSMap:
    """Representa un mapa BMS completo"""
    name: str
    mapset_name: str
    size: tuple[int, int] = (24, 80)  # líneas, columnas por defecto
    fields: List[BMSField] = field(default_factory=list)
    title: str = ""
    mode: str = "INOUT"  # IN, OUT, INOUT
    lang: str = "COBOL"  # COBOL, PLI, ASM
    term: str = "3270-2"
    ctrl: List[str] = field(default_factory=list)
    storage: str = "AUTO"
    
    def add_field(self, bms_field: BMSField) -> None:
        """Añade un campo al mapa"""
        self.fields.append(bms_field)
        
    def remove_field(self, field_name: str) -> bool:
        """Elimina un campo del mapa por nombre"""
        for i, field in enumerate(self.fields):
            if field.name == field_name:
                del self.fields[i]
                return True
        return False
        
    def get_field(self, field_name: str) -> Optional[BMSField]:
        """Obtiene un campo por nombre"""
        for field in self.fields:
            if field.name == field_name:
                return field
        return None
        
    def to_bms_code(self) -> str:
        """Genera el código BMS completo para este mapa"""
        lines = []
        
        # Cabecera del mapset
        lines.append(f"{self.mapset_name} DFHMSD TYPE=&SYSPARM,MODE={self.mode},LANG={self.lang},")
        lines.append(f"           TERM={self.term},CTRL=({','.join(self.ctrl)}),STORAGE={self.storage}")
        
        # Definición del mapa
        lines.append(f"{self.name} DFHMDI SIZE=({self.size[0]},{self.size[1]})")
        
        if self.title:
            lines.append(f"*        TITLE: {self.title}")
            
        # Campos
        for field in self.fields:
            lines.append(f"         {field.to_bms_code()}")
            
        # Fin del mapa y mapset
        lines.append(f"         DFHMSD TYPE=FINAL")
        lines.append("         END")
        
        return "\n".join(lines)


@dataclass
class BMSProject:
    """Representa un proyecto completo de mapas BMS"""
    name: str
    maps: List[BMSMap] = field(default_factory=list)
    description: str = ""
    created_date: str = ""
    modified_date: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def add_map(self, bms_map: BMSMap) -> None:
        """Añade un mapa al proyecto"""
        self.maps.append(bms_map)
        
    def get_map(self, map_name: str) -> Optional[BMSMap]:
        """Obtiene un mapa por nombre"""
        for bms_map in self.maps:
            if bms_map.name == map_name:
                return bms_map
        return None
        
    def remove_map(self, map_name: str) -> bool:
        """Elimina un mapa del proyecto"""
        for i, bms_map in enumerate(self.maps):
            if bms_map.name == map_name:
                del self.maps[i]
                return True
        return False
