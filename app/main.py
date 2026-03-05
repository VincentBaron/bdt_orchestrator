import logging
from fastapi import FastAPI
from app.api.routes import ats_webhooks, sourcing_webhooks

# Configuration basique du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(title="BDT Orchestrator (ATS <-> Sourcing IA)")

# Ajout des routes ATS (Step 1)
app.include_router(
    ats_webhooks.router,
    prefix="/webhooks/ats",
    tags=["ATS Webhooks"]
)

# Ajout des routes Sourcing (Step 2)
app.include_router(
    sourcing_webhooks.router,
    prefix="/webhooks/sourcing",
    tags=["Sourcing Webhooks"]
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
