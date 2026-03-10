import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, BackgroundTasks, status, Request
from app.api.dependencies import verify_secret_path
from app.schemas.payloads import AtsJobCreatedPayload
from app.services.ats_service import AtsService
from app.core.config import settings

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
    
    is_test_slug = vacancy_slug.endswith("-test")
    
    if settings.ENVIRONMENT == "dev" and not is_test_slug:
        logger.warning(f"[Webhook ATS] DEV MODE: ignoring prod webhook for slug {vacancy_slug}")
        return {"message": "prod request non traitée en dev"}
        
    if settings.ENVIRONMENT != "dev" and is_test_slug:
        logger.warning(f"[Webhook ATS] PROD MODE: ignoring test webhook for slug {vacancy_slug}")
        return {"message": "test request non traitée en prod"}
        
    logger.info(f"[Webhook ATS] Extracted job_id: {job_id}, slug: {vacancy_slug}")
    
    # Déclenchement de la recherche via le Service ATS
    background_tasks.add_task(AtsService.trigger_sourcing_search, job_id, vacancy_slug, job_title, payload_dict)
    
    return {"message": "Webhook ATS reçu et traitement en arrière-plan planifié."}

@router.post(
    "/{secret_path}/events",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_secret_path)]
)
async def ats_events_webhook(
    background_tasks: BackgroundTasks,
    secret_path: str,
    request: Request,
):
    """
    Catch-all endpoint for ATS events that might be sending a different payload schema. 
    This prevents 422 validation errors and logs the raw payload for inspection.
    """
    try:
        payload_dict = await request.json()
        logger.info(f"[Webhook ATS] Raw /events JSON payload: {payload_dict}")
        
        event_type = payload_dict.get("event")
        if event_type == "match.completed":
            data = payload_dict.get("data", {})
            job_id = data.get("job_id", "")
            match_id = data.get("match_id", "")
            
            is_test_slug = job_id.endswith("-test")
            
            if settings.ENVIRONMENT == "dev" and not is_test_slug:
                logger.warning(f"[Webhook ATS] DEV MODE: ignoring prod webhook for job_id {job_id}")
                return {"message": "prod request non traitée en dev"}
                
            if settings.ENVIRONMENT != "dev" and is_test_slug:
                logger.warning(f"[Webhook ATS] PROD MODE: ignoring test webhook for job_id {job_id}")
                return {"message": "test request non traitée en prod"}
                
            logger.info(f"==== 🎯 DETECTED MATCH.COMPLETED EVENT ====")
            logger.info(f"Event: {event_type}")
            logger.info(f"Job ID (Vacancy Slug): {job_id}")
            logger.info(f"Match ID: {match_id}")
            logger.info(f"Timestamp: {payload_dict.get('timestamp')}")
            logger.info(f"==========================================")
            
            # Since the Sourcing payload is sent to ATS webhook endpoint, we handle it here
            from app.services.sourcing_service import SourcingService
            if job_id and match_id:
                logger.info(f"[Webhook ATS -> Sourcing] Routing match {match_id} for job {job_id} to SourcingService")
                background_tasks.add_task(
                    SourcingService.fetch_and_process_sourcing_results,
                    match_id=match_id,
                    vacancy_slug=job_id
                )
            else:
                logger.warning(f"[Webhook ATS] Missing job_id or match_id in match.completed payload")
                
    except Exception as e:
        body = await request.body()
        logger.error(f"[Webhook ATS] Raw /events body (not JSON): {body.decode('utf-8')}, error: {e}")
        
    return {"message": "Webhook ATS /events reçu et logué."}
