from typing import Optional

from app.database import get_db

class TracksService:

    async def get_tracks(album_id: Optional[int] = None):  # Cambiamos a int
        db = get_db()

        match_stage = {"album_id": album_id} if album_id else {}

        pipeline = [
            {"$match": match_stage},  # Filtrar PRIMERO por ID es mucho más rápido
            {
                "$lookup": {
                    "from": "albums",
                    "localField": "album_id",
                    "foreignField": "id",
                    "as": "album_info"
                }
            },
            {"$unwind": "$album_info"},

            # 4. Traer Géneros y Compositores
            {"$lookup": {"from": "genres", "localField": "genre_ids", "foreignField": "id", "as": "genres_info"}},
            {"$lookup": {"from": "composers", "localField": "composer_ids", "foreignField": "id",
                         "as": "composers_info"}},

            # 5. Proyección final corregida
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "album": "$album_info.title",
                    "year": "$album_info.release_year",  # Usando release_year como pediste
                    "genres": "$genres_info.name",
                    "composers": "$composers_info.name",  # Verifica si es 'name' o 'full_name' en tu DB
                    "metadata": 1
                }
            }
        ]

        cursor = db.tracks.aggregate(pipeline)
        return await cursor.to_list(length=100)

    async def get_tracks_by_genre_logic(genre_id: int):
        db = get_db()

        # 1. Verificar que el género existe
        genre_info = await db.genres.find_one({"id": genre_id})
        if not genre_info:
            return None

        pipeline = [
            # Filtrar por el género solicitado
            {"$match": {"genre_ids": genre_id}},

            # Unir con Álbumes para obtener título y año
            {
                "$lookup": {
                    "from": "albums",
                    "localField": "album_id",
                    "foreignField": "id",
                    "as": "album_data"
                }
            },
            {"$unwind": "$album_data"},

            # Unir con Géneros para obtener la lista de nombres
            {
                "$lookup": {
                    "from": "genres",
                    "localField": "genre_ids",
                    "foreignField": "id",
                    "as": "genre_list"
                }
            },

            # Unir con Compositores para obtener la lista de nombres
            {
                "$lookup": {
                    "from": "composers",
                    "localField": "composer_ids",
                    "foreignField": "id",
                    "as": "composer_list"
                }
            },

            # Proyectar a la estructura exacta solicitada
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "album": "$album_data.title",
                    "year": "$album_data.release_year",
                    "genres": "$genre_list.name",
                    "composers": "$composer_list.name",
                    "metadata": 1
                }
            },
            {"$sort": {"year": -1, "title": 1}}
        ]

        cursor = db.tracks.aggregate(pipeline)
        tracks = await cursor.to_list(length=None)

        return {
            "genre_name": genre_info["name"],
            "tracks": tracks
        }