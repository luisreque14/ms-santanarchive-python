from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

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
    
    async def get_most_played_studio_albums(self) -> List[dict]:
        # 1. Obtener solo los IDs de tracks que han sonado en vivo (Desde la colección de conciertos)
        played_track_ids = await self.db.concert_songs.distinct("track_ids")

        pipeline = [
            # 1. Filtro de Álbum: Solo álbumes que no sean 'Live'
            {"$match": {"is_live": False}},

            # 2. Traer tracks del álbum que TAMBIÉN sean de estudio (is_live: false)
            {"$lookup": {
                "from": "tracks",
                "let": {"album_id_val": "$id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$album_id", "$$album_id_val"]},
                                    {"$eq": ["$metadata.is_live", False]} # <--- Filtro de Track Estudio
                                ]
                            }
                        }
                    }
                ],
                "as": "studio_tracks"
            }},

            # 3. Identificar cuáles de esos tracks de estudio han sonado en vivo
            {"$addFields": {
                "played_studio_songs": {
                    "$filter": {
                        "input": "$studio_tracks",
                        "as": "st",
                        "cond": {"$in": ["$$st.id", played_track_ids]}
                    }
                }
            }},

            # 4. Cálculos de métricas basados estrictamente en material de estudio
            {"$addFields": {
                "played_songs_count": {"$size": "$played_studio_songs"},
                "total_tracks_count": {"$size": "$studio_tracks"},
                "played_percentage": {
                    "$cond": [
                        {"$gt": [{"$size": "$studio_tracks"}, 0]},
                        {"$multiply": [
                            {"$divide": [{"$size": "$played_studio_songs"}, {"$size": "$studio_tracks"}]},
                            100
                        ]},
                        0
                    ]
                }
            }},

            # 5. Ordenamiento: Prioridad Porcentaje -> Volumen -> Título
            {"$sort": {
                "played_percentage": -1, 
                "played_songs_count": -1, 
                "title": 1
            }},

            # 6. Proyección final con todas tus columnas
            {"$project": {
                "_id": 0,
                "id": 1,
                "title": 1,
                "release_year": 1,
                "release_date": 1,
                "cover": 1,
                "is_live": 1,
                "played_songs_count": 1, 
                "total_tracks_count": 1,
                "played_percentage": {"$round": ["$played_percentage", 2]},
                "duration": {"$sum": "$studio_tracks.duration_seconds"}
            }}
        ]

        cursor = self.db.albums.aggregate(pipeline)
        return await cursor.to_list(length=None)
    
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
    
    async def get_geographic_conquest_milestones(self) -> List[dict]:
        pipeline = [
            # 1. Agrupamos por país para encontrar el año de la primera visita
            {"$group": {
                "_id": "$country_id",
                "first_visit_year": {"$min": "$concert_year"},
                "total_concerts_in_country": {"$sum": 1}
            }},

            # 2. Traemos la información del País (Nombre y Código ISO)
            {"$lookup": {
                "from": "countries",
                "localField": "_id",
                "foreignField": "id",
                "as": "country_info"
            }},
            {"$unwind": "$country_info"},

            # 3. Traemos la información del Continente
            {"$lookup": {
                "from": "continents",
                "localField": "country_info.continent_id",
                "foreignField": "id",
                "as": "continent_info"
            }},
            {"$unwind": "$continent_info"},

            # 4. Ordenamos cronológicamente por el año de conquista
            {"$sort": {"first_visit_year": 1}},

            # 5. Proyectamos el resultado final para el DTO
            {"$project": {
                "_id": 0,
                "year": "$first_visit_year",
                "countryName": "$country_info.name",
                "countryCode": "$country_info.code", # Importante para el mapa
                "continentName": "$continent_info.name",
                "totalShowsToDate": "$total_concerts_in_country"
            }}
        ]

        cursor = self.db.concerts.aggregate(pipeline)
        return await cursor.to_list(length=None)
    
    async def get_tracks_with_play_count_by_album(self, album_id: int) -> List[dict]:
        pipeline = [
            # 1. Filtramos los tracks pertenecientes al álbum solicitado
            {"$match": {"album_id": album_id}},

            # 2. Contamos las apariciones directamente en concert_songs
            {"$lookup": {
                "from": "concert_songs",
                "localField": "id",
                "foreignField": "track_ids",
                "as": "performances"
            }},

            # 3. Proyección simplificada: solo datos del track y el conteo
            {"$project": {
                "_id": 0,
                "track_number": 1,
                "title": 1,
                "duration": 1,
                "duration_seconds": 1,
                "album_id": 1,
                "play_count": {"$size": "$performances"}
            }},

            # 4. Ordenar por número de track para mantener el orden del disco
            {"$sort": {"track_number": 1}}
        ]

        cursor = self.db.tracks.aggregate(pipeline)
        return await cursor.to_list(length=None)