from app.database import get_db
from typing import Optional, List

class StatisticsRepository:
    """
    Handles all complex MongoDB aggregation pipelines for discography statistics.
    """

    @staticmethod
    async def get_instrumental_stats(match_query: dict, album_id: Optional[int]) -> List[dict]:
        db = get_db()
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
                "album_id": {"$ifNull": ["$_id", 0]},
                "album_name": {
                    "$cond": [album_id is None, "Full Discography", {"$ifNull": ["$info.title", "Unknown"]}]
                },
                "total_instrumental": 1, 
                "total_vocal": 1, 
                "_id": 0
            }}
        ]
        return await db.tracks.aggregate(pipeline).to_list(1)

    @staticmethod
    async def get_key_stats(match_query: dict, album_id: Optional[int]) -> List[dict]:
        db = get_db()
        pipeline = [
            {"$match": match_query},
            {"$group": {"_id": {"aid": "$album_id", "k": "$metadata.key"}, "count": {"$sum": 1}}},
            {"$lookup": {"from": "albums", "localField": "_id.aid", "foreignField": "id", "as": "info"}},
            {"$unwind": {"path": "$info", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "album_id": {"$ifNull": ["$_id.aid", 0]},
                "key": "$_id.k",
                "count": 1,
                "album_name": {"$cond": [album_id is None, "Full Discography", "$info.title"]},
                "_id": 0
            }},
            {"$sort": {"count": -1}}
        ]
        return await db.tracks.aggregate(pipeline).to_list(None)

    @staticmethod
    async def get_executive_summary() -> List[dict]:
        db = get_db()
        pipeline = [
            {
                "$facet": {
                    "general_stats": [
                        {
                            "$group": {
                                "_id": None,
                                "total": { "$sum": 1 },
                                "instrumentals": { "$sum": { "$cond": ["$metadata.is_instrumental", 1, 0] } },
                                "love_songs": { "$sum": { "$cond": ["$metadata.is_love_song", 1, 0] } }
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
                        "$cond": [{"$gt": ["$stats.total", 0]}, 
                                 {"$multiply": [{"$divide": ["$stats.instrumentals", "$stats.total"]}, 100]}, 0]
                    },
                    "love_songs_percentage": {
                        "$cond": [{"$gt": ["$stats.total", 0]}, 
                                 {"$multiply": [{"$divide": ["$stats.love_songs", "$stats.total"]}, 100]}, 0]
                    },
                    "most_used_key": { "$ifNull": ["$key_info._id", "N/A"] }
                }
            }
        ]
        return await db.tracks.aggregate(pipeline).to_list(1)

    @staticmethod
    async def get_love_song_stats() -> List[dict]:
        db = get_db()
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "love_songs": {"$sum": {"$cond": ["$metadata.is_love_song", 1, 0]}}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_tracks": "$total",
                    "love_songs_count": "$love_songs",
                    "non_love_songs_count": {"$subtract": ["$total", "$love_songs"]},
                    "love_songs_percentage": {
                        "$cond": [{"$gt": ["$total", 0]}, 
                                 {"$multiply": [{"$divide": ["$love_songs", "$total"]}, 100]}, 0]
                    },
                    "non_love_songs_percentage": {
                        "$cond": [{"$gt": ["$total", 0]}, 
                                 {"$multiply": [{"$divide": [{"$subtract": ["$total", "$love_songs"]}, "$total"]}, 100]}, 0]
                    }
                }
            }
        ]
        return await db.tracks.aggregate(pipeline).to_list(1)

    @staticmethod
    async def get_genre_stats() -> List[dict]:
        db = get_db()
        pipeline = [
            {"$unwind": "$genre_ids"},
            {
                "$facet": {
                    "counts_by_genre": [
                        {"$group": {"_id": "$genre_ids", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}}
                    ],
                    "total_occurrences": [{"$count": "total"}]
                }
            },
            {"$unwind": "$counts_by_genre"},
            {"$addFields": {"total_sum": {"$arrayElemAt": ["$total_occurrences.total", 0]}}},
            {
                "$lookup": {
                    "from": "genres",
                    "localField": "counts_by_genre._id",
                    "foreignField": "id",
                    "as": "info"
                }
            },
            {"$unwind": "$info"},
            {
                "$project": {
                    "_id": 0,
                    "genre_id": "$counts_by_genre._id",
                    "genre_name": "$info.name",
                    "track_count": "$counts_by_genre.count",
                    "percentage": {
                        "$cond": [{"$gt": ["$total_sum", 0]}, 
                                 {"$multiply": [{"$divide": ["$counts_by_genre.count", "$total_sum"]}, 100]}, 0]
                    }
                }
            }
        ]
        return await db.tracks.aggregate(pipeline).to_list(None)

    @staticmethod
    async def get_collab_report() -> List[dict]:
        db = get_db()
        pipeline = [
            {"$lookup": {"from": "albums", "localField": "album_id", "foreignField": "id", "as": "album_info"}},
            {"$unwind": "$album_info"},
            {
                "$addFields": {
                    "decade_start": {"$subtract": ["$album_info.release_year", {"$mod": ["$album_info.release_year", 10]}]},
                    "has_collaborators": {"$cond": [{"$and": [{"$isArray": "$collaborator_ids"}, {"$gt": [{"$size": "$collaborator_ids"}, 0]}]}, 1, 0]}
                }
            },
            {
                "$group": {
                    "_id": "$decade_start",
                    "total_tracks": {"$sum": 1},
                    "collab_tracks": {"$sum": "$has_collaborators"},
                    "all_collaborator_ids": {"$push": "$collaborator_ids"}
                }
            },
            {
                "$project": {
                    "period": {"$concat": [{"$toString": "$_id"}, "-", {"$toString": {"$add": ["$_id", 9]}}]},
                    "total_tracks": 1,
                    "collab_tracks": 1,
                    "collab_percentage": {"$round": [{"$multiply": [{"$divide": ["$collab_tracks", "$total_tracks"]}, 100]}, 1]},
                    "unique_collaborator_ids": {
                        "$reduce": {
                            "input": "$all_collaborator_ids",
                            "initialValue": [],
                            "in": {"$setUnion": ["$$value", "$$this"]}
                        }
                    }
                }
            },
            {"$lookup": {"from": "collaborators", "localField": "unique_collaborator_ids", "foreignField": "id", "as": "col_data"}},
            {
                "$project": {
                    "_id": 0,
                    "period": 1,
                    "total_tracks": 1,
                    "collab_tracks": 1,
                    "collab_percentage": 1,
                    "collaborators": "$col_data.full_name"
                }
            },
            {"$sort": {"period": 1}}
        ]
        return await db.tracks.aggregate(pipeline).to_list(None)