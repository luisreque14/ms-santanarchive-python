from fastapi import APIRouter, HTTPException, Query
from app.database import get_db
from app.models.statistics.discography.song_insights import SongFlatResponse
from typing import List, Optional

router = APIRouter()


@router.get("/tracks", response_model=List[SongFlatResponse])
async def get_all_tracks(
        album_id: Optional[int] = Query(None)
):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no conectada")

    # 1. Filtro dinámico: Si album_id es None, el match será {} (trae todo)
    match_query = {}
    if album_id is not None:
        match_query = {"album_id": album_id}

    # 2. Pipeline de agregación
    pipeline = [
        # Filtramos las canciones (todas o por album_id)
        {"$match": match_query},

        # Unimos con la colección de álbumes
        {
            "$lookup": {
                "from": "albums",  # Nombre de tu colección de álbumes
                "localField": "album_id",  # Campo en la colección 'tracks'
                "foreignField": "id",  # Campo en la colección 'albums'
                "as": "album_details"
            }
        },

        # Convertimos el array 'album_details' en un objeto simple
        {"$unwind": "$album_details"},

        # Estructuramos la respuesta final
        {
            "$project": {
                "_id": 0,
                "album_id": 1,
                "album_name": "$album_details.title",  # Extraemos el título del álbum
                "album_cover": "$album_details.cover",  # Extraemos la portada del álbum
                "title": 1,
                "track_number": 1,
                "side": 1,
                "duration": 1,
                "composer_ids": 1,
                "genre_ids": 1,
                "metadata": 1
            }
        },

        # Ordenamos por álbum y luego por número de pista
        {"$sort": {"album_id": 1, "track_number": 1}}
    ]

    cursor = db.tracks.aggregate(pipeline)
    result = await cursor.to_list(length=1000)

    if not result:
        raise HTTPException(status_code=404, detail="No se encontraron canciones con los criterios proporcionados")

    return result