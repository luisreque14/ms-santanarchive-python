from fastapi import HTTPException
from app.repositories.performance_repository import PerformanceRepository

class PerformanceService:
    def __init__(self, repository: PerformanceRepository):
        self.repo = repository

    async def add_performance_credit(self, credit_schema):
        # 1. Validar Concierto
        if not await self.repo.concert_exists(credit_schema.concert_id):
            raise HTTPException(status_code=404, detail="Concert not found")

        # 2. Validar Músico
        if not await self.repo.musician_exists(credit_schema.musician_id):
            raise HTTPException(status_code=404, detail="Musician not found")

        return await self.repo.create_credit(credit_schema.model_dump())

    async def list_credits_by_concert(self, concert_id: int):
        # Podríamos validar si el concierto existe aquí también si quisiéramos ser estrictos
        return await self.repo.get_credits_by_concert(concert_id)