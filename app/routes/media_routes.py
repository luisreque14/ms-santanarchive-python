from fastapi import APIRouter, Depends
from app.database import get_db
from app.repositories.media_repository import MediaRepository
from app.services.media_service import MediaService
from app.models.media import AlbumPhotoSchema, ConcertVideoSchema
from typing import List

router = APIRouter()

def get_media_service(db=Depends(get_db)):
    return MediaService(MediaRepository(db))

@router.post("/album-photos/", status_code=201)
async def add_album_photo(
    photo: AlbumPhotoSchema, 
    service: MediaService = Depends(get_media_service)
):
    return await service.add_photo_to_album(photo)

@router.post("/concert-videos/", status_code=201)
async def add_concert_video(
    video: ConcertVideoSchema, 
    service: MediaService = Depends(get_media_service)
):
    return await service.add_video_to_concert(video)

@router.get("/concert-videos/{concert_id}")
async def get_videos(
    concert_id: int, 
    service: MediaService = Depends(get_media_service)
):
    return await service.get_concert_multimedia(concert_id)