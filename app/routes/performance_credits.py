from fastapi import APIRouter, Depends
from app.database import get_db
from app.repositories.performance_repository import PerformanceRepository
from app.services.performance_service import PerformanceService
from app.models.performance_credits import PerformanceCreditSchema
from typing import List

router = APIRouter()

def get_performance_service(db=Depends(get_db)):
    return PerformanceService(PerformanceRepository(db))

@router.post("/", status_code=201)
async def add_credit(
    credit: PerformanceCreditSchema, 
    service: PerformanceService = Depends(get_performance_service)
):
    return await service.add_performance_credit(credit)

@router.get("/concert/{concert_id}")
async def get_credits(
    concert_id: int, 
    service: PerformanceService = Depends(get_performance_service)
):
    return await service.list_credits_by_concert(concert_id)