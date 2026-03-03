from fastapi import APIRouter, Depends, Query, status
from typing import Optional, List
from datetime import datetime
from app.services.concert_service import ConcertService
from app.dtos.concert_dto import ConcertDto, ConcertWithSetlistDto
from app.dtos.concert_song_dto import ConcertSongDto
from app.dtos.paginated_response import PaginatedResponse
from app.core.dependencies import get_concert_service

router = APIRouter(prefix="/concerts", tags=["Concerts"])

@router.get(
    "/", 
    response_model=PaginatedResponse[ConcertDto],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK
)
async def get_concerts(
    start_date: datetime = Query(..., description="Start date (YYYY-MM-DD)", alias="startDate"),
    end_date: datetime = Query(..., description="End date (YYYY-MM-DD)", alias="endDate"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    concert_type_id: Optional[int] = Query(None, alias="concertTypeId"),
    venue_type_id: Optional[int] = Query(None, alias="venueTypeId"),
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
        start_date,
        end_date,
        page,
        page_size,
        concert_type_id,
        venue_type_id,
        tour_id,
        city_id,
        state_id,
        country_id,
        continent_id
    )

@router.get(
    "/get-by-date", 
    response_model=List[ConcertDto],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK
)
async def get_by_date(
    search_date: datetime = Query(..., description="Search date (YYYY-MM-DD)", alias="search_date"),
    service: ConcertService = Depends(get_concert_service)
):
    return await service.get_by_date(
        search_date
    )

@router.get(
    "/get-setlist", 
    response_model=List[ConcertSongDto],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK
)
async def get_concert_setlist(
    concert_id: int = Query(1, ge=1),
    service: ConcertService = Depends(get_concert_service)
):
    return await service.get_concert_setlist(concert_id)

@router.get(
    "/get-concert-details-by-date", 
    response_model=List[ConcertWithSetlistDto],
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK
)
async def get_concert_details_by_date(
    date: datetime = Query(..., description="Search date (YYYY-MM-DD)", alias="date"),
    service: ConcertService = Depends(get_concert_service)
):
    return await service.get_concert_details_by_date(date)