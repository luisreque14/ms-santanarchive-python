from fastapi import APIRouter, HTTPException
from app.models.performance_credits import PerformanceCreditSchema
from app.database import get_db

router = APIRouter()


@router.post("/", status_code=201)
async def add_performance_credit(credit: PerformanceCreditSchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # 1. Validar Concierto
    if not await db.concerts.find_one({"id": credit.concert_id}):
        raise HTTPException(status_code=404, detail="Concert not found")

    # 2. Validar Músico
    if not await db.musicians.find_one({"id": credit.musician_id}):
        raise HTTPException(status_code=404, detail="Musician not found")

    await db.performance_credits.insert_one(credit.model_dump())
    return {"message": "Performance credit registered successfully"}


@router.get("/concert/{concert_id}")
async def get_credits_by_concert(concert_id: int):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    cursor = db.performance_credits.find({"concert_id": concert_id}, {"_id": 0})
    return await cursor.to_list(length=100)