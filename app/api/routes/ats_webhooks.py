import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, BackgroundTasks, status
from app.api.dependencies import verify_secret_path
from app.schemas.payloads import AtsJobCreatedPayload
from app.services.ats_service import AtsService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/{secret_path}/job-created",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_secret_path)]
)
async def ats_job_created_webhook(
    background_tasks: BackgroundTasks,
    payload: AtsJobCreatedPayload,
    secret_path: str,
):
    """
    Réception du webhook de création d'offre (ATS Flatchr).
    """
    payload_dict = payload.model_dump()
    logger.info(f"[Webhook ATS] Ingestion job-created: {payload_dict}")
    
    # Extraire le job_id (vacancy ID), le titre et le slug du payload typé
    job_id = str(payload.vacancy.id)
    vacancy_slug = payload.vacancy.slug
    job_title = payload.vacancy.title or "Titre non fourni"
    
    logger.info(f"[Webhook ATS] Extracted job_id: {job_id}, slug: {vacancy_slug}")
    
    # Planifier la synchro Jemmo + Déclenchement de la recherche via le Service ATS
    background_tasks.add_task(AtsService.trigger_sourcing_sync_and_match, job_id, vacancy_slug, job_title, payload_dict)
    
    return {"message": "Webhook ATS reçu et traitement en arrière-plan planifié."}
