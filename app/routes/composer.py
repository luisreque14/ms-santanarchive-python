from fastapi import APIRouter
from app.database import get_db
from app.models.music import ComposerResponse
from typing import List

router = APIRouter()

@router.get("/", response_model=List[ComposerResponse])
async def get_composers():
    db = get_db()
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
    return await db.composers.aggregate(pipeline).to_list(length=None)