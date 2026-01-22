from fastapi import HTTPException
from typing import List, Optional
from app.repositories.track_repository import TrackRepository
from app.dtos.track_dto import TrackDto, GenreFilterDto, TrackWithAlbumDetailsDto

class TrackService:
    def __init__(self, repository: TrackRepository):
        self.repo = repository

    async def list_tracks(self, album_id: Optional[int] = None) -> List[TrackDto]:
        """
        Lista pistas filtradas opcionalmente por álbum, transformando el resultado a camelCase.
        """
        match_stage = {"album_id": album_id} if album_id else {}
        tracks_db = await self.repo.get_tracks_with_details(match_stage)
        
        # Mapeo masivo de modelos de BD a DTOs de la API
        return [TrackDto.model_validate(t) for t in tracks_db]

    async def list_tracks_by_genre(self, genre_id: int) -> GenreFilterDto:
        """
        Busca información del género y sus pistas asociadas para devolver el GenreFilterDto.
        """
        genre_info = await self.repo.get_genre_by_id(genre_id)
        if not genre_info:
            raise HTTPException(status_code=404, detail="Genre not found")
        
        match_stage = {"genre_ids": genre_id}
        tracks_db = await self.repo.get_tracks_with_details(match_stage)
        
        # Construimos el objeto de respuesta siguiendo el contrato del DTO
        # Pydantic se encarga de mapear genre_name -> genreName y tracks -> tracks (camelCase interno)
        response_data = {
            "genre_name": genre_info["name"],
            "tracks": tracks_db
        }
        
        return GenreFilterDto.model_validate(response_data)

    async def get_by_guest_artists_range(self, start: int, end: int) -> List[TrackWithAlbumDetailsDto]:
        """
        Valida el rango de años y devuelve las pistas con colaboraciones mapeadas a DTO.
        """
        if start > end:
            raise HTTPException(
                status_code=400, 
                detail="Start year cannot be greater than end year"
            )
            
        guest_artists_db = await self.repo.get_by_guest_artists_range(start, end)
        
        return [TrackWithAlbumDetailsDto.model_validate(t) for t in guest_artists_db]

    async def get_tracks_by_top_duration(self, isLive: bool | None, order: str = "desc") -> List[TrackWithAlbumDetailsDto]:
        tracks_db = await self.repo.get_tracks_by_top_duration(order, isLive)
        
        return [TrackWithAlbumDetailsDto.model_validate(t) for t in tracks_db]

    async def get_tracks_by_lead_vocal(self, musicianId: int) -> List[TrackWithAlbumDetailsDto]:
        tracks_db = await self.repo.get_tracks_by_lead_vocal(musicianId)
        
        return [TrackWithAlbumDetailsDto.model_validate(t) for t in tracks_db]