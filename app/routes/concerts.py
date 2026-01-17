from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.repositories.concert_repository import ConcertRepository
from app.services.concert_service import ConcertService
from app.models.concert import ConcertSchema
from app.models.performance_credits import PerformanceCreditSchema
from typing import List, Optional

router = APIRouter()

def get_concert_service(db=Depends(get_db)):
    return ConcertService(ConcertRepository(db))

@router.post("/", status_code=201)
async def create_concert(
    concert: ConcertSchema, 
    service: ConcertService = Depends(get_concert_service)
):
    return await service.register_concert(concert)

@router.post("/performance-credits/", status_code=201)
async def add_credit(
    credit: PerformanceCreditSchema, 
    service: ConcertService = Depends(get_concert_service)
):
    return await service.add_credit(credit)

@router.get("/")
async def get_concerts(
    year: Optional[str] = Query(None), 
    service: ConcertService = Depends(get_concert_service)
):
    return await service.list_concerts(year)