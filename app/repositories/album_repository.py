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
            {"$match": {"album_id": album_id}},
            {"$sort": {"track_number": 1}},
            {
                "$lookup": {
                    "from": "composers",
                    "localField": "composer_ids",
                    "foreignField": "id",
                    "as": "composers_info"
                }
            },
            {
                "$lookup": {
                    "from": "collaborators",
                    "localField": "collaborator_ids",
                    "foreignField": "id",
                    "as": "collaborators_info"
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "track_number": 1,
                    "duration": 1,
                    "composers": "$composers_info.full_name",
                    "collaborators": "$collaborators_info.full_name",
                    "metadata": 1
                }
            }
        ]
        return await self.db.tracks.aggregate(pipeline).to_list(length=100)