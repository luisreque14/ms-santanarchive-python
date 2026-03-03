from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio

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
            self._get_total_non_album_songs(),
            self._get_total_studio_tracks_never_played()
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
            total_studio_tracks_never_played
        ) = await asyncio.gather(*tasks)

        # Unimos todas las piezas en el resumen final
        return {
            "total_concerts": total_concerts,
            "most_played_song": most_played_song_data.get("name") if most_played_song_data else "N/A",
            "most_played_album": most_played_album_data.get("title") if most_played_album_data else "N/A",
            "top_concert_year": top_year_data.get("year", 0) if top_year_data else 0,
            "top_country": top_country_data.get("country_name") if top_country_data else "N/A",
            "song_opener": song_opener_data.get("song_name") if song_opener_data else "N/A",
            "total_non_album_songs": total_non_album_songs,
            "total_studio_tracks_never_played": total_studio_tracks_never_played
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
    
    async def _get_total_studio_tracks_never_played(self) -> int:
        """
        Cuenta los tracks de estudio (is_live=False) que 
        no tienen ninguna ejecución registrada en vivo.
        """
        pipeline = [
            # 1. Filtramos solo tracks que NO son grabaciones en vivo
            {"$match": {"metadata.is_live": False}},
            
            # 2. Buscamos si el ID de este track aparece en algún concierto
            {"$lookup": {
                "from": "concert_songs",
                "localField": "id",
                "foreignField": "track_ids",
                "as": "concert_appearances"
            }},
            
            # 3. Filtramos los que tienen el array de conciertos vacío
            {"$match": {
                "concert_appearances": {"$size": 0}
            }},
            
            # 4. Contamos el resultado
            {"$count": "total_unplayed"}
        ]

        result = await self.db.tracks.aggregate(pipeline).to_list(length=1)
        return result[0]["total_unplayed"] if result else 0