from fastapi import APIRouter, Depends, Query, HTTPException
from app.services.album_service import AlbumService
from app.dtos.album_dto import AlbumDto
from typing import List
from app.core.dependencies import get_album_service

router = APIRouter(prefix="/albums", tags=["Albums"])

@router.get(
    "/", 
    response_model=List[AlbumDto], 
    response_model_by_alias=True
)
async def get_albums(
    era: str = Query("all"), 
    service: AlbumService = Depends(get_album_service)
):
    return await service.list_albums(era)

@router.get(
    "/{album_id}", 
    response_model=AlbumDto, 
    response_model_by_alias=True
)
async def get_album(
    album_id: int, 
    service: AlbumService = Depends(get_album_service)
):
    album = await service.get_album_details(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return album

@router.post(
    "/", 
    status_code=201, 
    response_model=AlbumDto, 
    response_model_by_alias=True
)
async def create_album(
    album: AlbumDto, 
    service: AlbumService = Depends(get_album_service)
):
    return await service.create_new_album(album)