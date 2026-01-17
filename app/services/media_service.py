from fastapi import HTTPException
from app.repositories.media_repository import MediaRepository

class MediaService:
    def __init__(self, repository: MediaRepository):
        self.repo = repository

    async def add_photo_to_album(self, photo_schema):
        if not await self.repo.album_exists(photo_schema.album_id):
            raise HTTPException(status_code=404, detail="Album not found")
        return await self.repo.insert_album_photo(photo_schema.model_dump())

    async def add_video_to_concert(self, video_schema):
        if not await self.repo.concert_exists(video_schema.concert_id):
            raise HTTPException(status_code=404, detail="Concert not found")
        return await self.repo.insert_concert_video(video_schema.model_dump())

    async def get_concert_multimedia(self, concert_id: int):
        # Aquí podrías validar también si el concierto existe antes de buscar videos
        return await self.repo.get_videos_by_concert(concert_id)