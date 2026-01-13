from fastapi import APIRouter, HTTPException
from app.services.statistics_service import get_executive_summary_logic
from app.models.statistics.executive_summary import ExecutiveSummaryResponse

router = APIRouter()


@router.get("/executive-summary", response_model=ExecutiveSummaryResponse)
async def get_executive_summary():
    summary = await get_executive_summary_logic()

    if not summary:
        raise HTTPException(
            status_code=404,
            detail="No hay datos suficientes para generar el resumen"
        )

    return summary