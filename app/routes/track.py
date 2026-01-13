from fastapi import APIRouter, Query
from app.database import get_db
from app.models.music import TrackResponse
from typing import List, Optional

router = APIRouter()


@router.get("/", response_model=List[TrackResponse])
async def get_tracks(album: Optional[str] = None):
    db = get_db()

    # Filtro opcional por nombre de álbum
    match_stage = {}
    if album:
        match_stage["album_info.title"] = {"$regex": album, "$options": "i"}

    pipeline = [
        {"$lookup": {"from": "albums", "localField": "album_id", "foreignField": "id", "as": "album_info"}},
        {"$match": match_stage},
        {"$lookup": {"from": "genres", "localField": "genre_ids", "foreignField": "id", "as": "genres_info"}},
        {"$lookup": {"from": "composers", "localField": "composer_ids", "foreignField": "id", "as": "composers_info"}},
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "album": {"$arrayElemAt": ["$album_info.title", 0]},
                "year": {"$arrayElemAt": ["$album_info.release_year", 0]},
                "genres": "$genres_info.name",
                "composers": "$composers_info.full_name",
                "metadata": 1
            }
        }
    ]
    return await db.tracks.aggregate(pipeline).to_list(length=100)