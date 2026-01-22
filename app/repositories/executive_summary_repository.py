from app.database import get_db
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio

class ExecutiveSummaryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_executive_summary(self, target_musician_id: int = 1) -> dict:
        """
        Método Orquestador: Ejecuta todas las consultas en paralelo.
        """
        # Disparamos todas las tareas al mismo tiempo
        tasks = [
            self._get_general_track_stats(target_musician_id),
            self._get_duration_extremes(),
            self._get_album_insights(),
            self._get_top_lead_singer(),
            self.db.albums.count_documents({}),
            self._get_most_instrumental_album()
        ]
        
        # gather espera a que todas terminen y devuelve los resultados en orden
        (
            general_stats, 
            duration_stats, 
            album_insights, 
            top_singer, 
            total_albums,
            most_instrumental_album
        ) = await asyncio.gather(*tasks)

        # Unimos todas las piezas en el resumen final
        return {
            "total_albums": total_albums,
            **general_stats,
            **duration_stats,
            **album_insights,
            **top_singer,
            "most_instrumental_album": most_instrumental_album
        }

    # --- Métodos Privados de Apoyo ---

    async def _get_general_track_stats(self, musician_id: int) -> dict:
        pipeline = [
            {
                "$facet": {
                    "general": [
                        {
                            "$group": {
                                "_id": None,
                                "total_tracks": {"$sum": 1},
                                "studio_instrumental": {
                                    "$sum": {
                                        "$cond": [
                                            {"$and": [
                                                {"$eq": ["$metadata.is_live", False]},
                                                {"$eq": ["$metadata.is_instrumental", True]}
                                            ]}, 1, 0
                                        ]
                                    }
                                },
                                # Total de canciones de estudio para el denominador
                                "total_studio": {
                                    "$sum": {"$cond": [{"$eq": ["$metadata.is_live", False]}, 1, 0]}
                                },
                                "love_songs": {"$sum": {"$cond": ["$metadata.is_love_song", 1, 0]}},
                                "minor_keys": {
                                    "$sum": {
                                        "$cond": [
                                            {"$regexMatch": {"input": "$metadata.key", "regex": "m$"}}, 
                                            1, 0
                                        ]
                                    }
                                },
                                "target_musician_songs": {
                                    "$sum": {"$cond": [{"$in": [musician_id, "$lead_vocal_ids"]}, 1, 0]}
                                }
                            }
                        }
                    ],
                    "most_used_key": [
                        {"$group": {"_id": "$metadata.key", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 1}
                    ]
                }
            },
            {
                "$project": {
                    "total_tracks": {"$arrayElemAt": ["$general.total_tracks", 0]},
                    "total_studio_instrumental": {"$arrayElemAt": ["$general.studio_instrumental", 0]},
                    "total_studio_tracks": {"$arrayElemAt": ["$general.total_studio", 0]},
                    "total_songs_by_musician": {"$arrayElemAt": ["$general.target_musician_songs", 0]},
                    "percentage_keys_minor": {
                        "$cond": [
                            {"$gt": [{"$arrayElemAt": ["$general.total_tracks", 0]}, 0]},
                            {"$multiply": [
                                {"$divide": [{"$arrayElemAt": ["$general.minor_keys", 0]}, {"$arrayElemAt": ["$general.total_tracks", 0]}]},
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
        pipeline = [
            # 1. Agrupamos tracks por album_id para sumar su duración total
            {
                "$group": {
                    "_id": "$album_id",
                    "total_duration_seconds": {"$sum": "$duration_seconds"}
                }
            },
            # 2. Unimos con la colección 'albums' para obtener el título e is_live
            {
                "$lookup": {
                    "from": "albums",
                    "localField": "_id",
                    "foreignField": "id",
                    "as": "info"
                }
            },
            {"$unwind": "$info"},
            
            # 3. Filtramos: Solo álbumes de estudio (is_live: false)
            {
                "$match": {
                    "info.is_live": False
                }
            },
            
            # 4. Bifurcamos con $facet para obtener el más largo y el más corto
            {
                "$facet": {
                    "longest": [
                        {"$sort": {"total_duration_seconds": -1}},
                        {"$limit": 1},
                        {"$project": {"title": "$info.title"}}
                    ],
                    "shortest": [
                        {"$sort": {"total_duration_seconds": 1}},
                        {"$limit": 1},
                        {"$project": {"title": "$info.title"}}
                    ]
                }
            },
            
            # 5. Proyectamos para devolver un diccionario plano
            {
                "$project": {
                    "longest_studio_album": {"$arrayElemAt": ["$longest.title", 0]},
                    "shortest_studio_album": {"$arrayElemAt": ["$shortest.title", 0]}
                }
            }
        ]
        
        cursor = self.db.tracks.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        # Manejo de valores por defecto si no hay álbumes de estudio
        if result and result[0]:
            data = result[0]
            return {
                "longest_studio_album": data.get("longest_studio_album", "N/A"),
                "shortest_studio_album": data.get("shortest_studio_album", "N/A")
            }
        
        return {"longest_studio_album": "N/A", "shortest_studio_album": "N/A"}

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
            {"$unwind": "$m"},
            {"$project": {
                "_id": 0,
                "top1_albums_singer": {"$concat": ["$m.first_name", " ", "$m.last_name"]}
            }}
        ]
        cursor = self.db.tracks.aggregate(pipeline)
        result = await cursor.to_list(length=1)
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