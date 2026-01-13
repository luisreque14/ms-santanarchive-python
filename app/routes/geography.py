from typing import List, Optional

from fastapi import APIRouter, HTTPException
from app.models.geography import ContinentSchema, CountrySchema, StateSchema, CitySchema
from app.database import get_db, get_next_sequence_value

router = APIRouter()

@router.post("/continents/", status_code=201)
async def create_continent(continent: ContinentSchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # Verificamos si ya existe el ID
    existing = await db.continents.find_one({"id": continent.id})
    if existing:
        raise HTTPException(status_code=400, detail="Continent ID already exists")

    # Insertamos en MongoDB
    new_continent = await db.continents.insert_one(continent.model_dump())
    return {"message": "Continent created successfully", "id": continent.id}


@router.get("/continents/")
async def get_continents():
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    continents = []
    cursor = db.continents.find({}, {"_id": 0})  # Excluimos el _id de Mongo para el frontend
    async for document in cursor:
        continents.append(document)
    return continents


@router.post("/countries/", status_code=201)
async def create_country(country: CountrySchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # 1. Validar que el continente exista
    continent = await db.continents.find_one({"id": country.continent_id})
    if not continent:
        raise HTTPException(
            status_code=400,
            detail=f"Continent with id {country.continent_id} does not exist"
        )

    # 2. Validar que el país no exista ya (por ID)
    existing = await db.countries.find_one({"id": country.id})
    if existing:
        raise HTTPException(status_code=400, detail="Country ID already exists")

    # 3. Insertar
    await db.countries.insert_one(country.model_dump())
    return {"message": "Country created successfully", "id": country.id}


@router.get("/countries/")
async def get_countries(continent_id: Optional[int] = None):
    db = get_db()
    query = {"continent_id": continent_id} if continent_id else {}

    # Traemos los documentos completos para tener ID y Name
    cursor = db.countries.find(query, {"_id": 0})
    return await cursor.to_list(length=None)


@router.post("/states/", status_code=201)
async def create_state(state: StateSchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # Validar que el país existe
    if not await db.countries.find_one({"id": state.country_id}):
        raise HTTPException(status_code=400, detail="Country not found")

    state_data = state.model_dump()
    state_data["id"] = await get_next_sequence_value("state_id")

    await db.states.insert_one(state_data)
    return {"message": "State created"}


# --- RUTAS PARA CIUDADES ---
@router.post("/cities/", status_code=201)
async def create_city(city: CitySchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # 1. Validar País
    if not await db.countries.find_one({"id": city.country_id}):
        raise HTTPException(status_code=400, detail="Country not found")

    # 2. Validar Estado (solo si se envió un state_id)
    if city.state_id is not None:
        if not await db.states.find_one({"id": city.state_id}):
            raise HTTPException(status_code=400, detail="State not found")

    await db.cities.insert_one(city.model_dump())
    return {"message": "City created"}


@router.get("/states/")
async def get_states():
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    states = []
    async for doc in db.states.find({}, {"_id": 0}):
        states.append(doc)
    return states

@router.get("/cities/")
async def get_cities(country_id: Optional[int] = None):
    db = get_db()
    query = {"country_id": country_id} if country_id else {}

    cursor = db.cities.find(query, {"_id": 0})
    return await cursor.to_list(length=None)