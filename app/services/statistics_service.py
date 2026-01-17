from app.repositories.statistics_repository import StatisticsRepository
from typing import Optional

class StatisticsService:
    def __init__(self, repository: StatisticsRepository):
        self.repo = repository

    async def get_instrumental_stats(self, album_id: Optional[int] = None):
        match_query = {"album_id": album_id} if album_id else {}
        result = await self.repo.run_instrumental_aggregation(match_query, album_id is not None)
        
        if not result: return None
        
        data = result[0]
        # Lógica de negocio: Formatear el nombre si es global
        if album_id is None:
            data["album_name"] = "Discografía Completa"
        return data

    async def get_executive_summary(self):
        result = await self.repo.run_executive_summary_pipeline()
        if not result or result[0].get("total_tracks") is None:
            return None
        return result[0]

    async def get_collaboration_report(self):
        # Aquí llamarías al repositorio y podrías añadir lógica extra
        # como redondear porcentajes o filtrar colaboradores nulos
        return await self.repo.run_collab_report_pipeline()