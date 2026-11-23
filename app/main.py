
from fastapi import FastAPI
from app.routes import logs, incidents

app = FastAPI(
    title="IncidentPilot API",
    description="Backend for AI-powered incident investigation",
    version="1.0.0"
)

# Connect the log upload routes to the main application
app.include_router(
    logs.router,
    prefix="/logs",
    tags=["Logs"]
)
app.include_router(
    incidents.router,
    prefix="/incidents",
    tags=["Incidents"]
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "IncidentPilot backend is running"
    }

# Path parameter: identifies a particular log
@app.get("/logs/{log_id}")
def get_log(log_id: int):
    return {
        "log_id": log_id,
        "message": "Log record requested"
    }


# Query parameter: filters logs by their level
@app.get("/logs")
def filter_logs(level: str = "ERROR"):
    return {
        "filter": level,
        "message": "Logs filtered successfully"
    }