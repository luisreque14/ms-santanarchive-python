from typing import List, Optional
from app.repositories.statistics_concerts_repository import StatisticsConcertsRepository
from app.repositories.concerts_executive_summary_repository import ConcertsExecutiveSummaryRepository
from app.dtos.statistics.concerts.executive_summary_dto import ConcertExecutiveSummaryDto
from app.dtos.track_dto import TrackForConcertDto
from app.dtos.album_dto import AlbumDto

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
    