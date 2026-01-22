from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

class MusicianRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # --- ROLES ---
    async def get_role_by_id(self, role_id: int):
        return await self.db.roles.find_one({"id": role_id})

    async def get_all_roles(self):
        return await self.db.roles.find({}, {"_id": 0}).to_list(length=100)

    async def create_role(self, role_data: dict):
        await self.db.roles.insert_one(role_data)
        return role_data["id"]

    # --- MUSICIANS ---
    async def get_all_musicians(self):
        return await self.db.musicians.find({}, {"_id": 0}).to_list(length=100)

    async def create_musician(self, musician_data: dict):
        await self.db.musicians.insert_one(musician_data)
        return True

    # --- VALIDATIONS ---
    async def check_roles_exist(self, role_ids: List[int]) -> bool:
        # Optimizamos: una sola consulta para verificar todos los roles
        count = await self.db.roles.count_documents({"id": {"$in": role_ids}})
        return count == len(role_ids)

    async def country_exists(self, country_id: int) -> bool:
        return await self.db.countries.find_one({"id": country_id}) is not None

    async def get_studio_lead_vocals(self) -> List[dict]:
        pipeline = [
            # 1. Join con COUNTRIES para obtener el nombre del país
            {
                "$lookup": {
                    "from": "countries",
                    "localField": "country_id",
                    "foreignField": "id",
                    "as": "country_info"
                }
            },
            {"$unwind": {"path": "$country_info", "preserveNullAndEmptyArrays": True}},

            # 2. Join con TRACKS filtrando por Lead Vocal Y que NO sea en vivo
            {
                "$lookup": {
                    "from": "tracks",
                    "let": {"musician_id": "$id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        # Filtro: El músico está en la lista de lead_vocal_ids
                                        { "$in": ["$$musician_id", "$lead_vocal_ids"] },
                                        # Filtro: La canción NO es en vivo
                                        { "$eq": ["$metadata.is_live", False] }
                                    ]
                                }
                            }
                        },
                        {"$count": "count"}
                    ],
                    "as": "track_count_res"
                }
            },

            # 3. Extraer el número del array de conteo
            {
                "$addFields": {
                    "number_of_tracks": {
                        "$ifNull": [{ "$arrayElemAt": ["$track_count_res.count", 0] }, 0]
                    }
                }
            },

            # --- NUEVA ETAPA: FILTRAR SOLO LOS QUE TIENEN TRACKS ---
            {
                "$match": {
                    "number_of_tracks": { "$gt": 0 }
                }
            },

            # 4. Proyectar campos finales
            {
                "$project": {
                    "_id": 0,
                    "id": 1,
                    "first_name": 1,
                    "last_name": 1,
                    "country_id": 1,
                    "country_name": { "$ifNull": ["$country_info.name", "Unknown"] },
                    "number_of_tracks": 1,
                    "active_from": 1,
                    "active_to": 1,
                    "roles": 1
                }
            },
            
            # 5. Ordenar por relevancia
            {"$sort": {"number_of_tracks": -1, "last_name": 1}}
        ]

        cursor = self.db.musicians.aggregate(pipeline)
        return await cursor.to_list(length=None)