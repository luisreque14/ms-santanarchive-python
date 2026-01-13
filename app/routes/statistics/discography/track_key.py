from fastapi import APIRouter, HTTPException, Query
from app.database import get_db
from app.models.statistics.discography.track_key import TrackKeyStats
from typing import List, Optional

router = APIRouter()

@router.get("/tone-stats", response_model=List[TrackKeyStats])
async def get_track_key_stats(
        album_id: Optional[int] = Query(None, description="ID del álbum opcional")
):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no conectada")

    # 1. Filtro inicial dinámico
    match_query = {}
    if album_id is not None:
        match_query = {"album_id": album_id}

    pipeline = [
        # Filtramos por álbum o traemos todo
        {"$match": match_query},

        # 2. Agrupamos por Album ID y por la Tonalidad (Key)
        {
            "$group": {
                "_id": {
                    "album_id": "$album_id",
                    "key": "$metadata.key"
                },
                "count": {"$sum": 1}
            }
        },

        # 3. Unimos con la colección de álbumes para obtener el nombre
        {
            "$lookup": {
                "from": "albums",
                "localField": "_id.album_id",
                "foreignField": "id",
                "as": "album_info"
            }
        },
        {"$unwind": {"path": "$album_info", "preserveNullAndEmptyArrays": True}},

        # 4. Proyectamos al formato final
        {
            "$project": {
                "_id": 0,
                "album_id": "$_id.album_id",
                "album_name": {
                    "$cond": [
                        {"$eq": [album_id, None]},
                        "Discografía Completa",
                        {"$ifNull": ["$album_info.title", "Desconocido"]}
                    ]
                },
                "key": "$_id.key",
                "count": 1
            }
        },

        # 5. Ordenamos por cantidad (descendente) o por nota
        {"$sort": {"count": -1}}
    ]

    cursor = db.tracks.aggregate(pipeline)
    result = await cursor.to_list(length=500)

    if not result:
        raise HTTPException(status_code=404, detail="No se encontraron datos para estas estadísticas")

    return result