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
            {"$group": {"_id": "$track_ids", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1}, # <--- Movemos el limit aquí arriba
            {"$lookup": {
                "from": "tracks",
                "localField": "_id",
                "foreignField": "id",
                "as": "track_data"
            }},
            {"$unwind": "$track_data"},
            {"$project": {
                "_id": 0,
                "id": "$_id",
                "name": "$track_data.title"
            }}
        ]
        result = await self.db.concert_songs.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {"id": 0, "name": "N/A"}
    
    async def _get_most_played_album(self) -> dict:
        pipeline = [
            # 1. Agrupar por track_ids (que son listas) de forma rápida
            {"$unwind": "$track_ids"},
            {"$group": {"_id": "$track_ids", "total_plays": {"$sum": 1}}},
            
            # 2. Join con tracks para saber su álbum
            {"$lookup": {
                "from": "tracks",
                "localField": "_id",
                "foreignField": "id",
                "as": "track_info"
            }},
            {"$unwind": "$track_info"},
            
            # 3. Re-agrupar por álbum_id
            {"$group": {
                "_id": "$track_info.album_id",
                "total_album_plays": {"$sum": "$total_plays"}
            }},
            
            # 4. Quedarnos solo con el ganador
            {"$sort": {"total_album_plays": -1}},
            {"$limit": 1},
            
            # 5. Buscar el nombre del álbum ganador
            {"$lookup": {
                "from": "albums",
                "localField": "_id",
                "foreignField": "id",
                "as": "album_info"
            }},
            {"$unwind": "$album_info"},
            {"$project": {"_id": 0, "title": "$album_info.title"}}
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
            {"$group": {"_id": "$country_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1},
            {"$lookup": {
                "from": "countries",
                "localField": "_id",
                "foreignField": "id",
                "as": "country_info"
            }},
            {"$unwind": "$country_info"},
            {"$project": {"_id": 0, "country_name": "$country_info.name"}}
        ]
        result = await self.db.concerts.aggregate(pipeline).to_list(length=1)
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
        # 1. Obtener IDs únicos de tracks vinculados a álbumes
        # (Suponiendo que un track vinculado a un álbum tiene un album_id)
        album_linked_track_ids = await self.db.tracks.distinct("id", {"album_id": {"$ne": None}})

        # 2. Encontrar canciones en conciertos cuyo track_id NO esté en esa lista
        # O canciones que no tengan track_ids en absoluto
        pipeline = [
            {"$group": {
                "_id": "$song_name",
                "track_id": {"$first": {"$arrayElemAt": ["$track_ids", 0]}}
            }},
            {"$match": {
                "$or": [
                    {"track_id": {"$nin": album_linked_track_ids}},
                    {"track_id": None}
                ]
            }},
            {"$count": "total"}
        ]
        result = await self.db.concert_songs.aggregate(pipeline).to_list(length=1)
        return result[0]["total"] if result else 0
    
    async def _get_total_studio_tracks_never_played(self) -> int:
        # 1. Obtener lista de IDs de tracks que SÍ se han tocado
        # Esto es rápido si track_ids está indexado
        played_track_ids = await self.db.concert_songs.distinct("track_ids")

        # 2. Contar tracks de estudio que no están en esa lista
        count = await self.db.tracks.count_documents({
            "metadata.is_live": False,
            "id": {"$nin": played_track_ids}
        })
        return count