from pydantic import BaseModel, Field, ConfigDict


class SafetyReportCreate(BaseModel):
    report_type: str = Field(
        min_length=2,
        max_length=100
    )

    description: str = Field(
        min_length=5,
        max_length=1000
    )

    severity: str = Field(
        default="medium",
        min_length=3,
        max_length=20
    )

    latitude: float = Field(
        ge=-90,
        le=90
    )

    longitude: float = Field(
        ge=-180,
        le=180
    )


class SafetyReportResponse(BaseModel):
    id: int
    user_id: int
    report_type: str
    description: str
    severity: str
    latitude: float
    longitude: float

    model_config = ConfigDict(
        from_attributes=True
    )