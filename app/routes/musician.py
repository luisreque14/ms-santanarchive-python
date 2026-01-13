from fastapi import APIRouter, HTTPException
from app.models.musician import RoleSchema, MusicianSchema
from app.database import get_db

router = APIRouter()


# --- ENDPOINTS PARA ROLES ---
@router.post("/roles/", status_code=201)
async def create_role(role: RoleSchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    if await db.roles.find_one({"id": role.id}):
        raise HTTPException(status_code=400, detail="Role ID already exists")
    await db.roles.insert_one(role.model_dump())
    return {"message": "Role created successfully"}


@router.get("/roles/")
async def get_roles():
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    return await db.roles.find({}, {"_id": 0}).to_list(length=100)


# --- ENDPOINTS PARA MÚSICOS ---
@router.post("/", status_code=201)
async def create_musician(musician: MusicianSchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")


    # Validar País
    if not await db.countries.find_one({"id": musician.country_id}):
        raise HTTPException(status_code=400, detail="Country not found")

    # Validar Roles
    for r_id in musician.roles:
        if not await db.roles.find_one({"id": r_id}):
            raise HTTPException(status_code=400, detail=f"Role ID {r_id} not found")

    await db.musicians.insert_one(musician.model_dump())
    return {"message": "Musician created successfully"}


@router.get("/")
async def get_musicians():
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # Traemos todos los músicos omitiendo el _id interno de Mongo
    return await db.musicians.find({}, {"_id": 0}).to_list(length=100)