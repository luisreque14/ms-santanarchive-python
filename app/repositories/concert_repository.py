from typing import Optional, List
from datetime import datetime, time, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

class ConcertRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
    async def get_by_filter(
        self, 
        start_date: datetime, 
        end_date: datetime,
        page: int = 1,
        page_size: int = 50,
        concert_type_id: Optional[int] = None,
        venue_type_id: Optional[int] = None,
        tour_id: Optional[int] = None,
        city_id: Optional[int] = None,
        state_id: Optional[int] = None,
        country_id: Optional[int] = None,
        continent_id: Optional[int] = None
    ) -> dict: # Cambiamos a dict para incluir metadatos
        
        # 1. Validación de rango (máximo 1 año)
        if end_date - start_date > timedelta(days=366):
            raise ValueError("The date range cannot exceed 1 year.")

        # 2. Ajuste de fechas
        query_start = datetime.combine(start_date.date(), time.min)
        query_end = datetime.combine(end_date.date(), time.max)

        # 3. Construcción del Match Query dinámico
        match_query = {"concert_date": {"$gte": query_start, "$lte": query_end}}
        if concert_type_id: match_query["concert_type_id"] = concert_type_id
        if venue_type_id: match_query["venue_type_id"] = venue_type_id
        if tour_id: match_query["tour_id"] = tour_id
        if city_id: match_query["city_id"] = city_id
        if state_id: match_query["state_id"] = state_id
        if country_id: match_query["country_id"] = country_id
        if continent_id: match_query["continent_id"] = continent_id

        # Cálculo de skip
        skip = (max(1, page) - 1) * page_size

        pipeline = [
            {"$match": match_query},
            {
                "$facet": {
                    # Rama 1: Metadatos (Conteo total)
                    "metadata": [{"$count": "total"}],
                    # Rama 2: Datos paginados y joins
                    "data": [
                        {"$sort": {"concert_date": -1}},
                        {"$skip": skip},
                        {"$limit": page_size},
                        # --- Aquí van todos tus $lookup anteriores ---
                        {"$lookup": {"from": "venue_types", "localField": "venue_type_id", "foreignField": "venue_type_id", "as": "v_type"}},
                        {"$unwind": {"path": "$v_type", "preserveNullAndEmptyArrays": True}},
                        {"$lookup": {"from": "show_types", "localField": "show_type_id", "foreignField": "show_type_id", "as": "s_type"}},
                        {"$unwind": {"path": "$s_type", "preserveNullAndEmptyArrays": True}},
                        {"$lookup": {"from": "concert_types", "localField": "concert_type_id", "foreignField": "concert_type_id", "as": "c_type"}},
                        {"$unwind": {"path": "$c_type", "preserveNullAndEmptyArrays": True}},
                        {"$lookup": {"from": "tours", "localField": "tour_id", "foreignField": "tour_id", "as": "tour"}},
                        {"$unwind": {"path": "$tour", "preserveNullAndEmptyArrays": True}},
                        {"$lookup": {"from": "cities", "localField": "city_id", "foreignField": "id", "as": "city"}},
                        {"$unwind": {"path": "$city", "preserveNullAndEmptyArrays": True}},
                        {"$lookup": {"from": "states", "localField": "state_id", "foreignField": "id", "as": "state"}},
                        {"$unwind": {"path": "$state", "preserveNullAndEmptyArrays": True}},
                        {"$lookup": {"from": "countries", "localField": "country_id", "foreignField": "id", "as": "country"}},
                        {"$unwind": {"path": "$country", "preserveNullAndEmptyArrays": True}},
                        {"$lookup": {"from": "continents", "localField": "continent_id", "foreignField": "id", "as": "continent"}},
                        {"$unwind": {"path": "$continent", "preserveNullAndEmptyArrays": True}},
                        # Proyección final
                        {"$project": {
                            "_id": 0,
                            "concert_date": 1,
                            "venue_name": 1,
                            "venue_type_id": 1,
                            "venue_type_name": "$v_type.venue_type_name",
                            "show_type_id": 1,
                            "show_type_name": "$s_type.show_type_name",
                            "show_time": 1,
                            "concert_type_id": 1,
                            "concert_type_name": "$c_type.concert_type_name",
                            "tour_id": 1,
                            "tour_name": "$tour.tour_name",
                            "city_id": 1,
                            "city_name": "$city.name",
                            "state_id": 1,
                            "state_name": "$state.name",
                            "country_id": 1,
                            "country_name": "$country.name",
                            "continent_id": 1,
                            "continent_name": "$continent.name",
                            "concert_year": 1,
                            "song_count": 1
                        }}
                    ]
                }
            },
            # Limpieza de la salida del facet
            {
                "$project": {
                    "total": {"$arrayElemAt": ["$metadata.total", 0]},
                    "results": "$data"
                }
            }
        ]

        result = await self.db.concerts.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {"total": 0, "results": [], "page": page, "pageSize": page_size}

        response = result[0]
        response["total"] = response.get("total", 0)
        response["page"] = page
        response["pageSize"] = page_size
        
        return response