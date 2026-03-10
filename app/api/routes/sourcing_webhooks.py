import logging
from fastapi import APIRouter, Depends, BackgroundTasks, status
from app.api.dependencies import verify_secret_path
from app.schemas.payloads import SourcingMatchCompletedPayload
from app.services.sourcing_service import SourcingService
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/{secret_path}/events",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_secret_path)]
)
async def sourcing_events_webhook(
    background_tasks: BackgroundTasks,
    payload: SourcingMatchCompletedPayload,
    secret_path: str,
):
    """
    Réception du webhook envoyé par Jemmo Sourcing.
    """
    event_type = payload.event
    
    logger.info(f"[Webhook Sourcing] Ingestion Event: {event_type} | MatchId: {payload.data.match_id} | ExternalJobId: {payload.data.job_id}")
    
    job_id = payload.data.job_id or ""
    is_test_slug = job_id.endswith("-test")
    
    if settings.ENVIRONMENT == "dev" and not is_test_slug:
        logger.warning(f"[Webhook Sourcing] DEV MODE: ignoring prod webhook for job_id {job_id}")
        return {"message": "prod request non traitée en dev"}
        
    if settings.ENVIRONMENT != "dev" and is_test_slug:
        logger.warning(f"[Webhook Sourcing] PROD MODE: ignoring test webhook for job_id {job_id}")
        return {"message": "test request non traitée en prod"}
        
    # On ne réagit qu'aux events de complétion du match
    if event_type == "match.completed":
        # Planifier la récupération des résultats via Jemmo API orchestré par SourcingService
        background_tasks.add_task(
            SourcingService.fetch_and_process_sourcing_results,
            match_id=payload.data.match_id,
            vacancy_slug=payload.data.job_id
        )
    else:
        logger.info(f"[Webhook Sourcing] Event ignoré : {event_type}")

    return {"message": "Webhook Sourcing reçu et traitement en cours si applicable."}
