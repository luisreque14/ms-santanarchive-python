from typing import List, Optional
from app.repositories.statistics_concerts_repository import StatisticsConcertsRepository
from app.repositories.concerts_executive_summary_repository import ConcertsExecutiveSummaryRepository
from app.dtos.statistics.concerts.executive_summary_dto import ConcertExecutiveSummaryDto
from app.dtos.statistics.concerts.concert_year_dto import ConcertYearDto
from app.dtos.track_dto import TrackForConcertDto, NonAlbumTrackDto
from app.dtos.album_dto import AlbumDto
from app.dtos.statistics.concerts.concert_country_dto import ConcertCountryDto

class StatisticsConcertsService:
    def __init__(self, repository: StatisticsConcertsRepository, concertsExecutiveSummaryRepository: ConcertsExecutiveSummaryRepository):
        self.repo = repository
        self.concertsExecutiveSummaryRepository = concertsExecutiveSummaryRepository

    async def get_executive_summary(self) -> Optional[ConcertExecutiveSummaryDto]:
        results = await self.concertsExecutiveSummaryRepository.get_executive_summary()
            
        return ConcertExecutiveSummaryDto.model_validate(results)
    
    async def get_top_20_most_played_songs(self) -> List[TrackForConcertDto]:
        results_db = await self.concertsExecutiveSummaryRepository.get_top_20_most_played_songs()
        
        return [TrackForConcertDto.model_validate(report) for report in results_db]
    
    async def get_top_10_most_played_albums(self) -> List[TrackForConcertDto]:
        results_db = await self.concertsExecutiveSummaryRepository.get_top_10_most_played_studio_albums()
        
        return [AlbumDto.model_validate(report) for report in results_db]
    
    async def get_concerts_stats_by_year(self) -> List[ConcertYearDto]:
        results_db = await self.concertsExecutiveSummaryRepository.get_concerts_stats_by_year()
        
        return [ConcertYearDto.model_validate(report) for report in results_db]
    
    async def get_concert_counts_by_country(self) -> List[ConcertCountryDto]:
        results_db = await self.concertsExecutiveSummaryRepository.get_concert_counts_by_country()
        
        return [ConcertCountryDto.model_validate(report) for report in results_db]
    
    async def get_top_20_concert_opener_tracks(self) -> List[TrackForConcertDto]:
        results_db = await self.concertsExecutiveSummaryRepository.get_top_20_concert_opener_tracks()
        
        return [TrackForConcertDto.model_validate(report) for report in results_db]
    
    async def get_non_album_songs(self) -> List[NonAlbumTrackDto]:
        results_db = await self.concertsExecutiveSummaryRepository.get_non_album_songs()
        
        return [NonAlbumTrackDto.model_validate(report) for report in results_db]
    