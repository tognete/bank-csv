from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.extraction import ExtractionResponse, HealthResponse
from app.services.extractor import DocumentProcessor

router = APIRouter()
processor = DocumentProcessor()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/extract", response_model=ExtractionResponse)
async def extract(file: UploadFile = File(...)) -> ExtractionResponse:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    result = processor.process(file.filename, content)
    dataframe = result.dataframe
    if not dataframe.empty:
        sanitized = dataframe.fillna("").astype(str)
        csv_payload = sanitized.to_csv(index=False)
        columns = sanitized.columns.tolist()
        rows = sanitized.values.tolist()
    else:
        csv_payload = ""
        columns = []
        rows = []
    return ExtractionResponse(
        filename=file.filename,
        columns=columns,
        rows=rows,
        csv=csv_payload,
        row_count=len(rows),
        notes=result.notes,
    )
