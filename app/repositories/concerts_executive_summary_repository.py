from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio

class ConcertsExecutiveSummaryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_executive_summary(self) -> dict:
        _CARLOS_MUSICIAN_ID = 1
        _CARLOS_COMPOSER_ID = 11
        
        tasks = [
            self.get_total_concerts_count(),
            self.get_most_played_song()
        ]
        
        # gather espera a que todas terminen y devuelve los resultados en orden
        (
            total_concerts,
            most_played_data,
        ) = await asyncio.gather(*tasks)

        song_name = most_played_data.get("name") if most_played_data else "N/A"

        # Unimos todas las piezas en el resumen final
        return {
            "total_concerts": total_concerts,
            "most_played_song": song_name
        }

    async def get_total_concerts_count(self) -> int:
        """
        Devuelve el conteo total de todos los documentos en la colección concerts.
        Ideal para estadísticas generales y storytelling.
        """
        # count_documents es más eficiente que un aggregate completo para este propósito
        total = await self.db.concerts.count_documents({})
        return total
    
    async def get_most_played_song(self) -> dict:
        pipeline = [
            {"$match": {"track_ids": {"$exists": True, "$not": {"$size": 0}}}},
            {"$unwind": "$track_ids"},
            {"$group": {
                "_id": "$track_ids",
                "count": {"$sum": 1}
            }},
            # 1. Traemos la información del track ANTES del sort
            {"$lookup": {
                "from": "tracks",
                "localField": "_id",
                "foreignField": "id",
                "as": "track_data"
            }},
            {"$unwind": "$track_data"},
            
            # 2. ORDENAMIENTO DETERMINISTA
            # Si el count es igual, el orden alfabético del nombre decidirá.
            # Esto garantiza que siempre salga la misma canción en cada ejecución.
            {"$sort": {
                "count": -1, 
                "track_data.title": 1  # Segundo criterio: Alfabético A-Z
            }},
            
            {"$limit": 1},
            {"$project": {
                "_id": 0,
                "id": "$_id",
                "name": "$track_data.title"
            }}
        ]

        result = await self.db.concert_songs.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {"id": 0, "name": "N/A"}
    
    async def get_top_20_most_played_songs(self) -> List[dict]:
        pipeline = [
            # 1. Agrupar y contar
            {"$match": {"track_ids": {"$exists": True, "$not": {"$size": 0}}}},
            {"$unwind": "$track_ids"},
            {"$group": {
                "_id": "$track_ids",
                "play_count": {"$sum": 1} # Este es el contador
            }},

            # 2. Join con Tracks para obtener info básica
            {"$lookup": {
                "from": "tracks",
                "localField": "_id",
                "foreignField": "id",
                "as": "track"
            }},
            {"$unwind": "$track"},

            # 3. Orden Determinista (Primero por conteo, luego alfabético)
            {"$sort": {
                "play_count": -1,
                "track.title": 1
            }},
            {"$limit": 20},

            # 4. Joins de Enriquecimiento (Solo para los 20 finalistas)
            {"$lookup": {
                "from": "albums",
                "localField": "track.album_id",
                "foreignField": "id",
                "as": "album"
            }},
            {"$unwind": {"path": "$album", "preserveNullAndEmptyArrays": True}},

            # Joins para obtener nombres de IDs (Músicos, Géneros, etc.)
            {"$lookup": {"from": "genres", "localField": "track.genre_ids", "foreignField": "id", "as": "genre_docs"}},
            {"$lookup": {"from": "musicians", "localField": "track.composer_ids", "foreignField": "id", "as": "composer_docs"}},
            {"$lookup": {"from": "musicians", "localField": "track.guest_artist_ids", "foreignField": "id", "as": "guest_docs"}},

            # 5. Proyección Final
            {"$project": {
                "_id": 0,
                "play_count": 1,  # Incluimos el conteo solicitado
                "track_number": "$track.track_number",
                "title": "$track.title",
                "duration": "$track.duration",
                "duration_seconds": "$track.duration_seconds",
                "metadata": "$track.metadata",
                "genres": "$genre_docs.name",
                "composers": "$composer_docs.name",
                "guestArtists": "$guest_docs.name",
                # Album fields
                "album_id": "$album.id",
                "album_title": "$album.title",
                "album_release_year": "$album.release_year",
                "album_release_date": "$album.release_date",
                "album_cover": "$album.cover"
            }}
        ]

        cursor = self.db.concert_songs.aggregate(pipeline)
        return await cursor.to_list(length=20)