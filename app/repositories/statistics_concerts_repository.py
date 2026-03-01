from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.dtos.statistics.concerts.executive_summary_dto import ConcertExecutiveSummaryDto

class StatisticsConcertsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        