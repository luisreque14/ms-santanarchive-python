from fastapi import APIRouter, HTTPException, Query
from app.database import get_db
from app.models.statistics.discography.instrumental_tracks import InstrumentalStatsResponse
from typing import Optional

router = APIRouter()

@router.get("/instrumental-tracks", response_model=InstrumentalStatsResponse)
async def get_instrumental_tracks(
        album_id: Optional[int] = Query(None, description="ID del álbum opcional")
):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no conectada")

    # 1. Definimos el filtro inicial
    match_query = {}
    if album_id is not None:
        match_query = {"album_id": album_id}

    pipeline = [
        # Filtrar por álbum o traer todo
        {"$match": match_query},

        # 2. Agrupación y conteo
        {
            "$group": {
                # Si hay album_id, agrupamos por él. Si no, agrupamos todo en un solo bloque (null)
                "_id": "$album_id" if album_id is not None else None,
                "total_instrumental": {
                    "$sum": {"$cond": ["$metadata.is_instrumental", 1, 0]}
                },
                "total_vocal": {
                    "$sum": {"$cond": ["$metadata.is_instrumental", 0, 1]}
                }
            }
        },

        # 3. Lookup para el nombre (solo si hay un ID específico)
        {
            "$lookup": {
                "from": "albums",
                "localField": "_id",
                "foreignField": "id",
                "as": "album_info"
            }
        },
        {"$unwind": {"path": "$album_info", "preserveNullAndEmptyArrays": True}},

        # 4. Proyección final con lógica para el nombre global
        {
            "$project": {
                "_id": 0,
                "album_id": "$_id",
                "album_name": {
                    "$cond": [
                        {"$eq": [album_id, None]},
                        "Discografía Completa",
                        {"$ifNull": ["$album_info.title", "Desconocido"]}
                    ]
                },
                "total_instrumental": 1,
                "total_vocal": 1
            }
        }
    ]

    cursor = db.tracks.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        raise HTTPException(status_code=404, detail="No se encontraron datos para calcular estadísticas")

    return result[0]