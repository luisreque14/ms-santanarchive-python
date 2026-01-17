from typing import Optional

from app.database import get_db

class StatisticsService:

    async def get_instrumental_logic(album_id: Optional[int] = None):
        db = get_db()
        match_query = {"album_id": album_id} if album_id else {}

        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$album_id" if album_id else None,
                "total_instrumental": {"$sum": {"$cond": ["$metadata.is_instrumental", 1, 0]}},
                "total_vocal": {"$sum": {"$cond": ["$metadata.is_instrumental", 0, 1]}}
            }},
            {"$lookup": {"from": "albums", "localField": "_id", "foreignField": "id", "as": "info"}},
            {"$unwind": {"path": "$info", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "album_id": "$_id",
                "album_name": {
                    "$cond": [album_id is None, "Discografía Completa", {"$ifNull": ["$info.title", "Desconocido"]}]},
                "total_instrumental": 1, "total_vocal": 1, "_id": 0
            }}
        ]
        result = await db.tracks.aggregate(pipeline).to_list(1)
        return result[0] if result else None

    async def get_key_stats_logic(album_id: Optional[int] = None):
        db = get_db()
        match_query = {"album_id": album_id} if album_id else {}

        pipeline = [
            {"$match": match_query},
            {"$group": {"_id": {"aid": "$album_id", "k": "$metadata.key"}, "count": {"$sum": 1}}},
            {"$lookup": {"from": "albums", "localField": "_id.aid", "foreignField": "id", "as": "info"}},
            {"$unwind": {"path": "$info", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "album_id": "$_id.aid",
                "key": "$_id.k",
                "count": 1,
                "album_name": {"$cond": [album_id is None, "Discografía Completa", "$info.title"]},
                "_id": 0
            }},
            {"$sort": {"count": -1}}
        ]
        return await db.tracks.aggregate(pipeline).to_list(None)

    async def get_executive_summary_logic():
        db = get_db()
        if db is None:
            return None

        pipeline = [
            {
                "$facet": {
                    "general_stats": [
                        {
                            "$group": {
                                "_id": None,
                                "total": { "$sum": 1 },
                                "instrumentals": {
                                    "$sum": { "$cond": ["$metadata.is_instrumental", 1, 0] }
                                },
                                "love_songs": {
                                    "$sum": { "$cond": ["$metadata.is_love_song", 1, 0] }
                                }
                            }
                        }
                    ],
                    "most_used_key": [
                        { "$group": { "_id": "$metadata.key", "count": { "$sum": 1 } } },
                        { "$sort": { "count": -1 } },
                        { "$limit": 1 }
                    ]
                }
            },
            {
                "$project": {
                    "stats": { "$arrayElemAt": ["$general_stats", 0] },
                    "key_info": { "$arrayElemAt": ["$most_used_key", 0] }
                }
            },
            {
                "$project": {
                    "total_tracks": "$stats.total",
                    "instrumental_percentage": {
                        "$cond": [
                            { "$gt": ["$stats.total", 0] },
                            { "$multiply": [{ "$divide": ["$stats.instrumentals", "$stats.total"] }, 100] },
                            0
                        ]
                    },
                    "love_songs_percentage": {
                        "$cond": [
                            { "$gt": ["$stats.total", 0] },
                            { "$multiply": [{ "$divide": ["$stats.love_songs", "$stats.total"] }, 100] },
                            0
                        ]
                    },
                    "most_used_key": { "$ifNull": ["$key_info._id", "N/A"] }
                }
            }
        ]

        cursor = db.tracks.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0] if result and result[0].get("total_tracks") is not None else None

    async def get_love_song_stats_logic():
        db = get_db()

        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "love_songs": {
                        "$sum": {"$cond": ["$metadata.is_love_song", 1, 0]}
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_tracks": "$total",
                    "love_songs_count": "$love_songs",
                    "non_love_songs_count": {"$subtract": ["$total", "$love_songs"]},
                    "love_songs_percentage": {
                        "$cond": [
                            {"$gt": ["$total", 0]},
                            {"$multiply": [{"$divide": ["$love_songs", "$total"]}, 100]},
                            0
                        ]
                    },
                    "non_love_songs_percentage": {
                        "$cond": [
                            {"$gt": ["$total", 0]},
                            {"$multiply": [{"$divide": [{"$subtract": ["$total", "$love_songs"]}, "$total"]}, 100]},
                            0
                        ]
                    }
                }
            }
        ]

        cursor = db.tracks.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0] if result else None

    async def get_genre_stats_logic():
        db = get_db()

        pipeline = [
            # 1. Expandir los géneros
            {"$unwind": "$genre_ids"},

            # 2. Agrupar por género y crear una rama para el total global de etiquetas
            {
                "$facet": {
                    "counts_by_genre": [
                        {"$group": {"_id": "$genre_ids", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}}
                    ],
                    "total_occurrences": [
                        {"$count": "total"}
                    ]
                }
            },

            # 3. Procesar los resultados del facet
            {"$unwind": "$counts_by_genre"},
            {
                "$addFields": {
                    "total_sum": {"$arrayElemAt": ["$total_occurrences.total", 0]}
                }
            },

            # 4. Lookup para nombres de géneros
            {
                "$lookup": {
                    "from": "genres",
                    "localField": "counts_by_genre._id",
                    "foreignField": "id",
                    "as": "info"
                }
            },
            {"$unwind": "$info"},

            # 5. Proyecto final con porcentaje sobre el total de ETIQUETAS
            {
                "$project": {
                    "_id": 0,
                    "genre_id": "$counts_by_genre._id",
                    "genre_name": "$info.name",
                    "track_count": "$counts_by_genre.count",
                    "percentage": {
                        "$cond": [
                            {"$gt": ["$total_sum", 0]},
                            {"$multiply": [{"$divide": ["$counts_by_genre.count", "$total_sum"]}, 100]},
                            0
                        ]
                    }
                }
            },
            {"$sort": {"track_count": -1}}
        ]

        cursor = db.tracks.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_collab_report():
        db = get_db()

        pipeline = [
            # 1. Traer información del álbum para tener el año
            {
                "$lookup": {
                    "from": "albums",
                    "localField": "album_id",
                    "foreignField": "id",
                    "as": "album_info"
                }
            },
            {"$unwind": "$album_info"},

            # 2. Calcular la década y verificar si tiene colaboradores
            {
                "$addFields": {
                    "decade_start": {
                        "$subtract": [
                            "$album_info.release_year",
                            {"$mod": ["$album_info.release_year", 10]}
                        ]
                    },
                    "has_collaborators": {
                        "$cond": [
                            {"$and": [
                                    {"$isArray": "$collaborator_ids"},
                                {"$gt": [{"$size": "$collaborator_ids"}, 0]}
                            ]},
                            1, 0
                        ]
                    }
                }
            },

            # 3. Agrupar por década
            {
                "$group": {
                    "_id": "$decade_start",
                    "total_tracks": {"$sum": 1},
                    "collab_tracks": {"$sum": "$has_collaborators"},
                    "all_collaborator_ids": {"$push": "$collaborator_ids"}
                }
            },

            # 4. Aplanar la lista de IDs de invitados y eliminar duplicados
            {
                "$project": {
                    "period": {
                        "$concat": [
                            {"$toString": "$_id"},
                            "-",
                            {"$toString": {"$add": ["$_id", 9]}}
                        ]
                    },
                    "total_tracks": 1,
                    "collab_tracks": 1,
                    "collab_percentage": {
                        "$round": [
                            {"$multiply": [{"$divide": ["$collab_tracks", "$total_tracks"]}, 100]},
                            1
                        ]
                    },
                    # Convertimos la lista de listas [[1,2], [3]] en una lista plana [1,2,3]
                    "unique_collaborator_ids": {
                        "$reduce": {
                            "input": "$all_collaborator_ids",
                            "initialValue": [],
                            "in": {"$setUnion": ["$$value", "$$this"]}
                        }
                    }
                }
            },

            # 5. Buscar los nombres de los colaboradores únicos
            {
                "$lookup": {
                    "from": "collaborators",
                    "localField": "unique_collaborator_ids",
                    "foreignField": "id",
                    "as": "collaborators_data"
                }
            },

            # 6. Formateo final
            {
                "$project": {
                    "_id": 0,
                    "period": 1,
                    "total_tracks": 1,
                    "collab_tracks": 1,
                    "collab_percentage": 1,
                    "collaborators": "$collaborators_data.full_name"
                }
            },
            {"$sort": {"period": 1}}
        ]

        cursor = db.tracks.aggregate(pipeline)
        return await cursor.to_list(length=None)