from fastapi import HTTPException
from app.repositories.musician_repository import MusicianRepository

class MusicianService:
    def __init__(self, repository: MusicianRepository):
        self.repo = repository

    async def add_role(self, role_schema):
        if await self.repo.get_role_by_id(role_schema.id):
            raise HTTPException(status_code=400, detail="Role ID already exists")
        return await self.repo.create_role(role_schema.model_dump())

    async def list_roles(self):
        return await self.repo.get_all_roles()

    async def register_musician(self, musician_schema):
        # 1. Validar País
        if not await self.repo.country_exists(musician_schema.country_id):
            raise HTTPException(status_code=400, detail="Country not found")

        # 2. Validar Roles (Optimizado: una sola llamada a DB)
        if not await self.repo.check_roles_exist(musician_schema.roles):
            raise HTTPException(status_code=400, detail="One or more Role IDs are invalid")

        return await self.repo.create_musician(musician_schema.model_dump())

    async def list_musicians(self):
        return await self.repo.get_all_musicians()