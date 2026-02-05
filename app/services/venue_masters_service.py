from typing import List
from app.repositories.venue_masters_repository import VenueMastersRepository
from app.dtos.venue_masters_dto import ConcertTypeDTO, ShowTypeDTO, VenueTypeDTO, TourDTO

class VenueMastersService:
    def __init__(self, repository: VenueMastersRepository):
        self.repository = repository

    async def get_concert_types(self) -> List[ConcertTypeDTO]:
        data = await self.repository.get_concert_types()
        return [ConcertTypeDTO(**item) for item in data]

    async def get_show_types(self) -> List[ShowTypeDTO]:
        data = await self.repository.get_show_types()
        return [ShowTypeDTO(**item) for item in data]

    async def get_venue_types(self) -> List[VenueTypeDTO]:
        data = await self.repository.get_venue_types()
        return [VenueTypeDTO(**item) for item in data]

    async def get_tours(self) -> List[TourDTO]:
        data = await self.repository.get_tours()
        return [TourDTO(**item) for item in data]