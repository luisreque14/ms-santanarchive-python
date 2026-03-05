from fastapi import HTTPException
from typing import List
from app.repositories.album_repository import AlbumRepository
from app.dtos.album_dto import AlbumDto, AlbumWithDetailsDto

class AlbumService:
    def __init__(self, repository: AlbumRepository):
        self.repo = repository

    async def list_albums(self, era: str) -> List[AlbumDto]:
        albums_db = await self.repo.get_albums(era)
        
        return [AlbumDto.model_validate(album) for album in albums_db]

    async def get_album_details(self, album_id: int) -> AlbumDto:
        album_db = await self.repo.get_album_by_id(album_id)
        if not album_db:
            raise HTTPException(status_code=404, detail="Album not found")
        
        return AlbumDto.model_validate(album_db)

    async def get_albums_by_studio_instrumental(self) -> AlbumWithDetailsDto:
        albums_db = await self.repo.get_albums_by_studio_instrumental()
        
        return [AlbumWithDetailsDto.model_validate(t) for t in albums_db]