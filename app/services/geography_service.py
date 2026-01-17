from fastapi import HTTPException
from app.repositories.geography_repository import GeographyRepository

class GeographyService:
    def __init__(self, repository: GeographyRepository):
        self.repo = repository

    async def create_country(self, country_data):
        # Validación de negocio: El continente debe existir
        if not await self.repo.get_continent_by_id(country_data.continent_id):
            raise HTTPException(status_code=400, detail="Continent does not exist")
        
        # Validación: No duplicados
        if await self.repo.get_country_by_id(country_data.id):
            raise HTTPException(status_code=400, detail="Country ID already exists")
            
        return await self.repo.create_country(country_data.model_dump())

    async def list_countries(self, continent_id=None):
        query = {"continent_id": continent_id} if continent_id else {}
        return await self.repo.get_countries(query)