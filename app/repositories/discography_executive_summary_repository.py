from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio

class DiscographyExecutiveSummaryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_executive_summary(self) -> dict:
        _CARLOS_MUSICIAN_ID = 1
        _CARLOS_COMPOSER_ID = 11
        
        """
        Método Orquestador: Ejecuta todas las consultas en paralelo.
        """
        
        # Disparamos todas las tareas al mismo tiempo
        tasks = [
            self._get_general_track_stats(_CARLOS_MUSICIAN_ID),
            self._get_duration_extremes(),
            self._get_album_insights(),
            self._get_top_lead_singer(),
            self.db.albums.count_documents({}),
            self._get_most_instrumental_album(),
            self.get_count_albums_without_instrumentals(),
            self.get_total_guest_artists(),
            self.get_total_live_tracks_in_studio_albums(),
            self.get_total_by_composer(_CARLOS_COMPOSER_ID)
        ]
        
        # gather espera a que todas terminen y devuelve los resultados en orden
        (
            general_stats, 
            duration_stats, 
            album_insights, 
            top_singer, 
            total_albums,
            most_instrumental_album,
            count_albums_without_instrumentals,
            total_guest_artists,
            total_live_tracks_in_studio_albums,
            total_tracks_carlos_composer
        ) = await asyncio.gather(*tasks)

        # Unimos todas las piezas en el resumen final
        return {
            "total_albums": total_albums,
            **general_stats,
            **duration_stats,
            **album_insights,
            **top_singer,
            "most_instrumental_album": most_instrumental_album,
            "count_albums_without_instrumentals": count_albums_without_instrumentals,
            "total_guest_artists": total_guest_artists,
            "total_live_tracks_in_studio_albums":total_live_tracks_in_studio_albums,
            "total_tracks_carlos_composer":total_tracks_carlos_composer
        }

    # --- Métodos Privados de Apoyo ---

    async def _get_general_track_stats(self, musician_id: int) -> dict:
        pipeline = [
            {
                "$facet": {
                    "stats": [
                        {
                            "$group": {
                                "_id": None,
                                "total_tracks": {"$sum": 1},
                                "total_studio_tracks": {"$sum": {"$cond": [{"$eq": ["$metadata.is_live", False]}, 1, 0]}},
                                "total_studio_instrumental": {
                                    "$sum": {"$cond": [{"$and": [
                                        {"$eq": ["$metadata.is_live", False]},
                                        {"$eq": ["$metadata.is_instrumental", True]}
                                    ]}, 1, 0]}
                                },
                                "minor_keys_count": {
                                    "$sum": {"$cond": [{"$regexMatch": {"input": "$metadata.key", "regex": "m$"}}, 1, 0]}
                                },
                                "songs_by_musician": {"$sum": {"$cond": [{"$in": [musician_id, "$lead_vocal_ids"]}, 1, 0]}}
                            }
                        }
                    ],
                    "most_used_key": [
                        {"$match": {"metadata.key": {"$ne": None}}},
                        {"$group": {"_id": "$metadata.key", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 1}
                    ]
                }
            },
            {
                "$project": {
                    "total_tracks": {"$arrayElemAt": ["$stats.total_tracks", 0]},
                    "total_studio_tracks": {"$arrayElemAt": ["$stats.total_studio_tracks", 0]},
                    "total_studio_instrumental": {"$arrayElemAt": ["$stats.total_studio_instrumental", 0]},
                    "total_songs_by_musician": {"$arrayElemAt": ["$stats.songs_by_musician", 0]},
                    "percentage_keys_minor": {
                        "$cond": [
                            {"$gt": [{"$arrayElemAt": ["$stats.total_tracks", 0]}, 0]},
                            {"$multiply": [
                                {"$divide": [{"$arrayElemAt": ["$stats.minor_keys_count", 0]}, {"$arrayElemAt": ["$stats.total_tracks", 0]}]},
                                100
                            ]},
                            0
                        ]
                    },
                    "most_used_key": {"$ifNull": [{"$arrayElemAt": ["$most_used_key._id", 0]}, "N/A"]}
                }
            }
        ]
        cursor = self.db.tracks.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0] if result else {}

    async def _get_duration_extremes(self) -> dict:
        """Obtiene el track EN VIVO más largo y más corto con sus títulos."""
        
        # Filtro para canciones en vivo
        live_filter = {
            "metadata.is_live": False, 
            "duration_seconds": {"$exists": True, "$ne": None}
        }
        
        projection = {"title": 1, "duration": 1, "duration_seconds": 1, "_id": 0}
        
        # Buscamos el más largo y el más corto por valor numérico
        long_cursor = self.db.tracks.find(live_filter, projection).sort("duration_seconds", -1).limit(1)
        short_cursor = self.db.tracks.find(live_filter, projection).sort("duration_seconds", 1).limit(1)
        
        long_res = await long_cursor.to_list(1)
        short_res = await short_cursor.to_list(1)
        
        return {
            "longest_studio_track_data": long_res[0] if long_res else None,
            "shortest_studio_track_data": short_res[0] if short_res else None
        }

    async def _get_album_insights(self) -> dict:
        # 1. Agrupar duraciones por ID de álbum (Operación rápida en memoria)
        pipeline_durations = [
            {"$group": {"_id": "$album_id", "total_duration": {"$sum": "$duration_seconds"}}},
            {"$sort": {"total_duration": -1}}
        ]
        album_stats = await self.db.tracks.aggregate(pipeline_durations).to_list(length=None)
        
        if not album_stats:
            return {"longest_studio_album": "N/A", "shortest_studio_album": "N/A"}

        # 2. Obtener lista de IDs de álbumes de estudio (is_live: False)
        studio_album_ids = await self.db.albums.distinct("id", {"is_live": False})
        
        # 3. Filtrar los stats para que solo queden los de estudio
        studio_stats = [s for s in album_stats if s["_id"] in studio_album_ids]
        
        if not studio_stats:
            return {"longest_studio_album": "N/A", "shortest_studio_album": "N/A"}

        # 4. Solo buscamos los nombres de los dos que nos interesan
        longest_id = studio_stats[0]["_id"]
        shortest_id = studio_stats[-1]["_id"]
        
        names = await self.db.albums.find(
            {"id": {"$in": [longest_id, shortest_id]}},
            {"id": 1, "title": 1}
        ).to_list(length=2)
        
        name_map = {a["id"]: a["title"] for a in names}
        
        return {
            "longest_studio_album": name_map.get(longest_id, "N/A"),
            "shortest_studio_album": name_map.get(shortest_id, "N/A")
        }

    async def _get_top_lead_singer(self) -> dict:
        pipeline = [
            {"$unwind": "$lead_vocal_ids"},
            {"$group": {"_id": "$lead_vocal_ids", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1},
            {"$lookup": {
                "from": "musicians",
                "localField": "_id",
                "foreignField": "id",
                "as": "m"
            }},
            {"$project": {
                "_id": 0,
                "top1_albums_singer": {
                    "$let": {
                        "vars": {"first": {"$arrayElemAt": ["$m", 0]}},
                        "in": {"$concat": ["$$first.first_name", " ", "$$first.last_name"]}
                    }
                }
            }}
        ]
        result = await self.db.tracks.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {"top1_albums_singer": "N/A"}
    
    async def _get_most_instrumental_album(self) -> str:
        pipeline = [
            # 1. Filtrar solo tracks instrumentales
            {
                "$match": {
                    "metadata.is_instrumental": True
                }
            },
            # 2. Agrupar por álbum para contar canciones
            {"$group": {"_id": "$album_id", "count": {"$sum": 1}}},
            # 3. Join con ALBUMS aplicando el filtro is_live: False dentro del lookup
            {
                "$lookup": {
                    "from": "albums",
                    "let": {"album_id_from_track": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$id", "$$album_id_from_track"]},
                                        {"$eq": ["$is_live", False]}
                                    ]
                                }
                            }
                        },
                        {"$project": {"title": 1, "_id": 0}}
                    ],
                    "as": "album_info"
                }
            },
            # 4. Eliminar los que no encontraron un álbum de estudio (album_info vacío)
            {"$unwind": "$album_info"},
            # 5. Ordenar por la cuenta de tracks instrumentales
            {"$sort": {"count": -1}},
            # 6. Tomar el top 1
            {"$limit": 1},
            # 7. Proyectar solo el título
            {"$project": {"_id": 0, "title": "$album_info.title"}}
        ]
        
        cursor = self.db.tracks.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0]["title"] if result else "N/A"
    
    async def get_count_albums_without_instrumentals(self) -> int:
        pipeline = [
            # 1. Filtramos álbumes de estudio
            {
                "$match": {
                    "is_live": False
                }
            },
            # 2. Buscamos si tienen al menos una canción instrumental
            {
                "$lookup": {
                    "from": "tracks",
                    "let": {"album_id_val": "$id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$album_id", "$$album_id_val"]},
                                        {"$eq": ["$metadata.is_instrumental", True]}
                                    ]
                                }
                            }
                        },
                        {"$limit": 1} # Optimización: detenerse al encontrar la primera
                    ],
                    "as": "has_instrumental"
                }
            },
            # 3. Filtramos los que NO tuvieron coincidencias (array vacío)
            {
                "$match": {
                    "has_instrumental": {"$size": 0}
                }
            },
            # 4. Contamos el total de documentos resultantes
            {
                "$count": "total_count"
            }
        ]

        cursor = self.db.albums.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        # Retornamos solo el número entero
        return result[0]["total_count"] if result else 0
    
    async def get_total_guest_artists(self) -> int:
        # distinct() hace el trabajo de unwind y group automáticamente en el motor de C++ de Mongo
        guests = await self.db.tracks.distinct(
            "guest_artist_ids", 
            {"metadata.is_live": False, "guest_artist_ids": {"$exists": True, "$ne": []}}
        )
        return len(guests)

    async def get_total_live_tracks_in_studio_albums(self) -> int:
        # Obtenemos los IDs de álbumes de estudio
        studio_ids = await self.db.albums.distinct("id", {"is_live": False})
        
        # Contamos tracks en vivo que pertenecen a esos IDs
        return await self.db.tracks.count_documents({
            "metadata.is_live": True,
            "album_id": {"$in": studio_ids}
        })
    
    async def get_total_live_tracks_in_studio_albums(self) -> int:
        pipeline = [
            # 1. Filtramos tracks que tengan el atributo metadata.is_live en True
            {
                "$match": {
                    "metadata.is_live": True
                }
            },
            # 2. Unimos con la colección de albums para verificar el tipo de álbum
            {
                "$lookup": {
                    "from": "albums",
                    "localField": "album_id",
                    "foreignField": "id",
                    "as": "album_info"
                }
            },
            # 3. Descomponemos el array para filtrar por sus atributos
            {"$unwind": "$album_info"},
            # 4. Filtramos solo aquellos cuyo álbum NO sea en vivo (is_live: false)
            {
                "$match": {
                    "album_info.is_live": False
                }
            },
            # 5. Contamos el total de tracks que cumplen ambas condiciones
            {
                "$count": "total_count"
            }
        ]

        cursor = self.db.tracks.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        return result[0]["total_count"] if result else 0
    
    async def get_total_by_composer(self, composer_id):
        query = {"composer_ids": composer_id}
        return await self.db.tracks.count_documents(query)