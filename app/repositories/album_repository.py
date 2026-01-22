from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

class AlbumRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_album_by_id(self, album_id: int):
        return await self.db.albums.find_one({"id": album_id}, {"_id": 0})

    async def create_album(self, album_data: dict):
        await self.db.albums.insert_one(album_data)
        return album_data["id"]

    async def get_tracks_by_album(self, album_id: int):
        pipeline = [
                    {"$match": {"album_id": int(album_id)}},
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
                            # Mapeo exacto a TrackDto (validation_alias="album")
                            "album": {"$ifNull": ["$album_info.title", "Unknown Album"]},
                            # Mapeo exacto a TrackDto (validation_alias="year")
                            "year": {"$ifNull": ["$album_info.release_year", 0]},
                            "genres": "$genres_info.name",
                            "composers": "$composers_info.name",
                            "guestArtists": {"$ifNull": ["$guests_info.full_name", []]},
                            # Pasamos metadata tal cual, asumiendo que en la BD ya tiene 
                            # las llaves: key, is_instrumental, is_live, is_love_song
                            "metadata": 1 
                        }
                    }
                ]
        
        return await self.db.tracks.aggregate(pipeline).to_list(length=100)
    
    async def get_albums(self, era: str = "all") -> list:
        # 1. Definir el filtro inicial (Era)
        match_stage = {}
        if era != "all" and era.isdigit():
            start_year = int(era)
            match_stage = {
                "release_year": {
                    "$gte": start_year, 
                    "$lte": start_year + 9
                }
            }

        pipeline = [
            # Filtrar álbumes por la década seleccionada antes de unir con tracks
            {"$match": match_stage} if match_stage else {"$match": {}},
            
            {
                "$lookup": {
                    "from": "tracks",
                    "localField": "id",
                    "foreignField": "album_id",
                    "as": "album_tracks"
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "id": 1,
                    "title": 1,
                    "release_date": 1,
                    "release_year": 1,
                    "cover": 1,
                    "is_live": 1,
                    "duration": { 
                        "$ifNull": [{"$sum": "$album_tracks.duration_seconds"}, 0] 
                    }
                }
            },
            {"$sort": {"id": 1}}
        ]
        
        cursor = self.db.albums.aggregate(pipeline)
        return await cursor.to_list(length=None)
    
    async def get_albums_by_studio_instrumental(self) -> List[dict]:
        pipeline = [
            # 1. Filtrar solo álbumes de estudio
            {
                "$match": {
                    "is_live": False
                }
            },
            # 2. Join con tracks para obtener canciones NO instrumentales
            {
                "$lookup": {
                    "from": "tracks",
                    "let": {"album_id_val": "$id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$album_id", "$$album_id_val"]},
                                        {"$eq": ["$metadata.is_instrumental", True]}
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "album_tracks"
                }
            },
            # 3. Proyectar los campos solicitados y calcular estadísticas
            {
                "$project": {
                    "_id": 0,
                    "id": 1,
                    "title": 1,
                    "release_date": 1,
                    "release_year": 1,
                    "cover": 1,
                    "is_live": 1,
                    "instrumental_tracks_count": {"$size": "$album_tracks"},
                    "duration": { 
                        "$ifNull": [{"$sum": "$album_tracks.duration_seconds"}, 0] 
                    }
                }
            },
            # 4. Ordenar por año de lanzamiento (opcional pero recomendado)
            {"$sort": {"release_year": -1}}
        ]

        cursor = self.db.albums.aggregate(pipeline)
        return await cursor.to_list(length=None)