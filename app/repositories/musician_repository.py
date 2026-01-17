from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

class MusicianRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # --- ROLES ---
    async def get_role_by_id(self, role_id: int):
        return await self.db.roles.find_one({"id": role_id})

    async def get_all_roles(self):
        return await self.db.roles.find({}, {"_id": 0}).to_list(length=100)

    async def create_role(self, role_data: dict):
        await self.db.roles.insert_one(role_data)
        return role_data["id"]

    # --- MUSICIANS ---
    async def get_all_musicians(self):
        return await self.db.musicians.find({}, {"_id": 0}).to_list(length=100)

    async def create_musician(self, musician_data: dict):
        await self.db.musicians.insert_one(musician_data)
        return True

    # --- VALIDATIONS ---
    async def check_roles_exist(self, role_ids: List[int]) -> bool:
        # Optimizamos: una sola consulta para verificar todos los roles
        count = await self.db.roles.count_documents({"id": {"$in": role_ids}})
        return count == len(role_ids)

    async def country_exists(self, country_id: int) -> bool:
        return await self.db.countries.find_one({"id": country_id}) is not None