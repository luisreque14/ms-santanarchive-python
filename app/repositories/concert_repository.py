from motor.motor_asyncio import AsyncIOMotorDatabase

class ConcertRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def find_city_by_id(self, city_id: int):
        return await self.db.cities.find_one({"id": city_id})

    async def find_concert_by_id(self, concert_id: int):
        return await self.db.concerts.find_one({"id": concert_id})

    async def find_musician_by_id(self, musician_id: int):
        return await self.db.musicians.find_one({"id": musician_id})

    async def create_concert(self, concert_data: dict):
        await self.db.concerts.insert_one(concert_data)
        return concert_data["id"]

    async def create_performance_credit(self, credit_data: dict):
        await self.db.performance_credits.insert_one(credit_data)
        return True

    async def get_concerts_by_year(self, search_year: str):
        pipeline = [
            {
                "$match": {
                    "$expr": {
                        "$eq": [{"$dateToString": {"format": "%Y", "date": "$date"}}, search_year]
                    }
                }
            },
            {
                "$lookup": {
                    "from": "cities",
                    "localField": "city_id",
                    "foreignField": "id", # Corregido de _id a id para consistencia
                    "as": "location"
                }
            },
            {"$unwind": "$location"},
            {
                "$project": {
                    "_id": 0,
                    "id": 1,
                    "date": 1,
                    "venue": 1,
                    "city": "$location.name",
                    "country": "$location.country",
                    "year": {"$dateToString": {"format": "%Y", "date": "$date"}}
                }
            }
        ]
        return await self.db.concerts.aggregate(pipeline).to_list(length=100)