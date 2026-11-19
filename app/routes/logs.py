
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_logs(file: UploadFile = File(...)):

    # Check whether the uploaded file has an allowed extension
    if not file.filename or not file.filename.lower().endswith((".log", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only .log and .txt files are allowed"
        )

    # Read the uploaded file content
    content = await file.read()

    # Convert file bytes into readable text
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must contain valid UTF-8 text"
        )

    # Count the number of lines in the file
    lines = text_content.splitlines()

    return UploadResponse(
        filename=file.filename,
        total_lines=len(lines),
        parsing_status="received",
        message="File uploaded successfully"
    )
