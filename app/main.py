
from fastapi import FastAPI
from app.routes import logs

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


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "IncidentPilot backend is running"
    }
