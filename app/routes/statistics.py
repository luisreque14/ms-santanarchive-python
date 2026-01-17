from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.repositories.statistics_repository import StatisticsRepository
from app.services.statistics_service import StatisticsService


router = APIRouter()

def get_stats_service(db=Depends(get_db)):
    return StatisticsService(StatisticsRepository(db))

@router.get("/executive-summary")
async def get_summary(service: StatisticsService = Depends(get_stats_service)):
    return await service.get_executive_summary()

@router.get("/instrumental")
async def get_instrumental(
    album_id: int = Query(None), 
    service: StatisticsService = Depends(get_stats_service)
):
    return await service.get_instrumental_stats(album_id)