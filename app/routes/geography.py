from fastapi import APIRouter, Depends, Query
from typing import List
from app.database import get_db
from app.repositories.geography_repository import GeographyRepository
from app.services.geography_service import GeographyService
from app.dtos.location_dto import CountryDto

router = APIRouter()

# Inyección de dependencias
def get_geo_service(db=Depends(get_db)):
    repo = GeographyRepository(db)
    return GeographyService(repo)

@router.get(
    "/countries/", 
    response_model=List[CountryDto],
    response_model_by_alias=True  # <--- Esto fuerza el uso de camelCase en el JSON de salida
)
async def get_countries(
    continent_id: int = Query(None), 
    service: GeographyService = Depends(get_geo_service)
):
    # El service ya devuelve objetos CountryDto, FastAPI se encarga del resto
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