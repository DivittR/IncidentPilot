from fastapi import APIRouter
from app.schemas import IncidentQuery

router = APIRouter()


@router.post("/search")
def search_incidents(query: IncidentQuery):

    return {
        "service": query.service,
        "level": query.level,
        "message": "Incident search request received"
    }