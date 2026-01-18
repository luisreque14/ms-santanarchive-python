from fastapi import APIRouter, Depends
from app.services.composer_service import ComposerService
from app.models.music import ComposerResponse
from typing import List
from app.core.dependencies import get_composer_service

router = APIRouter()

@router.get("/", response_model=List[ComposerResponse])
async def get_composers(
    service: ComposerService = Depends(get_composer_service)
):
    return await service.fetch_all_composers()