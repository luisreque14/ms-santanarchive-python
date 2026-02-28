from fastapi import HTTPException
from typing import List, Optional
from app.repositories.geography_repository import GeographyRepository
from app.dtos.geography_dto import ContinentDto, CountryDto, CityDto, StateDto

class GeographyService:
    def __init__(self, repository: GeographyRepository):
        self.repo = repository

    async def create_country(self, country_data) -> CountryDto:
        """
        Creates a new country after validating continent existence and ID uniqueness.
        Returns the created country as a DTO in camelCase.
        """
        # Business Validation: Continent must exist
        if not await self.repo.get_continent_by_id(country_data.continent_id):
            raise HTTPException(status_code=400, detail="Continent does not exist")
        
        # Validation: No duplicates
        if await self.repo.get_country_by_id(country_data.id):
            raise HTTPException(status_code=400, detail="Country ID already exists")
            
        # Persistence: Save to DB (returns snake_case dict/model)
        new_country_db = await self.repo.create_country(country_data.model_dump())
        
        # Mapping: Convert to DTO (camelCase)
        return CountryDto.model_validate(new_country_db)

    async def list_countries(self, continentId: Optional[int] = None) -> List[CountryDto]:
        """
        Retrieves a list of countries, optionally filtered by continent.
        Automatically maps the database results to the CountryDto format.
        """
        countries_db = await self.repo.get_countries(continentId)
        
        # Mapping: Transform the entire list from snake_case to camelCase DTOs
        return [CountryDto.model_validate(country) for country in countries_db]

    async def get_country_details(self, country_id: int) -> CountryDto:
        """
        Fetches a single country by ID and returns it as a DTO.
        """
        country_db = await self.repo.get_country_by_id(country_id)
        if not country_db:
            raise HTTPException(status_code=404, detail="Country not found")
            
        return CountryDto.model_validate(country_db)
    
    async def list_cities(self, country_id: int, state_id: Optional[int] = None) -> List[CityDto]:
        cities_db = await self.repo.get_cities(state_id, country_id)
        
        return [CityDto(**city) for city in cities_db]
    
    async def list_states(self, country_id: int) -> List[StateDto]:
        states_db = await self.repo.get_states(country_id)
        
        return [StateDto(**state) for state in states_db]
    
    async def list_continents(self) -> List[ContinentDto]:
        continents_db = await self.repo.get_all_continents()
        
        return [ContinentDto(**continent) for continent in continents_db]