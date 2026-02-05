from fastapi import APIRouter, Depends, Query
from typing import List
from app.services.geography_service import GeographyService
from app.dtos.geography_dto import ContinentDto, CountryDto, CityDto, StateDto
from app.core.dependencies import get_geo_service

router = APIRouter(prefix="/geography", tags=["Geography"])

@router.get(
    "/continents/", 
    response_model=List[ContinentDto],
    response_model_by_alias=True
)
async def get_continents(
    service: GeographyService = Depends(get_geo_service)
):
    return await service.list_continents()

@router.get(
    "/countries/", 
    response_model=List[CountryDto],
    response_model_by_alias=True
)
async def get_countries(
    continent_id: int = Query(None), 
    service: GeographyService = Depends(get_geo_service)
):
    return await service.list_countries(continent_id)

@router.post(
    "/countries/", 
    status_code=201, 
    response_model=CountryDto,
    response_model_by_alias=True  # <--- Esto asegura que la respuesta del POST sea camelCase
)
async def create_country(
    country: CountryDto, 
    service: GeographyService = Depends(get_geo_service)
):
    return await service.create_country(country)

@router.get(
    "/states/", 
    response_model=List[StateDto],
    response_model_by_alias=True
)
async def get_states(
    country_id: int = Query(None), 
    service: GeographyService = Depends(get_geo_service)
):
    return await service.list_states(country_id)

@router.get(
    "/cities/", 
    response_model=List[CityDto],
    response_model_by_alias=True
)
async def get_cities(
    country_id: int = Query(None), 
    state_id: int = Query(None), 
    service: GeographyService = Depends(get_geo_service)
):
    return await service.list_cities(country_id,state_id)
