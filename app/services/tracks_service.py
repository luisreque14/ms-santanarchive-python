from typing import Optional

from app.database import get_db

class TracksService:

    async def get_tracks(album_id: Optional[int] = None):
        db = get_db()

        # 1. Filtro inicial por ID de álbum
        match_stage = {"album_id": album_id} if album_id else {}

        pipeline = [
            # Filtrar primero es lo más eficiente
            {"$match": match_stage},

            # 2. Join con Albums
            {
                "$lookup": {
                    "from": "albums",
                    "localField": "album_id",
                    "foreignField": "id",
                    "as": "album_info"
                }
            },
            # preserveNullAndEmptyArrays evita que el track desaparezca si no tiene álbum
            {"$unwind": {"path": "$album_info", "preserveNullAndEmptyArrays": True}},

            # 3. Joins con Géneros y Compositores
            {"$lookup": {"from": "genres", "localField": "genre_ids", "foreignField": "id", "as": "genres_info"}},
            {"$lookup": {"from": "composers", "localField": "composer_ids", "foreignField": "id",
                         "as": "composers_info"}},

            # 4. NUEVO: Join con Guests (Colección de colaboradores)
            {
                "$lookup": {
                    "from": "guests",
                    "localField": "guest_ids",  # El array de IDs en Tracks
                    "foreignField": "id",  # El campo ID en Guests
                    "as": "guests_info"
                }
            },

            # 5. Proyección final corregida
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    # Usamos $ifNull para que Pydantic no falle si los datos no existen
                    "album": {"$ifNull": ["$album_info.title", "Unknown Album"]},
                    "year": {"$ifNull": ["$album_info.release_year", 0]},
                    "genres": "$genres_info.name",
                    "composers": "$composers_info.name",
                    # Mapeamos los nombres de los invitados. Si no hay, devuelve lista vacía []
                    "guests": {"$ifNull": ["$guests_info.full_name", []]},
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

    @staticmethod
    async def get_tracks_by_date_range(start_year: int, end_year: int):
        db = get_db()

        pipeline = [
            # 1. Join con Albums para obtener nombre y año
            {
                "$lookup": {
                    "from": "albums",
                    "localField": "album_id",
                    "foreignField": "id",
                    "as": "album_info"
                }
            },
            {"$unwind": "$album_info"},

            # 2. Filtro por rango de años
            {
                "$match": {
                    "album_info.release_year": {"$gte": start_year, "$lte": end_year},
                    "collaborator_ids": {"$exists": True, "$not": {"$size": 0}}
                }
            },

            # 3. Join con Collaborators para los nombres
            {
                "$lookup": {
                    "from": "collaborators",
                    "localField": "collaborator_ids",
                    "foreignField": "id",
                    "as": "collabs_data"
                }
            },

            # 4. Join con Composers
            {
                "$lookup": {
                    "from": "composers",
                    "localField": "composer_ids",
                    "foreignField": "id",
                    "as": "composers_data"
                }
            },

            # 5. Join con Genres
            {
                "$lookup": {
                    "from": "genres",
                    "localField": "genre_ids",
                    "foreignField": "id",
                    "as": "genres_data"
                }
            },

            # 6. Proyección final (Mapeo exacto a TrackResponse)
            {
                "$project": {
                    "_id": 0,  # Pydantic no lo pide en tu clase, así que lo omitimos
                    "title": 1,
                    "album": "$album_info.title",  # Mapeamos album_id -> nombre del album
                    "year": "$album_info.release_year",  # Mapeamos release_year -> year
                    "genres": "$genres_data.name",  # Array de nombres de géneros
                    "composers": "$composers_data.full_name",  # Array de nombres de compositores
                    "metadata": 1,
                    "collaborators": "$collabs_data.full_name"  # Array de nombres de colaboradores
                }
            }
        ]

        cursor = db.tracks.aggregate(pipeline)
        return await cursor.to_list(length=None)