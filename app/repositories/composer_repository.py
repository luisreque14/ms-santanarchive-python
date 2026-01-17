from motor.motor_asyncio import AsyncIOMotorDatabase

class ComposerRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_composers_with_country(self):
        pipeline = [
            {
                "$lookup": {
                    "from": "countries",
                    "localField": "country_id",
                    "foreignField": "id",
                    "as": "country_info"
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "id": 1,
                    "full_name": 1,
                    "country_name": { "$arrayElemAt": ["$country_info.name", 0] }
                }
            }
        ]
        return await self.db.composers.aggregate(pipeline).to_list(length=None)