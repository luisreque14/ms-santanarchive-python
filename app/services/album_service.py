from fastapi import HTTPException
from typing import List
from app.repositories.album_repository import AlbumRepository
from app.dtos.album_dto import AlbumDto

class AlbumService:
    def __init__(self, repository: AlbumRepository):
        self.repo = repository

    async def list_albums(self, era: str) -> List[AlbumDto]:
        # Obtenemos los modelos de la base de datos (snake_case)
        albums_db = await self.repo.get_albums(era)
        
        # Mapeamos la lista de resultados al DTO con camelCase
        # model_validate se encarga de convertir release_year -> releaseYear, etc.
        return [AlbumDto.model_validate(album) for album in albums_db]

    async def get_album_details(self, album_id: int) -> AlbumDto:
        album_db = await self.repo.get_album_by_id(album_id)
        if not album_db:
            raise HTTPException(status_code=404, detail="Album not found")
        
        return AlbumDto.model_validate(album_db)

    async def create_new_album(self, album_schema) -> AlbumDto:
        # Verificamos existencia usando el repo
        if await self.repo.get_album_by_id(album_schema.id):
            raise HTTPException(status_code=400, detail="Album ID already exists")
        
        # Guardamos en la BD usando el dump del schema (snake_case)
        created_album = await self.repo.create_album(album_schema.model_dump())
        
        # Retornamos el DTO (camelCase)
        return AlbumDto.model_validate(created_album)
