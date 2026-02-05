from fastapi import Depends
from app.database import get_db
from app.repositories.statistics_repository import StatisticsRepository
from app.services.statistics_service import StatisticsService
from app.repositories.album_repository import AlbumRepository
from app.services.album_service import AlbumService
from app.repositories.composer_repository import ComposerRepository
from app.services.composer_service import ComposerService
from app.repositories.geography_repository import GeographyRepository
from app.services.geography_service import GeographyService
from app.repositories.musician_repository import MusicianRepository
from app.services.musician_service import MusicianService
from app.repositories.performance_repository import PerformanceRepository
from app.services.performance_service import PerformanceService
from app.repositories.track_repository import TrackRepository
from app.services.track_service import TrackService
from app.repositories.discography_executive_summary_repository import DiscographyExecutiveSummaryRepository
from app.repositories.concert_repository import ConcertRepository
from app.services.concert_service import ConcertService
from app.repositories.concert_masters_repository import ConcertMastersRepository
from app.services.concert_masters_service import ConcertMastersService

def get_stats_service(db=Depends(get_db)):
    repo = StatisticsRepository(db)
    executiveSummaryRepo = DiscographyExecutiveSummaryRepository(db)
    return StatisticsService(repo, executiveSummaryRepo)

def get_album_service(db=Depends(get_db)):
    repo = AlbumRepository(db)
    return AlbumService(repo)

def get_composer_service(db=Depends(get_db)):
    repo = ComposerRepository(db)
    return ComposerService(repo)

def get_geo_service(db=Depends(get_db)):
    repo = GeographyRepository(db)
    return GeographyService(repo)

def get_musician_service(db=Depends(get_db)):
    return MusicianService(MusicianRepository(db))

def get_performance_service(db=Depends(get_db)):
    return PerformanceService(PerformanceRepository(db))

def get_track_service(db=Depends(get_db)):
    return TrackService(TrackRepository(db))

def get_concert_service(db=Depends(get_db)):
    return ConcertService(ConcertRepository(db))

def get_concert_masters_service(db=Depends(get_db)):
    return ConcertMastersService(ConcertMastersRepository(db))
