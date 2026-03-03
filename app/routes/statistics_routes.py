from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.services.statistics_discography_service import StatisticsDiscographyService
from app.dtos.statistics.discography.executive_summary_dto import DiscographyExecutiveSummaryDto
from app.dtos.statistics.concerts.executive_summary_dto import ConcertExecutiveSummaryDto
from app.dtos.statistics.discography.track_key_dto import TrackKeyStatsDto
from app.dtos.statistics.discography_dto import (
    InstrumentalStatsDto,
    LoveSongStatsDto,
    MusicalGenreStatsDto,
    GuestArtistReportDto,
    InstrumentalTrackByYearDto
    )
from app.core.dependencies import get_stats_discography_service
from app.core.dependencies import get_stats_concerts_service
from app.services.statistics_concerts_service import StatisticsConcertsService
from app.dtos.track_dto import TrackForConcertDto, NonAlbumTrackDto
from app.dtos.album_dto import AlbumDto
from app.dtos.statistics.concerts.concert_year_dto import ConcertYearDto
from app.dtos.statistics.concerts.concert_country_dto import ConcertCountryDto

router = APIRouter(prefix="/statistics", tags=["Statistics"])

@router.get(
    "/instrumental-tracks", 
    response_model=InstrumentalStatsDto,
    response_model_by_alias=True
)
async def get_instrumental_stats(
    album_id: Optional[int] = Query(None),
    service: StatisticsDiscographyService = Depends(get_stats_discography_service)
    ):
    data = await service.get_instrumental_logic(album_id)
    if not data:
        raise HTTPException(status_code=404, detail="No data found for instrumental stats")
    return data

@router.get(
    "/tone-stats", 
    # Mapea 'count' a 'totalTracks' y 'key' a 'musicalKey'
    response_model=List[TrackKeyStatsDto],
    response_model_by_alias=True
)
async def get_key_stats(
    album_id: Optional[int] = Query(None),
    service: StatisticsDiscographyService = Depends(get_stats_discography_service)
):
    return await service.get_key_stats_logic(album_id)

@router.get(
    "/discography/executive-summary", 
    response_model=DiscographyExecutiveSummaryDto,
    response_model_by_alias=True
)
async def get_executive_summary(
    service: StatisticsDiscographyService = Depends(get_stats_discography_service)
):
    data = await service.get_executive_summary()
    if not data:
        raise HTTPException(status_code=404, detail="Could not generate executive summary")
    return data

@router.get(
    "/love-songs", 
    response_model=LoveSongStatsDto,
    response_model_by_alias=True
)
async def get_love_song_stats(
    service: StatisticsDiscographyService = Depends(get_stats_discography_service)
):
    data = await service.get_love_song_stats_logic()
    if not data:
        raise HTTPException(status_code=404, detail="No love song data available")
    return data

@router.get(
    "/musical-genres", 
    response_model=List[MusicalGenreStatsDto],
    response_model_by_alias=True
)
async def get_musical_genre_stats(
    service: StatisticsDiscographyService = Depends(get_stats_discography_service)
):
    return await service.get_musical_genre_stats_logic()

@router.get(
    "/guest-artists", 
    response_model=List[GuestArtistReportDto],
    response_model_by_alias=True
)
async def get_guest_artists_report(
    service: StatisticsDiscographyService = Depends(get_stats_discography_service)
):
    return await service.get_guest_artists_report_logic()

@router.get(
    "/instrumental-tracks-by-year", 
    response_model=List[InstrumentalTrackByYearDto],
    response_model_by_alias=True
)
async def get_instrumental_tracks_by_year(
    service: StatisticsDiscographyService = Depends(get_stats_discography_service)
):
    return await service.get_instrumental_tracks_by_year()

@router.get(
    "/concerts/executive-summary", 
    response_model=ConcertExecutiveSummaryDto,
    response_model_by_alias=True
)
async def get_executive_summary(
    service: StatisticsConcertsService = Depends(get_stats_concerts_service)
):
    data = await service.get_executive_summary()
    if not data:
        raise HTTPException(status_code=404, detail="Could not generate executive summary")
    return data

@router.get(
    "/concerts/get-top-20-most-played-songs", 
    response_model=List[TrackForConcertDto],
    response_model_by_alias=True
)
async def get_top_20_most_played_songs(
    service: StatisticsConcertsService = Depends(get_stats_concerts_service)
):
    return await service.get_top_20_most_played_songs()

@router.get(
    "/concerts/get-top-10-most-played-albums", 
    response_model=List[AlbumDto],
    response_model_by_alias=True
)
async def get_top_10_most_played_albums(
    service: StatisticsConcertsService = Depends(get_stats_concerts_service)
):
    return await service.get_top_10_most_played_albums()

@router.get(
    "/concerts/get-concerts-stats-by-year", 
    response_model=List[ConcertYearDto],
    response_model_by_alias=True
)
async def get_concerts_stats_by_year(
    service: StatisticsConcertsService = Depends(get_stats_concerts_service)
):
    return await service.get_concerts_stats_by_year()

@router.get(
    "/concerts/get-concert-counts-by-country", 
    response_model=List[ConcertCountryDto],
    response_model_by_alias=True
)
async def get_concert_counts_by_country(
    service: StatisticsConcertsService = Depends(get_stats_concerts_service)
):
    return await service.get_concert_counts_by_country()

@router.get(
    "/concerts/get-top-20-concert-opener-tracks", 
    response_model=List[TrackForConcertDto],
    response_model_by_alias=True
)
async def get_top_20_concert_opener_tracks(
    service: StatisticsConcertsService = Depends(get_stats_concerts_service)
):
    return await service.get_top_20_concert_opener_tracks()

@router.get(
    "/concerts/get-non-album-songs", 
    response_model=List[NonAlbumTrackDto],
    response_model_by_alias=True
)
async def get_non_album_songs(
    service: StatisticsConcertsService = Depends(get_stats_concerts_service)
):
    return await service.get_non_album_songs()