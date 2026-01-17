from motor.motor_asyncio import AsyncIOMotorDatabase

class PerformanceRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # Verificaciones de integridad referencial
    async def concert_exists(self, concert_id: int) -> bool:
        return await self.db.concerts.find_one({"id": concert_id}) is not None

    async def musician_exists(self, musician_id: int) -> bool:
        return await self.db.musicians.find_one({"id": musician_id}) is not None

    # Operaciones CRUD
    async def create_credit(self, credit_data: dict):
        await self.db.performance_credits.insert_one(credit_data)
        return True

    async def get_credits_by_concert(self, concert_id: int):
        return await self.db.performance_credits.find(
            {"concert_id": concert_id}, 
            {"_id": 0}
        ).to_list(length=100)