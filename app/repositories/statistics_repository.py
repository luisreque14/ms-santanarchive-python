from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

class StatisticsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def run_instrumental_aggregation(self, match_query: dict, is_single_album: bool):
        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$album_id" if is_single_album else None,
                "total_instrumental": {"$sum": {"$cond": ["$metadata.is_instrumental", 1, 0]}},
                "total_vocal": {"$sum": {"$cond": ["$metadata.is_instrumental", 0, 1]}}
            }},
            {"$lookup": {"from": "albums", "localField": "_id", "foreignField": "id", "as": "info"}},
            {"$unwind": {"path": "$info", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "album_id": "$_id",
                "album_name": "$info.title",
                "total_instrumental": 1, "total_vocal": 1, "_id": 0
            }}
        ]
        return await self.db.tracks.aggregate(pipeline).to_list(1)

    async def run_executive_summary_pipeline(self):
        # Aquí pegas el pipeline gigante de $facet que ya tienes
        pipeline = [
            {"$facet": {
                "general_stats": [
                    {"$group": {
                        "_id": None,
                        "total": { "$sum": 1 },
                        "instrumentals": {"$sum": {"$cond": ["$metadata.is_instrumental", 1, 0]}},
                        "love_songs": {"$sum": {"$cond": ["$metadata.is_love_song", 1, 0]}}
                    }}
                ],
                "most_used_key": [
                    {"$group": {"_id": "$metadata.key", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 1}
                ]
            }},
            # ... resto del project que ya definiste ...
        ]
        return await self.db.tracks.aggregate(pipeline).to_list(1)

    async def get_genre_stats_pipeline(self):
        # Aquí va tu pipeline de unwind de genre_ids
        # (Omitido por brevedad, pero iría aquí íntegro)
        pass