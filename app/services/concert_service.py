from fastapi import HTTPException
from datetime import datetime
from typing import List, Optional
from app.repositories.concert_repository import ConcertRepository
from app.dtos.concert_dto import ConcertDto
from app.dtos.performance_credit_dto import PerformanceCreditDto

class ConcertService:
    def __init__(self, repository: ConcertRepository):
        self.repo = repository

    async def register_concert(self, concert_schema) -> ConcertDto:
        # Validación de integridad referencial
        if not await self.repo.find_city_by_id(concert_schema.city_id):
            raise HTTPException(status_code=400, detail="City not found")
        
        # Persistencia (BD usa snake_case)
        new_concert = await self.repo.create_concert(concert_schema.model_dump())
        
        # Respuesta mapeada a camelCase
        return ConcertDto.model_validate(new_concert)

    async def add_credit(self, credit_schema) -> PerformanceCreditDto:
        # Validaciones de existencia
        if not await self.repo.find_concert_by_id(credit_schema.concert_id):
            raise HTTPException(status_code=404, detail="Concert not found")
        if not await self.repo.find_musician_by_id(credit_schema.musician_id):
            raise HTTPException(status_code=404, detail="Musician not found")
        
        # Guardar en BD
        new_credit = await self.repo.create_performance_credit(credit_schema.model_dump())
        
        # Retornar DTO con camelCase
        return PerformanceCreditDto.model_validate(new_credit)

    async def list_concerts(self, year: Optional[str] = None) -> List[ConcertDto]:
        # Lógica de negocio: determinar el año de búsqueda
        search_year = year if year and year != "all" else str(datetime.now().year)
        
        concerts_db = await self.repo.get_concerts_by_year(search_year)
        
        # Transformación masiva de la lista a DTOs
        return [ConcertDto.model_validate(c) for c in concerts_db]