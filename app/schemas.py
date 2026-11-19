
from pydantic import BaseModel


# Defines the exact structure of a successful upload response
class UploadResponse(BaseModel):
    filename: str
    total_lines: int
    parsing_status: str
    message: str
