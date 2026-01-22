from fastapi import APIRouter, Depends
from app.services.musician_service import MusicianService
from app.dtos.musician_dto import RoleDto, MusicianDto, MusicianDetailsDto
from typing import List
from app.core.dependencies import get_musician_service

router = APIRouter(prefix="/musicians", tags=["Musicians"])

@router.get(
    "/roles/", 
    response_model=List[RoleDto],
    response_model_by_alias=True
)
async def get_roles(service: MusicianService = Depends(get_musician_service)):
    """
    Lista todos los roles musicales (instrumentos, producción, etc.) en camelCase.
    """
    return await service.list_roles()

@router.post(
    "/roles/", 
    status_code=201,
    response_model=RoleDto,
    response_model_by_alias=True
)
async def create_role(
    role: RoleDto, 
    service: MusicianService = Depends(get_musician_service)
):
    return await service.add_role(role)

@router.get(
    "/", 
    response_model=List[MusicianDto],
    response_model_by_alias=True
)
async def get_musicians(service: MusicianService = Depends(get_musician_service)):
    """
    Obtiene la lista de músicos con sus fechas de actividad y biografías mapeadas.
    """
    return await service.list_musicians()

@router.post(
    "/", 
    status_code=201,
    response_model=MusicianDto,
    response_model_by_alias=True
)
async def create_musician(
    musician: MusicianDto, 
    service: MusicianService = Depends(get_musician_service)
):
    return await service.register_musician(musician)

@router.get(
    "/by-studio-lead-vocals", 
    response_model=List[MusicianDetailsDto],
    response_model_by_alias=True
)
async def get_studio_lead_vocals(service: MusicianService = Depends(get_musician_service)):
    return await service.get_studio_lead_vocals()