from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase

class StatisticsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_instrumental_stats(self, match_query: dict, album_id: Optional[int]) -> List[dict]:
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
        return await self.db.tracks.aggregate(pipeline).to_list(1)

    async def get_key_stats(self, match_query: dict, album_id: Optional[int]) -> List[dict]:
        pipeline = [
                {"$match": match_query},
                {"$group": {"_id": {"aid": "$album_id", "k": "$metadata.key"}, "count": {"$sum": 1}}},
                {"$lookup": {"from": "albums", "localField": "_id.aid", "foreignField": "id", "as": "info"}},
                {"$unwind": {"path": "$info", "preserveNullAndEmptyArrays": True}},
                {"$project": {
                    "album_id": {"$ifNull": ["$_id.aid", 0]},
                    "key": "$_id.k",
                    "count": 1,
                    # Lógica corregida:
                    "album_name": {
                        "$cond": {
                            "if": {"$and": [
                                {"$eq": [album_id, None]}, # Si el parámetro de búsqueda fue None
                                {"$eq": ["$_id.aid", None]} # Y el registro no tiene album_id
                            ]},
                            "then": "Full Discography",
                            "else": {"$ifNull": ["$info.title", "Unknown Album"]}
                        }
                    },
                    "_id": 0
                }},
                {"$sort": {"count": -1}}
            ]
        
        return await self.db.tracks.aggregate(pipeline).to_list(None)

    async def get_love_song_stats(self) -> List[dict]:
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
        return await self.db.tracks.aggregate(pipeline).to_list(1)

    async def get_musical_genre_stats(self) -> List[dict]:
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
        return await self.db.tracks.aggregate(pipeline).to_list(None)

    async def get_guest_artists_report(self) -> List[dict]:
        pipeline = [
            {"$lookup": {"from": "albums", "localField": "album_id", "foreignField": "id", "as": "album_info"}},
            {"$unwind": "$album_info"},
            {
                "$addFields": {
                    "decade_start": {"$subtract": ["$album_info.release_year", {"$mod": ["$album_info.release_year", 10]}]},
                    "has_guest_artists": {"$cond": [{"$and": [{"$isArray": "$guest_artist_ids"}, {"$gt": [{"$size": "$guest_artist_ids"}, 0]}]}, 1, 0]}
                }
            },
            {
                "$group": {
                    "_id": "$decade_start",
                    "total_tracks": {"$sum": 1},
                    "guest_artist_tracks": {"$sum": "$has_guest_artists"},
                    "all_guest_artist_ids": {"$push": "$guest_artist_ids"}
                }
            },
            {
                "$project": {
                    "period": {"$concat": [{"$toString": "$_id"}, "-", {"$toString": {"$add": ["$_id", 9]}}]},
                    "total_tracks": 1,
                    "guest_artist_tracks": 1,
                    "guest_artist_percentage": {"$round": [{"$multiply": [{"$divide": ["$guest_artist_tracks", "$total_tracks"]}, 100]}, 1]},
                    "unique_guest_artist_ids": {
                        "$reduce": {
                            "input": "$all_guest_artist_ids",
                            "initialValue": [],
                            "in": {"$setUnion": ["$$value", "$$this"]}
                        }
                    }
                }
            },
            {"$lookup": {"from": "guest_artists", "localField": "unique_guest_artist_ids", "foreignField": "id", "as": "col_data"}},
            {
                "$project": {
                    "_id": 0,
                    "period": 1,
                    "total_tracks": 1,
                    "guest_artist_tracks": 1,
                    "guest_artist_percentage": 1,
                    "guest_artists": "$col_data.full_name"
                }
            },
            {"$sort": {"period": 1}}
        ]
        return await self.db.tracks.aggregate(pipeline).to_list(None)
    
    async def get_instrumental_tracks_by_year(self) -> List[dict]:
        pipeline = [
            # 1. Filtramos solo tracks instrumentales
            {
                "$match": {
                    "metadata.is_instrumental": True
                }
            },
            # 2. Join con la colección de albums
            {
                "$lookup": {
                    "from": "albums",
                    "localField": "album_id",
                    "foreignField": "id",
                    "as": "album_info"
                }
            },
            # 3. Aplanamos para acceder al año del álbum
            {"$unwind": "$album_info"},
            # 4. Agrupamos por el año de lanzamiento del álbum
            {
                "$group": {
                    "_id": "$album_info.release_year",
                    "total_tracks": { "$sum": 1 }
                }
            },
            # 5. Renombramos y limpiamos la salida
            {
                "$project": {
                    "_id": 0,
                    "year": "$_id",
                    "total_tracks": 1
                }
            },
            # 6. Ordenamos por año de forma descendente
            {
                "$sort": { "year": -1 }
            }
        ]

        cursor = self.db.tracks.aggregate(pipeline)
        return await cursor.to_list(length=None)