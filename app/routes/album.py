from fastapi import APIRouter, HTTPException, Query
from app.models.album import AlbumSchema
from app.database import get_db
from typing import List, Optional

router = APIRouter()


@router.post("/", status_code=201)
async def create_album(album: AlbumSchema):
    db = get_db()

    if db is None:
        raise HTTPException(status_code=500, detail="La base de datos no está conectada")

    # Verificar si el álbum ya existe
    if await db.albums.find_one({"id": album.id}):
        raise HTTPException(status_code=400, detail="Album ID already exists")

    await db.albums.insert_one(album.model_dump())
    return {"message": "Album and tracklist created successfully"}


@router.get("/")
async def get_albums(era: Optional[str] = Query("all")):
    db = get_db()
    query = {}

    # Si la era es una década (ej: 1970), filtramos por el rango de años
    if era != "all" and era.isdigit():
        start_year = int(era)
        end_year = start_year + 9
        query["release_year"] = {"$gte": start_year, "$lte": end_year}

    # Ordenamos por año para que la discografía tenga sentido cronológico
    albums = await db.albums.find(query, {"_id": 0}).sort("release_year", 1).to_list(length=100)

    # Mapeamos los campos para que coincidan con lo que espera tu componente
    # (Agregamos una imagen por defecto si no tienes el campo 'cover' en la BD)
    for album in albums:
        album["cover"] = album.get("cover", "/images/default-album.jpg")

    return albums


@router.get("/{album_id}")
async def get_album_by_id(album_id: int):
    db = get_db()
    album = await db.albums.find_one({"id": album_id}, {"_id": 0})
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return album


@router.get("/{album_id}/tracks")
async def get_album_tracks(album_id: int):
    db = get_db()

    pipeline = [
        {"$match": {"album_id": album_id}},
        {"$sort": {"track_number": 1}},  # Ordenar por número de pista

        # 1. Lookup para Compositores
        {
            "$lookup": {
                "from": "composers",
                "localField": "composer_ids",
                "foreignField": "id",
                "as": "composers_info"
            }
        },

        # 2. Lookup para Colaboradores (Nuevo)
        {
            "$lookup": {
                "from": "collaborators",
                "localField": "collaborator_ids",
                "foreignField": "id",
                "as": "collaborators_info"
            }
        },

        # 3. Proyección de campos
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "track_number": 1,
                "duration": 1,
                "composers": "$composers_info.full_name",
                "collaborators": "$collaborators_info.full_name",  # Extrae solo los nombres
                "metadata": 1
            }
        }
    ]

    tracks = await db.tracks.aggregate(pipeline).to_list(length=100)

    # Retornamos lista vacía si no hay resultados, manteniendo consistencia
    return tracks if tracks else []