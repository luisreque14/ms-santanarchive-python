from fastapi import HTTPException
from app.repositories.album_repository import AlbumRepository

class AlbumService:
    def __init__(self, repository: AlbumRepository):
        self.repo = repository

    async def list_albums(self, era: str):
        query = {}
        if era != "all" and era.isdigit():
            start_year = int(era)
            query["release_year"] = {"$gte": start_year, "$lte": start_year + 9}

        albums = await self.repo.get_albums(query)
        
        # Lógica de negocio: enriquecer datos para el frontend
        for album in albums:
            album["cover"] = album.get("cover", "/images/default-album.jpg")
        return albums

    async def get_album_details(self, album_id: int):
        album = await self.repo.get_album_by_id(album_id)
        if not album:
            raise HTTPException(status_code=404, detail="Album not found")
        return album

    async def create_new_album(self, album_schema):
        if await self.repo.get_album_by_id(album_schema.id):
            raise HTTPException(status_code=400, detail="Album ID already exists")
        return await self.repo.create_album(album_schema.model_dump())

    async def get_formatted_tracks(self, album_id: int):
        # Primero verificamos si el álbum existe
        if not await self.repo.get_album_by_id(album_id):
            raise HTTPException(status_code=404, detail="Album not found")
        return await self.repo.get_tracks_by_album(album_id)