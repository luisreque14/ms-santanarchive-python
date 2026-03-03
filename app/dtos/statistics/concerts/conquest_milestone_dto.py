from pydantic import BaseModel, Field, ConfigDict

class ConquestMilestoneDto(BaseModel):
    year: int = Field(..., description="The year of the first concert in this country")
    countryName: str = Field(..., validation_alias="countryName")
    countryCode: str = Field(..., validation_alias="countryCode")
    continentName: str = Field(..., validation_alias="continentName")
    totalShowsToDate: int = Field(..., validation_alias="totalShowsToDate")

    model_config = ConfigDict(populate_by_name=True)