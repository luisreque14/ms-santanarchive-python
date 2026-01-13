from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from datetime import date

class RoleSchema(BaseModel):
    id: int
    name: str
    category: Optional[str] = None

class MusicianSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    nickname: Optional[str] = Field(None, alias="apelativo")
    country_id: int
    start_date: date
    end_date: Optional[date] = None
    roles: List[int]
    bio: Optional[str] = None

    class Config:
        populate_by_name = True


# Schema contenedor para validación masiva
class SantanaBandData(BaseModel):
    roles: List[RoleSchema]
    musicians: List[MusicianSchema]


raw_data = {
    "roles": [
        {"id": 1, "name": "Guitar", "category": "Strings"},
        {"id": 2, "name": "Vocals", "category": "Vocals"},
        {"id": 3, "name": "Percussion", "category": "Percussion"},
        {"id": 7, "name": "Drums", "category": "Percussion"},
        {"id": 8, "name": "Timbales", "category": "Percussion"}
    ],
    "musicians": [
        {
            "id": 1,
            "first_name": "Carlos",
            "last_name": "Santana",
            "apelativo": "Devadip",
            "country_id": 10,
            "start_date": "1966-01-01",
            "end_date": None,
            "roles": [1, 2, 3]
        },
        {
            "id": 4,
            "first_name": "Jose",
            "last_name": "Areas",
            "apelativo": "Chepito",
            "country_id": 5,
            "start_date": "1969-01-01",
            "end_date": "1977-12-31",
            "roles": [3, 8]
        }
    ]
}


# --- SCRIPT DE VALIDACIÓN Y PRUEBA ---

def validate_and_show():
    try:
        # Validar todo el objeto contra el schema
        band_data = SantanaBandData(**raw_data)
        print("✅ Validación exitosa: Los datos cumplen con el schema.\n")

        # Crear un mapa de roles para búsqueda rápida por ID
        role_map = {r.id: r.name for r in band_data.roles}

        print("--- Listado de Músicos ---")
        for m in band_data.musicians:
            # Obtener nombres de roles usando los IDs
            role_names = [role_map.get(rid) for rid in m.roles]

            status = "Present" if m.end_date is None else str(m.end_date)
            nickname_str = f" ({m.nickname})" if m.nickname else ""

            print(f"Músico: {m.first_name} {m.last_name}{nickname_str}")
            print(f"  Roles: {', '.join(role_names)}")
            print(f"  Periodo: {m.start_date} -> {status}")
            print("-" * 30)

    except ValidationError as e:
        print("❌ Error de validación:")
        print(e.json())


if __name__ == "__main__":
    validate_and_show()