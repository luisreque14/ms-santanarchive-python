from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from app.models.concert import ConcertSchema
from app.models.performance_credits import PerformanceCreditSchema
from app.database import get_db

router = APIRouter()


@router.post("/", status_code=201)
async def create_concert(concert: ConcertSchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # Validar que la ciudad exista
    if not await db.cities.find_one({"id": concert.city_id}):
        raise HTTPException(status_code=400, detail="City not found")

    await db.concerts.insert_one(concert.model_dump())
    return {"message": "Concert registered"}


@router.post("/performance-credits/", status_code=201)
async def add_performance_credit(credit: PerformanceCreditSchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # Validar existencia de concierto y músico
    if not await db.concerts.find_one({"id": credit.concert_id}):
        raise HTTPException(status_code=404, detail="Concert not found")
    if not await db.musicians.find_one({"id": credit.musician_id}):
        raise HTTPException(status_code=404, detail="Musician not found")

    await db.performance_credits.insert_one(credit.model_dump())
    return {"message": "Performance credit added"}


@router.get("", response_model=List[dict])  # Usamos dict para manejar los campos agregados
async def get_concerts(year: Optional[str] = None):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # Si no hay año en la URL, usamos el año actual (ej: "2026")
    search_year = year if year and year != "all" else str(datetime.now().year)

    pipeline = [
        # 1. Filtramos por año primero para optimizar la búsqueda
        {
            "$match": {
                "$expr": {
                    "$eq": [{"$dateToString": {"format": "%Y", "date": "$date"}}, search_year]
                }
            }
        },
        # 2. Join con ciudades
        {
            "$lookup": {
                "from": "cities",
                "localField": "city_id",
                "foreignField": "_id",
                "as": "location"
            }
        },
        {"$unwind": "$location"},
        {
            "$project": {
                "id": 1,
                "date": 1,
                "venue": 1,
                "city": "$location.name",
                "country": "$location.country",
                "year": {"$dateToString": {"format": "%Y", "date": "$date"}}
            }
        }
    ]

    concerts = await db.concerts.aggregate(pipeline).to_list(length=100)
    return concerts