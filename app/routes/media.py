from fastapi import APIRouter, HTTPException
from app.models.media import AlbumPhotoSchema, ConcertVideoSchema
from app.database import get_db

router = APIRouter()


@router.post("/album-photos/", status_code=201)
async def add_album_photo(photo: AlbumPhotoSchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # Validamos que el álbum exista antes de asociar la foto
    if not await db.albums.find_one({"id": photo.album_id}):
        raise HTTPException(status_code=404, detail="Album not found")

    await db.album_photos.insert_one(photo.model_dump())
    return {"message": "Photo URL added to album"}


@router.post("/concert-videos/", status_code=201)
async def add_concert_video(video: ConcertVideoSchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # Validamos que el concierto exista
    if not await db.concerts.find_one({"id": video.concert_id}):
        raise HTTPException(status_code=404, detail="Concert not found")

    await db.concert_videos.insert_one(video.model_dump())
    return {"message": "Video URL added to concert"}


@router.get("/concert-videos/{concert_id}")
async def get_videos_by_concert(concert_id: int):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    videos = await db.concert_videos.find({"concert_id": concert_id}, {"_id": 0}).to_list(10)
    return videos