from pydantic import BaseModel, Field, ConfigDict, ValidationError
from typing import List, Optional
from datetime import date

class RoleSchema(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=2)
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class MusicianSchema(BaseModel):
    id: int = Field(..., gt=0)
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    # Alias "apelativo" se mantiene para compatibilidad con datos externos
    nickname: Optional[str] = Field(None, alias="apelativo")
    country_id: int
    start_date: date
    end_date: Optional[date] = None
    roles: List[int] = Field(default_factory=list)
    bio: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True  # Sustituye al antiguo 'allow_population_by_field_name'
    )

class SantanaBandData(BaseModel):
    roles: List[RoleSchema]
    musicians: List[MusicianSchema]

    model_config = ConfigDict(from_attributes=True)

# --- SCRIPT DE VALIDACIÓN (Actualizado) ---

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

def validate_and_show():
    try:
        # Pydantic v2 maneja la instanciación igual, pero es más rápido
        band_data = SantanaBandData(**raw_data)
        print("✅ Validation successful: Data matches the schema.\n")

        role_map = {r.id: r.name for r in band_data.roles}

        print("--- Musicians List ---")
        for m in band_data.musicians:
            role_names = [role_map.get(rid, "Unknown") for rid in m.roles]
            status = "Present" if m.end_date is None else str(m.end_date)
            # Gracias a populate_by_name=True, podemos usar m.nickname
            nickname_str = f" ({m.nickname})" if m.nickname else ""

            print(f"Musician: {m.first_name} {m.last_name}{nickname_str}")
            print(f"  Roles: {', '.join(role_names)}")
            print(f"  Period: {m.start_date} -> {status}")
            print("-" * 30)

    except ValidationError as e:
        print("❌ Validation Error:")
        print(e.json(indent=2))

if __name__ == "__main__":
    validate_and_show()