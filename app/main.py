import logging
from fastapi import FastAPI
from app.api.routes import ats_webhooks

# Configuration basique du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(title="BDT Orchestrator (ATS <-> Sourcing IA)")

# Ajout des routes (Step 1)
app.include_router(
    ats_webhooks.router,
    prefix="/webhooks/ats",
    tags=["ATS Webhooks"]
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
