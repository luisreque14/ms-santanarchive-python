from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio
from datetime import datetime

class ConcertsExecutiveSummaryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_executive_summary(self) -> dict:
        tasks = [
            self._get_total_concerts_count(),
            self._get_most_played_song(),
            self._get_most_played_album(),
            self._get_year_with_most_concerts(),
            self._get_top_country_with_most_concerts(),
            self._get_most_frequent_concert_opener_song(),
            self._get_total_non_album_songs()
        ]
        
        # gather espera a que todas terminen y devuelve los resultados en orden
        (
            total_concerts,
            most_played_song_data,
            most_played_album_data,
            top_year_data,
            top_country_data,
            song_opener_data,
            total_non_album_songs,
        ) = await asyncio.gather(*tasks)

        # Unimos todas las piezas en el resumen final
        return {
            "total_concerts": total_concerts,
            "most_played_song": most_played_song_data.get("name") if most_played_song_data else "N/A",
            "most_played_album": most_played_album_data.get("title") if most_played_album_data else "N/A",
            "top_concert_year": top_year_data.get("year", 0) if top_year_data else 0,
            "top_country": top_country_data.get("country_name") if top_country_data else "N/A",
            "song_opener": song_opener_data.get("song_name") if song_opener_data else "N/A",
            "total_non_album_songs": total_non_album_songs
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
    
    async def _get_year_with_most_concerts(self) -> dict:
        """
        Obtiene el año con mayor actividad usando el campo indexado concert_year.
        Incluye todos los tipos de eventos registrados.
        """
        pipeline = [
            # 1. Aseguramos que el año no sea nulo para evitar el grupo 'None'
            {"$match": {
                "concert_year": {"$ne": None}
            }},
            
            # 2. Agrupamos directamente por el campo pre-calculado
            {"$group": {
                "_id": "$concert_year", 
                "count": {"$sum": 1}
            }},
            
            # 3. Ordenamos: Mayor cantidad primero, desempate por el año más reciente
            {"$sort": {
                "count": -1,
                "_id": -1 
            }},
            
            # 4. Tomamos el ganador
            {"$limit": 1},
            
            # 5. Proyectamos el resultado final
            {"$project": {
                "_id": 0,
                "year": "$_id",
                "count": 1
            }}
        ]

        result = await self.db.concerts.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {"year": 0, "count": 0}
    
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
    
    async def _get_top_country_with_most_concerts(self) -> dict:
        pipeline = [
            # 1. Agrupar por ID de país
            {"$group": {
                "_id": "$country_id",
                "count": {"$sum": 1}
            }},
            
            # 2. Ordenar por volumen de conciertos
            {"$sort": {"count": -1}},
            
            # 3. Quedarnos solo con el ID del país más frecuente
            {"$limit": 1},
            
            # 4. Buscar el nombre en la colección 'countries'
            {"$lookup": {
                "from": "countries",
                "localField": "_id",
                "foreignField": "id",
                "as": "country_info"
            }},
            
            {"$unwind": "$country_info"},
            
            # 5. Proyectar ÚNICAMENTE el nombre para tu DTO
            {"$project": {
                "_id": 0,
                "country_name": "$country_info.name"
            }}
        ]

        result = await self.db.concerts.aggregate(pipeline).to_list(length=1)
        # Devolvemos el string directamente o un dict con la llave esperada
        return result[0] if result else {"country_name": "N/A"}
    
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
    
    async def _get_most_frequent_concert_opener_song(self) -> dict:
        """
        Obtiene el nombre de la canción que más veces ha abierto un concierto.
        """
        pipeline = [
            # 1. Filtramos solo la primera canción de cada setlist
            {"$match": {"song_number": 1}},
            
            # 2. Agrupamos por nombre y contamos apariciones
            {"$group": {
                "_id": "$song_name",
                "count": {"$sum": 1}
            }},
            
            # 3. Ordenamos por el que más veces aparece
            {"$sort": {"count": -1}},
            
            # 4. Tomamos solo el primero (el ganador)
            {"$limit": 1},
            
            # 5. Proyectamos solo el nombre para que el DTO sea limpio
            {"$project": {
                "_id": 0,
                "song_name": "$_id"
            }}
        ]

        result = await self.db.concert_songs.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {"song_name": "N/A"}
    
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
    
    async def _get_total_non_album_songs(self) -> int:
        """
        Cuenta cuántas canciones únicas existen en los conciertos 
        que no tienen una relación con la colección de tracks/albums.
        """
        pipeline = [
            # 1. Agrupamos por nombre de canción para tener canciones ÚNICAS
            {"$group": {
                "_id": "$song_name",
                "track_id": {"$first": {"$arrayElemAt": ["$track_ids", 0]}}
            }},
            
            # 2. Intentamos buscar la canción en la colección de tracks
            {"$lookup": {
                "from": "tracks",
                "localField": "track_id",
                "foreignField": "id",
                "as": "track_info"
            }},
            
            # 3. Filtramos: solo nos quedamos con las que NO tienen info en tracks
            # y que tampoco tienen un track_id válido (por si acaso)
            {"$match": {
                "$or": [
                    {"track_info": {"$size": 0}},
                    {"track_id": {"$exists": False}},
                    {"track_id": None}
                ]
            }},
            
            # 4. Contamos el resultado final
            {"$count": "total"}
        ]

        result = await self.db.concert_songs.aggregate(pipeline).to_list(length=1)
        return result[0]["total"] if result else 0
    
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