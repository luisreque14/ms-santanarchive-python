from motor.motor_asyncio import AsyncIOMotorDatabase

class ConcertMastersRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_concert_types(self):
        return await self.db.concert_types.find({}, {
            "_id": 0, 
            "id": "$concert_type_id", 
            "name": "$concert_type_name"
        }).sort("concert_type_name", 1).to_list(length=None)

    async def get_show_types(self):
        return await self.db.show_types.find({}, {
            "_id": 0, 
            "id": "$show_type_id", 
            "name": "$show_type_name"
        }).sort("show_type_name", 1).to_list(length=None)

    async def get_venue_types(self):
        return await self.db.venue_types.find({}, {
            "_id": 0, 
            "id": "$venue_type_id", 
            "name": "$venue_type_name"
        }).sort("venue_type_name", 1).to_list(length=None)

    async def get_tours(self):
        return await self.db.tours.find({}, {
            "_id": 0, 
            "id": "$tour_id", 
            "name": "$tour_name"
        }).sort("tour_name", 1).to_list(length=None)