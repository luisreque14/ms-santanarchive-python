from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio

class ConcertsExecutiveSummaryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_executive_summary(self) -> dict:
        _CARLOS_MUSICIAN_ID = 1
        _CARLOS_COMPOSER_ID = 11
        
        tasks = [
            self.get_total_concerts_count()
        ]
        
        # gather espera a que todas terminen y devuelve los resultados en orden
        (
            total_concerts,
        ) = await asyncio.gather(*tasks)

        # Unimos todas las piezas en el resumen final
        return {
            "total_concerts": total_concerts
        }

    async def get_total_concerts_count(self) -> int:
        """
        Devuelve el conteo total de todos los documentos en la colección concerts.
        Ideal para estadísticas generales y storytelling.
        """
        # count_documents es más eficiente que un aggregate completo para este propósito
        total = await self.db.concerts.count_documents({})
        return total