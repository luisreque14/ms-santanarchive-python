from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

class TrackRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_genre_by_id(self, genre_id: int):
        return await self.db.genres.find_one({"id": genre_id})

    async def get_tracks_with_details(self, match_stage: dict):
        pipeline = [
            {"$match": match_stage},
            {
                "$lookup": {
                    "from": "albums",
                    "localField": "album_id",
                    "foreignField": "id",
                    "as": "album_info"
                }
            },
            {"$unwind": {"path": "$album_info", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": "genres", "localField": "genre_ids", "foreignField": "id", "as": "genres_info"}},
            {"$lookup": {"from": "composers", "localField": "composer_ids", "foreignField": "id", "as": "composers_info"}},
            {"$lookup": {"from": "guests", "localField": "guest_ids", "foreignField": "id", "as": "guests_info"}},
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "album": {"$ifNull": ["$album_info.title", "Unknown Album"]},
                    "year": {"$ifNull": ["$album_info.release_year", 0]},
                    "genres": "$genres_info.name",
                    "composers": "$composers_info.name",
                    "guests": {"$ifNull": ["$guests_info.full_name", []]},
                    "metadata": 1
                }
            }
        ]
        return await self.db.tracks.aggregate(pipeline).to_list(length=100)

    async def get_tracks_by_date_range_pipeline(self, start_year: int, end_year: int):
        pipeline = [
            # ... (Aquí va tu pipeline #2 que filtra por años y colaboradores) ...
            # Mantenemos el pipeline tal cual lo definiste
            {"$lookup": {"from": "albums", "localField": "album_id", "foreignField": "id", "as": "album_info"}},
            {"$unwind": "$album_info"},
            {
                "$match": {
                    "album_info.release_year": {"$gte": start_year, "$lte": end_year},
                    "collaborator_ids": {"$exists": True, "$not": {"$size": 0}}
                }
            },
            # ... Resto de los lookups de colaboradores, compositores y géneros ...
        ]
        return await self.db.tracks.aggregate(pipeline).to_list(length=None)