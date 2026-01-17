from fastapi import APIRouter, Depends
from app.database import get_db
from app.repositories.composer_repository import ComposerRepository
from app.services.composer_service import ComposerService
from app.models.music import ComposerResponse
from typing import List

router = APIRouter()

# Inyección de la dependencia del servicio
def get_composer_service(db=Depends(get_db)):
    repo = ComposerRepository(db)
    return ComposerService(repo)

@router.get("/", response_model=List[ComposerResponse])
async def get_composers(
    service: ComposerService = Depends(get_composer_service)
):
    return await service.fetch_all_composers()