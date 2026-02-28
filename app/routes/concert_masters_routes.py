from fastapi import APIRouter, Depends
from typing import List
from app.services.concert_masters_service import ConcertMastersService
from app.dtos.concert_masters_dto import ConcertTypeDTO, ShowTypeDTO, VenueTypeDTO, TourDTO
from app.core.dependencies import get_concert_masters_service

router = APIRouter(prefix="/concert-masters", tags=["ConcertMasters"])

@router.get("/concert-types", response_model=List[ConcertTypeDTO])
async def get_concert_types(service: ConcertMastersService = Depends(get_concert_masters_service)):
    return await service.get_concert_types()

@router.get("/show-types", response_model=List[ShowTypeDTO])
async def get_show_types(service: ConcertMastersService = Depends(get_concert_masters_service)):
    return await service.get_show_types()

@router.get("/venue-types", response_model=List[VenueTypeDTO])
async def get_venue_types(service: ConcertMastersService = Depends(get_concert_masters_service)):
    return await service.get_venue_types()

@router.get("/tours", response_model=List[TourDTO])
async def get_tours(service: ConcertMastersService = Depends(get_concert_masters_service)):
    return await service.get_tours()