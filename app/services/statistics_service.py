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
    """
    Business logic layer for discography statistics.
    Orchestrates repository calls and transforms results into camelCase DTOs.
    """

    @staticmethod
    async def get_instrumental_logic(album_id: Optional[int] = None) -> Optional[InstrumentalStatsDto]:
        # Business Logic: Determine the filter scope
        match_query = {"album_id": album_id} if album_id else {}
        
        results = await StatisticsRepository.get_instrumental_stats(match_query, album_id)
        
        if not results:
            return None
            
        # Mapeo de snake_case (total_instrumental) a camelCase (totalInstrumental)
        return InstrumentalStatsDto.model_validate(results[0])

    @staticmethod
    async def get_key_stats_logic(album_id: Optional[int] = None) -> List[TrackKeyStatsDto]:
        match_query = {"album_id": album_id} if album_id else {}
        
        # Obtenemos la lista de la BD
        results_db = await StatisticsRepository.get_key_stats(match_query, album_id)
        
        # Transformación masiva a camelCase (count -> totalTracks)
        return [TrackKeyStatsDto.model_validate(stat) for stat in results_db]

    @staticmethod
    async def get_executive_summary_logic() -> Optional[ExecutiveSummaryDto]:
        results = await StatisticsRepository.get_executive_summary()
        
        # Validation: Ensure we have data before mapping to DTO
        if not results or results[0].get("total_tracks") is None:
            return None
            
        return ExecutiveSummaryDto.model_validate(results[0])

    @staticmethod
    async def get_love_song_stats_logic() -> Optional[LoveSongStatsDto]:
        results = await StatisticsRepository.get_love_song_stats()
        
        if not results:
            return None
            
        return LoveSongStatsDto.model_validate(results[0])

    @staticmethod
    async def get_genre_stats_logic() -> List[MusicalGenreStatsDto]:
        results_db = await StatisticsRepository.get_genre_stats()
        
        # Mapeo: genre_name -> genreName, track_count -> trackCount
        return [MusicalGenreStatsDto.model_validate(genre) for genre in results_db]

    @staticmethod
    async def get_collab_report_logic() -> List[CollaboratorReportDto]:
        results_db = await StatisticsRepository.get_collab_report()
        
        # Mapeo: collab_percentage -> collabPercentage, etc.
        return [CollaboratorReportDto.model_validate(report) for report in results_db]