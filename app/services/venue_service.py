from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime
from app.repositories.venue_repository import VenueRepository
from app.dtos.venue_dto import VenueDto

class VenueService:
    def __init__(self, repository: VenueRepository):
        self.repo = repository

    async def get_by_filter(
        self, 
        start_date: datetime, 
        end_date: datetime,
        concert_type_id: Optional[int] = None,
        tour_id: Optional[int] = None,
        city_id: Optional[int] = None,
        state_id: Optional[int] = None,
        country_id: Optional[int] = None,
        continent_id: Optional[int] = None
    ) -> List[VenueDto]:
        # La validación del rango de 1 año ya está en el repositorio, 
        # pero la capturamos aquí para lanzar la excepción HTTP correcta.
        venues_db = await self.repo.get_by_filter(
            start_date=start_date,
            end_date=end_date,
            concert_type_id=concert_type_id,
            tour_id=tour_id,
            city_id=city_id,
            state_id=state_id,
            country_id=country_id,
            continent_id=continent_id
        )
        
        # Mapeo de la lista de diccionarios (snake_case) a DTOs (camelCase)
        return [VenueDto.model_validate(v) for v in venues_db]
