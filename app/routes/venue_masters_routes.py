from fastapi import APIRouter, Depends
from typing import List
from app.services.venue_masters_service import VenueMastersService
from app.dtos.venue_masters_dto import ConcertTypeDTO, ShowTypeDTO, VenueTypeDTO, TourDTO
from app.core.dependencies import get_venue_masters_service

router = APIRouter(prefix="/api/venue-masters", tags=["VenueMasters"])

@router.get("/concert-types", response_model=List[ConcertTypeDTO])
async def get_concert_types(service: VenueMastersService = Depends(get_venue_masters_service)):
    return await service.get_concert_types()

@router.get("/show-types", response_model=List[ShowTypeDTO])
async def get_show_types(service: VenueMastersService = Depends(get_venue_masters_service)):
    return await service.get_show_types()

@router.get("/venue-types", response_model=List[VenueTypeDTO])
async def get_venue_types(service: VenueMastersService = Depends(get_venue_masters_service)):
    return await service.get_venue_types()

@router.get("/tours", response_model=List[TourDTO])
async def get_tours(service: VenueMastersService = Depends(get_venue_masters_service)):
    return await service.get_tours()