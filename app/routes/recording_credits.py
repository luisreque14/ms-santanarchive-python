from fastapi import APIRouter, HTTPException
from app.models.recording_credits import RecordingCreditSchema
from app.database import get_db

router = APIRouter()

@router.post("/", status_code=201)
async def add_recording_credit(credit: RecordingCreditSchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # Verificaciones de integridad
    if not await db.albums.find_one({"id": credit.album_id}):
        raise HTTPException(status_code=404, detail="Album not found")
    if not await db.musicians.find_one({"id": credit.musician_id}):
        raise HTTPException(status_code=404, detail="Musician not found")

    await db.recording_credits.insert_one(credit.model_dump())
    return {"message": "Recording credit registered"}


@router.get("/album/{album_id}")
async def get_credits_by_album(album_id: int):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # Retorna la lista de músicos y qué tocaron en ese álbum específico
    cursor = db.recording_credits.find({"album_id": album_id}, {"_id": 0})
    return await cursor.to_list(length=100)