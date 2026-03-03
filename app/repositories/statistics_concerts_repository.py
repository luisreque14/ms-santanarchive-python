from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.dtos.statistics.concerts.executive_summary_dto import ConcertExecutiveSummaryDto

class StatisticsConcertsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
    
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
    
    
    async def get_top_10_most_played_studio_albums(self) -> List[dict]:
        pipeline = [
            # 1. Obtener IDs únicos de canciones que han sonado en vivo
            {"$match": {"track_ids": {"$exists": True, "$not": {"$size": 0}}}},
            {"$unwind": "$track_ids"},
            {"$group": {"_id": "$track_ids"}}, # Esto elimina duplicados de interpretaciones

            # 2. Relacionar esas canciones únicas con sus álbumes
            {"$lookup": {
                "from": "tracks",
                "localField": "_id",
                "foreignField": "id",
                "as": "t"
            }},
            {"$unwind": "$t"},

            # 3. Contar cuántas canciones ÚNICAS tiene cada álbum en vivo
            {"$group": {
                "_id": "$t.album_id",
                "played_songs_count": {"$sum": 1} # Ahora suma 1 por cada track_id distinto
            }},

            # 4. Traer metadata del álbum
            {"$lookup": {
                "from": "albums",
                "localField": "_id",
                "foreignField": "id",
                "as": "album_info"
            }},
            {"$unwind": "$album_info"},

            # 5. FILTRO: Solo álbumes de estudio
            {"$match": {"album_info.is_live": False}},

            # 6. Ordenar por los que tienen más canciones distintas tocadas
            {"$sort": {"played_songs_count": -1}},
            {"$limit": 10},

            # 7. Traer todos los tracks del álbum para el conteo total y duración
            {"$lookup": {
                "from": "tracks",
                "localField": "_id",
                "foreignField": "album_id",
                "as": "album_tracks"
            }},

            # 8. Proyección final
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
    
    
    async def get_concerts_stats_by_year(self) -> List[dict]:
        pipeline = [
            # 1. Agrupar conciertos por el campo concert_year directamente
            {"$group": {
                "_id": "$concert_year",
                "total_concerts": {"$sum": 1},
                # Guardamos los IDs de los conciertos de este año para el siguiente paso
                "concert_ids_in_year": {"$push": "$id"}
            }},

            # 2. Join con concert_songs para obtener las canciones de todos esos conciertos
            {"$lookup": {
                "from": "concert_songs",
                "localField": "concert_ids_in_year",
                "foreignField": "concert_id",
                "as": "year_songs"
            }},

            # 3. Procesar canciones únicas
            {"$project": {
                "year": "$_id",
                "total_concerts": 1,
                # Obtenemos los nombres de canciones únicos para este año
                "different_songs_count": {
                    "$size": {
                        "$setUnion": {
                            "$filter": {
                                "input": "$year_songs.song_name",
                                "as": "sn",
                                "cond": { "$ne": ["$$sn", None] }
                            }
                        }
                    }
                }
            }},

            # 4. Ordenar cronológicamente descendente
            {"$sort": {"year": -1}}
        ]

        cursor = self.db.concerts.aggregate(pipeline)
        return await cursor.to_list(length=None)
    
    
    async def get_concert_counts_by_country(self) -> List[dict]:
        """
        Obtiene un listado de todos los países con su respectiva 
        cantidad de conciertos realizados.
        """
        pipeline = [
            # 1. Agrupar conciertos por country_id
            {"$group": {
                "_id": "$country_id",
                "count": {"$sum": 1}
            }},

            # 2. Relacionar con la colección de países para obtener el nombre
            {"$lookup": {
                "from": "countries",
                "localField": "_id",
                "foreignField": "id",
                "as": "country_info"
            }},

            # 3. Aplanar el array resultante del lookup
            {"$unwind": "$country_info"},

            # 4. Proyectar campos limpios para el DTO
            {"$project": {
                "_id": 0,
                "country_id": "$_id",
                "country_name": "$country_info.name",
                "concert_count": "$count"
            }},

            # 5. Ordenar por cantidad de conciertos (desc) y luego alfabéticamente
            {"$sort": {
                "concert_count": -1,
                "country_name": 1
            }}
        ]

        cursor = self.db.concerts.aggregate(pipeline)
        return await cursor.to_list(length=None)
    
    
    async def get_top_20_concert_opener_tracks(self) -> List[dict]:
        pipeline = [
            {"$match": {"song_number": 1}},
            {"$group": {
                "_id": "$song_name",
                "opening_count": {"$sum": 1}, 
                "track_id": {"$first": {"$arrayElemAt": ["$track_ids", 0]}}
            }},
            {"$sort": {"opening_count": -1}},
            {"$limit": 20},
            
            # Buscamos el total de ejecuciones (en cualquier posición) para esta canción
            {"$lookup": {
                "from": "concert_songs",
                "localField": "_id",
                "foreignField": "song_name",
                "as": "all_performances"
            }},
            
            # Joins de metadata (Tracks, Genres, Composers, Albums)
            {"$lookup": {
                "from": "tracks",
                "localField": "track_id",
                "foreignField": "id",
                "as": "track_info"
            }},
            {"$unwind": {"path": "$track_info", "preserveNullAndEmptyArrays": True}},
            
            {"$lookup": {
                "from": "genres",
                "localField": "track_info.genre_ids",
                "foreignField": "id",
                "as": "genres_data"
            }},
            {"$lookup": {
                "from": "composers",
                "localField": "track_info.composer_ids",
                "foreignField": "id",
                "as": "composers_data"
            }},
            {"$lookup": {
                "from": "albums",
                "localField": "track_info.album_id",
                "foreignField": "id",
                "as": "album_info"
            }},
            {"$unwind": {"path": "$album_info", "preserveNullAndEmptyArrays": True}},

            {"$project": {
                "_id": 0,
                "play_count": "$opening_count", 
                "title": {"$ifNull": ["$track_info.title", "$_id"]},
                "track_number": {"$ifNull": ["$track_info.track_number", 0]},
                "duration": {"$ifNull": ["$track_info.duration", "00:00:00"]},
                "duration_seconds": {"$ifNull": ["$track_info.duration_seconds", 0]},
                "genres": {"$ifNull": ["$genres_data.name", []]}, 
                "composers": {"$ifNull": ["$composers_data.name", []]},
                "metadata": {"$ifNull": ["$track_info.metadata", {
                    "key": "N/A", "is_instrumental": False, "is_live": True, "is_love_song": False
                }]},
                "guest_artists": {"$ifNull": ["$track_info.guest_artist_ids", []]},
                "album_id": {"$ifNull": ["$album_info.id", 0]},
                "album_title": {"$ifNull": ["$album_info.title", "Non-Album Track"]},
                "album_release_year": {"$ifNull": ["$album_info.release_year", 0]},
                "album_release_date": {"$ifNull": ["$album_info.release_date", datetime(1900, 1, 1)]},
                "album_cover": {"$ifNull": ["$album_info.cover", None]}
            }}
        ]

        cursor = self.db.concert_songs.aggregate(pipeline)
        return await cursor.to_list(length=20)
    
    async def get_non_album_songs(self) -> List[dict]:
        """
        Obtiene el listado de canciones que se han tocado en vivo 
        pero no existen en la colección de tracks/álbumes.
        """
        pipeline = [
            # 1. Agrupar por nombre de canción para evitar duplicados
            {"$group": {
                "_id": "$song_name",
                "track_id": {"$first": {"$arrayElemAt": ["$track_ids", 0]}},
                "total_plays": {"$sum": 1}
            }},

            # 2. Intentar cruzar con la tabla de tracks de estudio
            {"$lookup": {
                "from": "tracks",
                "localField": "track_id",
                "foreignField": "id",
                "as": "studio_record"
            }},

            # 3. Filtrar: Solo nos quedamos con las que NO tienen registro en studio_record
            {"$match": {
                "studio_record": {"$size": 0}
            }},

            # 4. Ordenar por las más populares en vivo
            {"$sort": {"total_plays": -1}},

            # 5. Proyectar un resultado limpio que encaje con tus DTOs básicos
            {"$project": {
                "_id": 0,
                "title": "$_id",
                "play_count": "$total_plays",
            }}
        ]

        cursor = self.db.concert_songs.aggregate(pipeline)
        return await cursor.to_list(length=None)