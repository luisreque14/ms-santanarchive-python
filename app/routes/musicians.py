from fastapi import APIRouter, Depends
from app.database import get_db
from app.repositories.musician_repository import MusicianRepository
from app.services.musician_service import MusicianService
from app.models.musician import RoleSchema, MusicianSchema
from typing import List

router = APIRouter()

def get_musician_service(db=Depends(get_db)):
    return MusicianService(MusicianRepository(db))

@router.post("/roles/", status_code=201)
async def create_role(role: RoleSchema, service: MusicianService = Depends(get_musician_service)):
    return await service.add_role(role)

@router.get("/roles/")
async def get_roles(service: MusicianService = Depends(get_musician_service)):
    return await service.list_roles()

@router.post("/", status_code=201)
async def create_musician(musician: MusicianSchema, service: MusicianService = Depends(get_musician_service)):
    return await service.register_musician(musician)

@router.get("/")
async def get_musicians(service: MusicianService = Depends(get_musician_service)):
    return await service.list_musicians()