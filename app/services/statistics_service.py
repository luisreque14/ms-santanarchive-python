from typing import Optional

from app.database import get_db

class StatisticsService:

    async def get_instrumental_logic(album_id: Optional[int] = None):
        db = get_db()
        match_query = {"album_id": album_id} if album_id else {}

        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$album_id" if album_id else None,
                "total_instrumental": {"$sum": {"$cond": ["$metadata.is_instrumental", 1, 0]}},
                "total_vocal": {"$sum": {"$cond": ["$metadata.is_instrumental", 0, 1]}}
            }},
            {"$lookup": {"from": "albums", "localField": "_id", "foreignField": "id", "as": "info"}},
            {"$unwind": {"path": "$info", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "album_id": "$_id",
                "album_name": {
                    "$cond": [album_id is None, "Discografía Completa", {"$ifNull": ["$info.title", "Desconocido"]}]},
                "total_instrumental": 1, "total_vocal": 1, "_id": 0
            }}
        ]
        result = await db.tracks.aggregate(pipeline).to_list(1)
        return result[0] if result else None

    async def get_key_stats_logic(album_id: Optional[int] = None):
        db = get_db()
        match_query = {"album_id": album_id} if album_id else {}

        pipeline = [
            {"$match": match_query},
            {"$group": {"_id": {"aid": "$album_id", "k": "$metadata.key"}, "count": {"$sum": 1}}},
            {"$lookup": {"from": "albums", "localField": "_id.aid", "foreignField": "id", "as": "info"}},
            {"$unwind": {"path": "$info", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "album_id": "$_id.aid",
                "key": "$_id.k",
                "count": 1,
                "album_name": {"$cond": [album_id is None, "Discografía Completa", "$info.title"]},
                "_id": 0
            }},
            {"$sort": {"count": -1}}
        ]
        return await db.tracks.aggregate(pipeline).to_list(None)

    async def get_executive_summary_logic():
        db = get_db()
        if db is None:
            return None

        pipeline = [
            {
                "$facet": {
                    "general_stats": [
                        {
                            "$group": {
                                "_id": None,
                                "total": { "$sum": 1 },
                                "instrumentals": {
                                    "$sum": { "$cond": ["$metadata.is_instrumental", 1, 0] }
                                },
                                "love_songs": {
                                    "$sum": { "$cond": ["$metadata.is_love_song", 1, 0] }
                                }
                            }
                        }
                    ],
                    "most_used_key": [
                        { "$group": { "_id": "$metadata.key", "count": { "$sum": 1 } } },
                        { "$sort": { "count": -1 } },
                        { "$limit": 1 }
                    ]
                }
            },
            {
                "$project": {
                    "stats": { "$arrayElemAt": ["$general_stats", 0] },
                    "key_info": { "$arrayElemAt": ["$most_used_key", 0] }
                }
            },
            {
                "$project": {
                    "total_tracks": "$stats.total",
                    "instrumental_percentage": {
                        "$cond": [
                            { "$gt": ["$stats.total", 0] },
                            { "$multiply": [{ "$divide": ["$stats.instrumentals", "$stats.total"] }, 100] },
                            0
                        ]
                    },
                    "love_songs_percentage": {
                        "$cond": [
                            { "$gt": ["$stats.total", 0] },
                            { "$multiply": [{ "$divide": ["$stats.love_songs", "$stats.total"] }, 100] },
                            0
                        ]
                    },
                    "most_used_key": { "$ifNull": ["$key_info._id", "N/A"] }
                }
            }
        ]

        cursor = db.tracks.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0] if result and result[0].get("total_tracks") is not None else None