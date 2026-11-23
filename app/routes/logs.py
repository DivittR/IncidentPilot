from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas import UploadResponse
from app.services.log_service import count_log_lines

MAX_FILE_SIZE = 1 * 1024 * 1024  # Maximum upload size: 1 MB

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_logs(file: UploadFile = File(...)):

    # Check whether the uploaded file has an allowed extension
    if not file.filename or not file.filename.lower().endswith((".log", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only .log and .txt files are allowed"
        )

    # Read at most 1 MB plus one extra byte
    content = await file.read(MAX_FILE_SIZE + 1)

    # Reject files larger than 1 MB
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size cannot exceed 1 MB"
        )

    # Convert file bytes into readable text
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must contain valid UTF-8 text"
        )

    # Count the number of lines in the file
    total_lines = count_log_lines(text_content)
    return UploadResponse(
        filename=file.filename,
        total_lines=total_lines,
        parsing_status="received",
        message="File uploaded successfully"
    )
