from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.repositories.geography_repository import GeographyRepository
from app.services.geography_service import GeographyService
from app.models.geography import CountrySchema

router = APIRouter()

# Inyección de dependencias manual para el ejemplo
def get_geo_service(db=Depends(get_db)):
    repo = GeographyRepository(db)
    return GeographyService(repo)

@router.get("/countries/")
async def get_countries(
    continent_id: int = Query(None), 
    service: GeographyService = Depends(get_geo_service)
):
    return await service.list_countries(continent_id)

@router.post("/countries/", status_code=201)
async def create_country(
    country: CountrySchema, 
    service: GeographyService = Depends(get_geo_service)
):
    return await service.create_country(country)