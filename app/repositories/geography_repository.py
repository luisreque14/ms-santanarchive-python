from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.geography import ContinentSchema, CountrySchema, StateSchema, CitySchema

class GeographyRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # --- CONTINENTS ---
    async def get_all_continents(self):
        return await self.db.continents.find({}, {"_id": 0}).to_list(length=None)

    async def get_continent_by_id(self, continent_id: int):
        return await self.db.continents.find_one({"id": continent_id})

    async def create_continent(self, continent_data: dict):
        await self.db.continents.insert_one(continent_data)
        return continent_data["id"]

    # --- COUNTRIES ---
    async def get_countries(self, query: dict):
        return await self.db.countries.find(query, {"_id": 0}).to_list(length=None)

    async def get_country_by_id(self, country_id: int):
        return await self.db.countries.find_one({"id": country_id})

    async def create_country(self, country_data: dict):
        await self.db.countries.insert_one(country_data)
        return country_data["id"]

    # --- STATES & CITIES ---
    async def get_state_by_id(self, state_id: int):
        return await self.db.states.find_one({"id": state_id})

    async def create_state(self, state_data: dict):
        await self.db.states.insert_one(state_data)
        return state_data["id"]

    async def create_city(self, city_data: dict):
        await self.db.cities.insert_one(city_data)
        return city_data["id"]