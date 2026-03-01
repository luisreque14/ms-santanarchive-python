from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio

class ConcertsExecutiveSummaryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_executive_summary(self) -> dict:
        tasks = [
            self._get_total_concerts_count(),
            self._get_most_played_song(),
            self._get_most_played_album()
        ]
        
        # gather espera a que todas terminen y devuelve los resultados en orden
        (
            total_concerts,
            most_played_data,
            most_played_album_data
        ) = await asyncio.gather(*tasks)

        song_name = most_played_data.get("name") if most_played_data else "N/A"
        album_name = most_played_album_data.get("title") if most_played_album_data else "N/A"

        # Unimos todas las piezas en el resumen final
        return {
            "total_concerts": total_concerts,
            "most_played_song": song_name,
            "most_played_album": album_name
        }

    async def _get_total_concerts_count(self) -> int:
        """
        Devuelve el conteo total de todos los documentos en la colección concerts.
        Ideal para estadísticas generales y storytelling.
        """
        # count_documents es más eficiente que un aggregate completo para este propósito
        total = await self.db.concerts.count_documents({})
        return total
    
    async def _get_most_played_song(self) -> dict:
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
    
    async def _get_most_played_album(self) -> dict:
        """
        Obtiene el título del álbum cuyas canciones (sumadas) se han 
        interpretado más veces en todos los conciertos.
        """
        pipeline = [
            # 1. Filtrar ejecuciones con tracks vinculados
            {"$match": {"track_ids": {"$exists": True, "$not": {"$size": 0}}}},
            
            # 2. Descomponer los tracks vinculados
            {"$unwind": "$track_ids"},
            
            # 3. Join con 'tracks' para saber a qué álbum pertenece cada canción
            {"$lookup": {
                "from": "tracks",
                "localField": "track_ids",
                "foreignField": "id",
                "as": "track_info"
            }},
            {"$unwind": "$track_info"},
            
            # 4. Agrupar por el ID del álbum y contar ejecuciones totales
            {"$group": {
                "_id": "$track_info.album_id",
                "total_plays": {"$sum": 1}
            }},
            
            # 5. Join con 'albums' para obtener el título
            {"$lookup": {
                "from": "albums",
                "localField": "_id",
                "foreignField": "id",
                "as": "album_info"
            }},
            {"$unwind": "$album_info"},
            
            # 6. Ordenar por el álbum más escuchado y desempate por título
            {"$sort": {
                "total_plays": -1,
                "album_info.title": 1
            }},
            
            # 7. Tomar el ganador
            {"$limit": 1},
            
            # 8. Proyectar solo el título
            {"$project": {
                "_id": 0,
                "title": "$album_info.title"
            }}
        ]

        result = await self.db.concert_songs.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {"title": "N/A"}
    
    async def get_top_10_most_played_studio_albums(self) -> List[dict]:
        pipeline = [
            # 1. Agrupar ejecuciones de canciones por ID de álbum
            {"$match": {"track_ids": {"$exists": True, "$not": {"$size": 0}}}},
            {"$unwind": "$track_ids"},
            {"$lookup": {
                "from": "tracks",
                "localField": "track_ids",
                "foreignField": "id",
                "as": "t"
            }},
            {"$unwind": "$t"},
            {"$group": {
                "_id": "$t.album_id",
                "played_songs_count": {"$sum": 1}
            }},

            # 2. Join con Albums para obtener metadata
            {"$lookup": {
                "from": "albums",
                "localField": "_id",
                "foreignField": "id",
                "as": "album_info"
            }},
            {"$unwind": "$album_info"},

            # 3. FILTRO: Solo álbumes que NO sean en vivo
            # is_live: false significa que son álbumes de estudio
            {"$match": {"album_info.is_live": False}},

            # 4. Ordenar por popularidad y limitar a los 10 mejores
            {"$sort": {"played_songs_count": -1}},
            {"$limit": 10},

            # 5. Join con Tracks para obtener todas las canciones del álbum y su duración
            {"$lookup": {
                "from": "tracks",
                "localField": "_id",
                "foreignField": "album_id",
                "as": "album_tracks"
            }},

            # 6. Proyección final con suma de duración y conteo de tracks
            {"$project": {
                "_id": 0,
                "id": "$_id",
                "title": "$album_info.title",
                "release_year": "$album_info.release_year",
                "release_date": "$album_info.release_date",
                "cover": "$album_info.cover",
                "is_live": "$album_info.is_live",
                "played_songs_count": 1,
                "total_tracks_count": {"$size": "$album_tracks"},
                "duration": {
                    "$sum": "$album_tracks.duration_seconds"
                }
            }},
            
            {"$sort": {"played_songs_count": -1, "title": 1}}
        ]

        cursor = self.db.concert_songs.aggregate(pipeline)
        return await cursor.to_list(length=10)