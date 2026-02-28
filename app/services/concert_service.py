from typing import Optional
from datetime import datetime
from app.repositories.concert_repository import ConcertRepository
from app.dtos.concert_dto import ConcertDto
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
