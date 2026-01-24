from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional

class TrackRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_genre_by_id(self, genre_id: int):
        return await self.db.genres.find_one({"id": genre_id})

    async def get_by_album(self, match_stage: dict):
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
                            "track_number": 1,
                            "title": 1,
                            "duration": 1,
                            "duration_seconds": 1,
                            "album": {"$ifNull": ["$album_info.title", "Unknown Album"]},
                            "year": {"$ifNull": ["$album_info.release_year", 0]},
                            "genres": "$genres_info.name",
                            "composers": "$composers_info.full_name",
                            "guest_artists": {"$ifNull": ["$guests_info.full_name", []]},
                            "metadata": 1 
                        }
                    }
                ]
        
        return await self.db.tracks.aggregate(pipeline).to_list(length=100)

    async def get_by_guest_artists_range(self, start_year: int, end_year: int):
        pipeline = [
                    # 1. Filtro inicial: Asegurar que guest_artist_ids existe y tiene datos
                    {
                        "$match": {
                            "guest_artist_ids": {"$exists": True, "$not": {"$size": 0}}
                        }
                    },
                    # 2. Lookups
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
                    {"$lookup": {"from": "collaborators", "localField": "guest_artist_ids", "foreignField": "id", "as": "guests_info"}},

                    # 3. Filtro por año (ahora que tenemos album_info)
                    {
                        "$match": {
                            "album_info.release_year": {"$gte": start_year, "$lte": end_year}
                        }
                    },
                    # 4. Proyección ajustada a tus validation_alias del DTO
                    {
                        "$project": {
                            "_id": 0,
                            "id": 1,
                            "track_number": 1,
                            "title": 1,
                            "duration": 1,
                            "duration_seconds": 1,
                            "album_id": "$album_info.id",
                            "album_title": "$album_info.title",
                            "album_release_year": "$album_info.release_year",
                            "album_release_date": "$album_info.release_date",
                            "album_cover": "$album_info.cover",
                            "metadata": 1,
                            "genres": "$genres_info.name", 
                            "composers": "$composers_info.full_name",
                            "guestArtists": "$guests_info.full_name" # O el campo donde guardes el nombre del invitado
                        }
                    },
                    {"$sort": {"album_release_year": 1}}
                ]
        return await self.db.tracks.aggregate(pipeline).to_list(length=None)

    async def get_by_top_duration(
            self, 
            order: str = "desc", 
            is_live: Optional[bool] = None
        ) -> List[dict]:
            # 1. Determinar dirección: 1 para ASC, -1 para DESC
            direction = -1 if order.lower() == "desc" else 1

            # 2. Construir el filtro dinámico
            match_filter = {}
            if is_live is not None:
                match_filter["metadata.is_live"] = is_live

            pipeline = [
                # Filtramos antes de ordenar para optimizar la búsqueda
                {"$match": match_filter},
                
                # Ordenamos por duración
                {"$sort": {"duration_seconds": direction}},
                
                # Limitamos al Top 10
                {"$limit": 10},
                
                # Join con la colección albums
                {
                    "$lookup": {
                        "from": "albums",
                        "localField": "album_id",
                        "foreignField": "id",
                        "as": "album_info"
                    }
                },
                {"$unwind": "$album_info"},
                {
                    "$project": {
                        "_id": 0,
                        "track_number": 1,
                        "title": 1,
                        "duration": 1,
                        "duration_seconds": 1,
                        "album_id": 1,
                        "album_title": "$album_info.title",
                        "album_release_year": "$album_info.release_year",
                        "album_release_date": "$album_info.release_date",
                        "album_cover": "$album_info.cover"
                    }
                }
            ]

            cursor = self.db.tracks.aggregate(pipeline)
            return await cursor.to_list(length=10)
        
    async def get_by_lead_vocal(self, musician_id: int) -> List[dict]:
        pipeline = [
            # 1. Filtrar tracks donde el músico es Lead Vocal
            {
                "$match": {
                    "lead_vocal_ids": musician_id
                }
            },
            
            # 2. Join con ALBUMS para obtener detalles del álbum
            {
                "$lookup": {
                    "from": "albums",
                    "localField": "album_id",
                    "foreignField": "id",
                    "as": "album_info"
                }
            },
            
            # 3. Descomponer el array de album_info
            {"$unwind": {"path": "$album_info"}},

            # 4. Proyectar los campos solicitados
            {
                "$project": {
                    "_id": 0,
                    "track_number": 1,
                    "title": 1,
                    "duration": 1,
                    "duration_seconds": 1,
                    "album_id": 1,
                    "album_title": "$album_info.title",
                    "album_release_year": "$album_info.release_year",
                    "album_release_date": "$album_info.release_date",
                    "album_cover": "$album_info.cover"
                }
            },

            # 5. Ordenar por año de lanzamiento y luego por número de track
            {
                "$sort": {
                    "album_release_year": -1,
                    "track_number": 1
                }
            }
        ]

        cursor = self.db.tracks.aggregate(pipeline)
        return await cursor.to_list(length=None)
    
    async def get_by_live_in_studio_albums(self) -> List[dict]:
        pipeline = [
            # 1. Filtramos tracks grabados en vivo (is_live: true)
            {
                "$match": {
                    "metadata.is_live": True
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
            # 3. Validamos que el join haya encontrado un álbum
            {
                "$match": {
                    "album_info": { "$ne": [] }
                }
            },
            # 4. Aplanamos para acceder a las propiedades del álbum
            {"$unwind": "$album_info"},
            # 5. Filtramos solo los que pertenecen a álbumes de estudio
            {
                "$match": {
                    "album_info.is_live": False
                }
            },
            # 6. Proyección final con el mapeo solicitado
            {
                "$project": {
                    "_id": 0,
                    "track_number": 1,
                    "title": 1,
                    "duration": 1,
                    "duration_seconds": 1,
                    "album_id": 1,
                    "album_title": "$album_info.title",
                    "album_release_year": "$album_info.release_year",
                    "album_release_date": "$album_info.release_date",
                    "album_cover": "$album_info.cover"
                }
            },
            # 7. Orden opcional por año y número de track
            {
                "$sort": {
                    "album_release_year": -1,
                    "track_number": 1
                }
            }
        ]

        cursor = self.db.tracks.aggregate(pipeline)
        return await cursor.to_list(length=None)