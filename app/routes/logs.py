
from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from app.schemas import UploadResponse
from app.services.log_service import (
    parse_log_content,
    group_similar_errors
)

MAX_FILE_SIZE = 1 * 1024 * 1024  # Maximum upload size: 1 MB

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_logs(
    file: UploadFile = File(...),
    log_type: str = Query("application")
):
    # Validate log type
    if log_type not in ["application", "apache"]:
        raise HTTPException(
            status_code=400,
            detail="log_type must be application or apache"
        )

    # Validate file extension
    if not file.filename or not file.filename.lower().endswith((".log", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only .log and .txt files are allowed"
        )

    # Read at most 1 MB plus one extra byte
    content = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size cannot exceed 1 MB"
        )

    # Convert bytes into readable text
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must contain valid UTF-8 text"
        )

    # Parse log lines into structured records
    result = parse_log_content(text_content, log_type)

    parsed_records = result["parsed_records"]
    invalid_lines = result["invalid_lines"]

    # Group repeated errors into incidents
    incidents = group_similar_errors(parsed_records)

    # Return the complete analysis
    return UploadResponse(
        filename=file.filename,
        log_type=log_type,
        total_lines=result["total_lines"],
        parsed_lines=len(parsed_records),
        invalid_lines_count=len(invalid_lines),
        parsing_status="completed",
        message="Log file parsed and analyzed successfully",
        parsed_records=parsed_records,
        invalid_lines=invalid_lines,
        incidents=incidents
    )
