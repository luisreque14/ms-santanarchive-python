from fastapi import HTTPException
from datetime import datetime
from app.repositories.concert_repository import ConcertRepository

class ConcertService:
    def __init__(self, repository: ConcertRepository):
        self.repo = repository

    async def register_concert(self, concert_schema):
        if not await self.repo.find_city_by_id(concert_schema.city_id):
            raise HTTPException(status_code=400, detail="City not found")
        return await self.repo.create_concert(concert_schema.model_dump())

    async def add_credit(self, credit_schema):
        if not await self.repo.find_concert_by_id(credit_schema.concert_id):
            raise HTTPException(status_code=404, detail="Concert not found")
        if not await self.repo.find_musician_by_id(credit_schema.musician_id):
            raise HTTPException(status_code=404, detail="Musician not found")
        return await self.repo.create_performance_credit(credit_schema.model_dump())

    async def list_concerts(self, year: str = None):
        # Lógica de negocio para el año por defecto
        search_year = year if year and year != "all" else str(datetime.now().year)
        return await self.repo.get_concerts_by_year(search_year)