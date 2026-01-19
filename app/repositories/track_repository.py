from motor.motor_asyncio import AsyncIOMotorDatabase

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
                            "composers": "$composers_info.full_name",
                            "guest_artists": {"$ifNull": ["$guests_info.full_name", []]},
                            "metadata": 1 
                        }
                    }
                ]
        
        return await self.db.tracks.aggregate(pipeline).to_list(length=100)

    async def get_tracks_by_date_range_pipeline(self, start_year: int, end_year: int):
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
                            "title": 1,
                            "albumId": "$album_info.id",
                            "albumTitle": "$album_info.title", # validation_alias="album"
                            "albumReleaseYear": "$album_info.release_year", # validation_alias="year"
                            "albumCover": "$album_info.cover",
                            "metadata": 1,
                            # Extraemos solo el campo 'name' de cada objeto en el array resultante
                            "genres": "$genres_info.name", 
                            "composers": "$composers_info.full_name",
                            # validation_alias="guestArtists"
                            "guestArtists": "$guests_info.full_name" # O el campo donde guardes el nombre del invitado
                        }
                    },
                    {"$sort": {"albumReleaseYear": 1}}
                ]
        return await self.db.tracks.aggregate(pipeline).to_list(length=None)