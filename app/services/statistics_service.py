from typing import Optional, List
from app.repositories.statistics_repository import StatisticsRepository
from app.dtos.statistics.executive_summary_dto import ExecutiveSummaryDto
from app.dtos.statistics.discography.track_key_dto import TrackKeyStatsDto
from app.dtos.statistics.discography_dto import (
    InstrumentalStatsDto,
    LoveSongStatsDto,
    MusicalGenreStatsDto,
    CollaboratorReportDto
    )
class StatisticsService:
    def __init__(self, repository: StatisticsRepository):
        self.repo = repository

    async def get_instrumental_logic(self, album_id: Optional[int] = None) -> Optional[InstrumentalStatsDto]:
        # Business Logic: Determine the filter scope
        match_query = {"album_id": album_id} if album_id else {}
        
        results = await self.repo.get_instrumental_stats(match_query, album_id)
        
        if not results:
            return None
            
        # Mapeo de snake_case (total_instrumental) a camelCase (totalInstrumental)
        return InstrumentalStatsDto.model_validate(results[0])

    async def get_key_stats_logic(self, album_id: Optional[int] = None) -> List[TrackKeyStatsDto]:
        match_query = {"album_id": album_id} if album_id else {}
        
        # Obtenemos la lista de la BD
        results_db = await self.repo.get_key_stats(match_query, album_id)
        
        # Transformación masiva a camelCase (count -> totalTracks)
        return [TrackKeyStatsDto.model_validate(stat) for stat in results_db]

    async def get_executive_summary_logic(self) -> Optional[ExecutiveSummaryDto]:
        results = await self.repo.get_executive_summary()
        
        # Validation: Ensure we have data before mapping to DTO
        if not results or results[0].get("total_tracks") is None:
            return None
            
        return ExecutiveSummaryDto.model_validate(results[0])

    async def get_love_song_stats_logic(self) -> Optional[LoveSongStatsDto]:
        results = await self.repo.get_love_song_stats()
        
        if not results:
            return None
            
        return LoveSongStatsDto.model_validate(results[0])

    async def get_musical_genre_stats_logic(self) -> List[MusicalGenreStatsDto]:
        results_db = await self.repo.get_musical_genre_stats()
        
        # Mapeo: genre_name -> genreName, track_count -> trackCount
        return [MusicalGenreStatsDto.model_validate(genre) for genre in results_db]

    async def get_collab_report_logic(self) -> List[CollaboratorReportDto]:
        results_db = await self.repo.get_collab_report()
        
        # Mapeo: collab_percentage -> collabPercentage, etc.
        return [CollaboratorReportDto.model_validate(report) for report in results_db]