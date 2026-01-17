from motor.motor_asyncio import AsyncIOMotorDatabase

class MediaRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # Verificaciones de integridad
    async def album_exists(self, album_id: int) -> bool:
        return await self.db.albums.find_one({"id": album_id}) is not None

    async def concert_exists(self, concert_id: int) -> bool:
        return await self.db.concerts.find_one({"id": concert_id}) is not None

    # Operaciones de inserción
    async def insert_album_photo(self, photo_data: dict):
        await self.db.album_photos.insert_one(photo_data)
        return True

    async def insert_concert_video(self, video_data: dict):
        await self.db.concert_videos.insert_one(video_data)
        return True

    # Consultas
    async def get_videos_by_concert(self, concert_id: int):
        return await self.db.concert_videos.find(
            {"concert_id": concert_id}, 
            {"_id": 0}
        ).to_list(10)