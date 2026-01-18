from fastapi import APIRouter, Depends, Query, HTTPException
from app.services.concert_service import ConcertService
from app.dtos.concert_dto import ConcertDto
from app.dtos.performance_credit_dto import PerformanceCreditDto
from typing import List, Optional
from app.core.dependencies import get_concert_service

router = APIRouter(prefix="/concerts", tags=["Concerts"])

@router.get(
    "/", 
    response_model=List[ConcertDto], 
    response_model_by_alias=True
)
async def get_concerts(
    year: Optional[str] = Query(None), 
    service: ConcertService = Depends(get_concert_service)
):
    """
    Obtiene la lista de conciertos filtrados por año. 
    Devuelve los datos en camelCase.
    """
    return await service.list_concerts(year)

@router.post(
    "/", 
    status_code=201, 
    response_model=ConcertDto, 
    response_model_by_alias=True
)
async def create_concert(
    concert: ConcertDto, # Usamos el DTO para la entrada también por consistencia
    service: ConcertService = Depends(get_concert_service)
):
    """
    Registra un nuevo concierto. 
    Acepta tanto snake_case como camelCase en la entrada.
    """
    return await service.register_concert(concert)

@router.post(
    "/performance-credits/", 
    status_code=201, 
    response_model=PerformanceCreditDto, 
    response_model_by_alias=True
)
async def add_credit(
    credit: PerformanceCreditDto, 
    service: ConcertService = Depends(get_concert_service)
):
    """
    Añade un crédito de actuación a un concierto (músicos en vivo).
    """
    return await service.add_credit(credit)