from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Any

class ConcertExecutiveSummaryDto(BaseModel):
    total_concerts: int = Field(0, validation_alias="total_concerts", exclude=False)