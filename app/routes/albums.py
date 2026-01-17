from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.repositories.album_repository import AlbumRepository
from app.services.album_service import AlbumService
from app.models.album import AlbumSchema
from typing import List

router = APIRouter()

def get_album_service(db=Depends(get_db)):
    repo = AlbumRepository(db)
    return AlbumService(repo)

@router.get("/")
async def get_albums(
    era: str = Query("all"), 
    service: AlbumService = Depends(get_album_service)
):
    return await service.list_albums(era)

@router.get("/{album_id}")
async def get_album(
    album_id: int, 
    service: AlbumService = Depends(get_album_service)
):
    return await service.get_album_details(album_id)

@router.get("/{album_id}/tracks")
async def get_tracks(
    album_id: int, 
    service: AlbumService = Depends(get_album_service)
):
    return await service.get_formatted_tracks(album_id)

@router.post("/", status_code=201)
async def create_album(
    album: AlbumSchema, 
    service: AlbumService = Depends(get_album_service)
):
    return await service.create_new_album(album)