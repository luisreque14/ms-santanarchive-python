from pydantic import BaseModel

class ConcertTypeDTO(BaseModel):
    id: int
    name: str

class ShowTypeDTO(BaseModel):
    id: int
    name: str

class VenueTypeDTO(BaseModel):
    id: int
    name: str

class TourDTO(BaseModel):
    id: int
    name: str