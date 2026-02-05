from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from datetime import datetime
from app.services.concert_service import ConcertService
from app.dtos.concert_dto import ConcertDto
from app.core.dependencies import get_concert_service

router = APIRouter(prefix="/concerts", tags=["Concerts"])

@router.get(
    "/", 
    response_model=List[ConcertDto],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK
)
async def get_concerts(
    start_date: datetime = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="End date (YYYY-MM-DD)"),
    concert_type_id: Optional[int] = Query(None, alias="concertTypeId"),
    tour_id: Optional[int] = Query(None, alias="tourId"),
    city_id: Optional[int] = Query(None, alias="cityId"),
    state_id: Optional[int] = Query(None, alias="stateId"),
    country_id: Optional[int] = Query(None, alias="countryId"),
    continent_id: Optional[int] = Query(None, alias="continentId"),
    service: ConcertService = Depends(get_concert_service)
):
    """
    Get a list of concerts filtered by a date range (max 1 year) 
    and optional geographical or tour parameters.
    """
    return await service.get_by_filter(
        start_date=start_date,
        end_date=end_date,
        concert_type_id=concert_type_id,
        tour_id=tour_id,
        city_id=city_id,
        state_id=state_id,
        country_id=country_id,
        continent_id=continent_id
    )