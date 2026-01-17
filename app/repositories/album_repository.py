from motor.motor_asyncio import AsyncIOMotorDatabase

class AlbumRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_albums(self, query: dict):
        return await self.db.albums.find(query, {"_id": 0}).sort("release_year", 1).to_list(length=100)

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
                            # CAMBIO: Usamos 'collaborators' para que coincida con tu DTO
                            "collaborators": {"$ifNull": ["$guests_info.full_name", []]},
                            # Pasamos metadata tal cual, asumiendo que en la BD ya tiene 
                            # las llaves: key, is_instrumental, is_live, is_love_song
                            "metadata": 1 
                        }
                    }
                ]
        
        return await self.db.tracks.aggregate(pipeline).to_list(length=100)