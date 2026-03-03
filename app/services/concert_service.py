from typing import Optional, List
from datetime import datetime
from app.repositories.concert_repository import ConcertRepository
from app.dtos.concert_dto import ConcertDto, ConcertWithSetlistDto
from app.dtos.concert_song_dto import ConcertSongDto
from app.dtos.paginated_response import PaginatedResponse

class ConcertService:
    def __init__(self, repository: ConcertRepository):
        self.repo = repository

    async def get_by_filter(
        self, 
        start_date: datetime, 
        end_date: datetime,
        page: int = 1,
        page_size: int = 50,
        concert_type_id: Optional[int] = None,
        venue_type_id: Optional[int] = None,
        tour_id: Optional[int] = None,
        city_id: Optional[int] = None,
        state_id: Optional[int] = None,
        country_id: Optional[int] = None,
        continent_id: Optional[int] = None
    ) -> PaginatedResponse[ConcertDto]:
        # La validación del rango de 1 año ya está en el repositorio, 
        # pero la capturamos aquí para lanzar la excepción HTTP correcta.
        repo_response = await self.repo.get_by_filter(
            start_date,
            end_date,
            page,
            page_size,
            concert_type_id,
            venue_type_id,
            tour_id,
            city_id,
            state_id,
            country_id,
            continent_id
        )
        
        concerts_dtos = [
            ConcertDto.model_validate(v) 
            for v in repo_response.get("results", [])
        ]
        
        return PaginatedResponse(
            total=repo_response.get("total", 0),
            page=repo_response.get("page", page),
            pageSize=repo_response.get("pageSize", page_size),
            results=concerts_dtos
        )
    
    async def get_by_date(self, search_date: datetime) -> List[ConcertDto]:
        data = await self.repo.get_by_date(search_date)
        
        return [ConcertDto(**item) for item in data]
    
    async def get_concert_setlist(self, concert_id: int) -> List[ConcertSongDto]:
        data = await self.repo.get_concert_setlist(concert_id)
        
        return [ConcertSongDto(**item) for item in data]
    
    async def get_concert_details_by_date(self, search_date: datetime) -> List[ConcertWithSetlistDto]:
        # 1. Obtener los conciertos de la fecha
        concerts_data = await self.repo.get_by_date(search_date)
        
        if not concerts_data:
            return []

        results = []
        
        # 2. Iterar por cada concierto encontrado para traer sus canciones
        for concert_dict in concerts_data:
            # Convertimos el diccionario base a DTO
            concert_dto = ConcertWithSetlistDto(**concert_dict)
            
            # 3. Llamamos al método del repo para obtener las canciones
            songs_data = await self.repo.get_concert_setlist(concert_dto.id)
            
            # 4. Mapeamos las canciones a su DTO y las asignamos al concierto
            concert_dto.setlist = [ConcertSongDto(**song) for song in songs_data]
            
            results.append(concert_dto)
            
        return results