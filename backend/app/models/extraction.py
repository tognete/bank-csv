from pydantic import BaseModel


class ExtractionResponse(BaseModel):
    filename: str
    columns: list[str]
    rows: list[list[str]]
    csv: str
    row_count: int
    notes: list[str] = []


class HealthResponse(BaseModel):
    status: str
