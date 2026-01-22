from fastapi import HTTPException
from typing import List
from app.repositories.musician_repository import MusicianRepository
from app.dtos.musician_dto import MusicianDto, RoleDto, MusicianDetailsDto

class MusicianService:
    def __init__(self, repository: MusicianRepository):
        self.repo = repository

    async def add_role(self, role_schema) -> RoleDto:
        """
        Crea un nuevo rol y lo devuelve como DTO en camelCase.
        """
        if await self.repo.get_role_by_id(role_schema.id):
            raise HTTPException(status_code=400, detail="Role ID already exists")
        
        new_role = await self.repo.create_role(role_schema.model_dump())
        return RoleDto.model_validate(new_role)

    async def list_roles(self) -> List[RoleDto]:
        """
        Lista todos los roles mapeados al contrato de la API.
        """
        roles_db = await self.repo.get_all_roles()
        return [RoleDto.model_validate(r) for r in roles_db]

    async def register_musician(self, musician_schema) -> MusicianDto:
        """
        Valida país y roles, persiste el músico y devuelve el DTO (camelCase).
        """
        # 1. Validar País
        if not await self.repo.country_exists(musician_schema.country_id):
            raise HTTPException(status_code=400, detail="Country not found")

        # 2. Validar Roles (Optimizado)
        if not await self.repo.check_roles_exist(musician_schema.roles):
            raise HTTPException(status_code=400, detail="One or more Role IDs are invalid")

        # Guardar en BD (usa snake_case internamente)
        new_musician = await self.repo.create_musician(musician_schema.model_dump())
        
        # Mapeo a DTO: nickname (de apelativo), activeFrom (de start_date), etc.
        return MusicianDto.model_validate(new_musician)

    async def list_musicians(self) -> List[MusicianDto]:
        """
        Lista todos los músicos transformados al estándar camelCase.
        """
        musicians_db = await self.repo.get_all_musicians()
        return [MusicianDto.model_validate(m) for m in musicians_db]

    async def get_studio_lead_vocals(self) -> List[MusicianDetailsDto]:
        musicians_db = await self.repo.get_studio_lead_vocals()
        return [MusicianDetailsDto.model_validate(m) for m in musicians_db]