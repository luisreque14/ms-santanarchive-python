from fastapi import APIRouter, HTTPException, Depends
from app.dtos.recording_credit_dto import RecordingCreditDto
from app.database import get_db
from typing import List

router = APIRouter(prefix="/recording-credits", tags=["Recording Credits"])

@router.post(
    "/", 
    status_code=201,
    response_model=RecordingCreditDto,
    response_model_by_alias=True
)
async def add_recording_credit(
    credit: RecordingCreditDto, 
    db = Depends(get_db)
):
    """
    Registers a musician's participation in a studio album.
    Ensures referential integrity for album and musician IDs.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection error")

    # Verificaciones de integridad usando los campos del DTO
    # Nota: Usamos credit.albumId porque definimos ese nombre en el DTO
    if not await db.albums.find_one({"id": credit.albumId}):
        raise HTTPException(status_code=404, detail="Album not found")
        
    if not await db.musicians.find_one({"id": credit.musicianId}):
        raise HTTPException(status_code=404, detail="Musician not found")

    # Usamos by_alias=False para guardar en la BD con los nombres originales (snake_case)
    await db.recording_credits.insert_one(credit.model_dump(by_alias=False))
    return credit


@router.get(
    "/album/{album_id}", 
    response_model=List[RecordingCreditDto],
    response_model_by_alias=True
)
async def get_credits_by_album(
    album_id: int, 
    db = Depends(get_db)
):
    """
    Returns the list of musicians and instruments for a specific album.
    Output is automatically formatted to camelCase.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection error")

    cursor = db.recording_credits.find({"album_id": album_id}, {"_id": 0})
    credits_db = await cursor.to_list(length=100)
    
    # Validamos cada resultado contra el DTO para asegurar la transformación de alias
    return [RecordingCreditDto.model_validate(c) for c in credits_db]