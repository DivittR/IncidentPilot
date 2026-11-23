
from typing import Any
from pydantic import BaseModel


class UploadResponse(BaseModel):
    filename: str
    log_type: str
    total_lines: int
    parsed_lines: int
    invalid_lines_count: int
    parsing_status: str
    message: str
    parsed_records: list[dict[str, Any]]
    invalid_lines: list[dict[str, Any]]
    incidents: list[dict[str, Any]]


class IncidentQuery(BaseModel):
    service: str
    level: str
