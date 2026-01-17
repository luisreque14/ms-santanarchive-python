from typing import Optional, List
from app.repositories.statistics_repository import StatisticsRepository

class StatisticsService:
    """
    Business logic layer for discography statistics.
    Orchestrates repository calls and ensures data consistency.
    """

    @staticmethod
    async def get_instrumental_logic(album_id: Optional[int] = None):
        # Business Logic: Determine the filter scope
        match_query = {"album_id": album_id} if album_id else {}
        
        results = await StatisticsRepository.get_instrumental_stats(match_query, album_id)
        
        # Ensure we return a single object or None
        return results[0] if results else None

    @staticmethod
    async def get_key_stats_logic(album_id: Optional[int] = None):
        match_query = {"album_id": album_id} if album_id else {}
        
        # Returns a list of stats per key
        return await StatisticsRepository.get_key_stats(match_query, album_id)

    @staticmethod
    async def get_executive_summary_logic():
        results = await StatisticsRepository.get_executive_summary()
        
        # Validation: Ensure we have data before sending to the response model
        if not results or results[0].get("total_tracks") is None:
            return None
            
        return results[0]

    @staticmethod
    async def get_love_song_stats_logic():
        results = await StatisticsRepository.get_love_song_stats()
        
        return results[0] if results else None

    @staticmethod
    async def get_genre_stats_logic():
        # Pure orchestration: results are already formatted by the repository
        return await StatisticsRepository.get_genre_stats()

    @staticmethod
    async def get_collab_report_logic():
        # Historical reports usually don't need additional logic, 
        # but here you could filter by specific decades if needed.
        return await StatisticsRepository.get_collab_report()