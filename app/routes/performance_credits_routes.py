from fastapi import APIRouter, Depends
from app.services.performance_service import PerformanceService
from app.dtos.performance_credit_dto import PerformanceCreditDto # Ajustado al nombre del archivo anterior
from typing import List
from app.core.dependencies import get_performance_service

router = APIRouter(prefix="/performance-credits", tags=["Performance Credits"])

@router.get(
    "/concert/{concert_id}", 
    response_model=List[PerformanceCreditDto],
    # Esto fuerza el uso de serialization_alias (camelCase)
    response_model_by_alias=True 
)
async def get_credits(
    concert_id: int, 
    service: PerformanceService = Depends(get_performance_service)
):
    """
    Obtiene todos los créditos de músicos (instrumentos y notas) para un concierto específico.
    """
    credits = await service.list_credits_by_concert(concert_id)
    return credits

@router.post(
    "/", 
    status_code=201,
    response_model=PerformanceCreditDto,
    response_model_by_alias=True
)
async def add_performance_credit(
    credit: PerformanceCreditDto, 
    service: PerformanceService = Depends(get_performance_service)
):
    """
    Registra la participación de un músico en un concierto. 
    Permite enviar datos en camelCase desde el frontend.
    """
    return await service.add_performance_credit(credit)