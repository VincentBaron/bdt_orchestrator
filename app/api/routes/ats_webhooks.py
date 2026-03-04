import logging
import httpx
from typing import Any, Dict
from fastapi import APIRouter, Depends, BackgroundTasks, status
from app.api.dependencies import verify_secret_path
from app.schemas.payloads import AtsJobCreatedPayload
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

async def trigger_sourcing_match(job_id: str, payload_data: Dict[str, Any]):
    """
    Tâche asynchrone pour appeler l'API Sourcing (Mock pour l'instant).
    """
    url = f"{settings.SOURCING_API_URL}/partners/clients/{settings.SOURCING_CLIENT_EXTERNAL_ID}/jobs/{job_id}/match"
    headers = {
        "x-api-key": settings.SOURCING_API_KEY
    }
    
    logger.info(f"[Background] Déclenchement Sourcing Match via {url} pour le job_id={job_id}")
    
    # Mocking de l'appel HTTP
    # Pour l'instant, on lance juste une requête GET factice ou on log la requête qui serait envoyée
    try:
        # Dans un vrai scénario :
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(url, headers=headers, json={"ats_payload": payload_data})
        #     response.raise_for_status()
        #     logger.info(f"[Background] Réponse Sourcing: {response.status_code}")
        
        logger.info(f"[Background] (MOCK) Appel HTTP POST vers {url} simulé avec succès.")
        
    except Exception as e:
        logger.error(f"[Background] Erreur lors du déclenchement du Sourcing Match : {e}")

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
    # Logguer le payload entrant
    payload_dict = payload.model_dump()
    logger.info(f"[Webhook ATS] Ingestion job-created: {payload_dict}")
    
    # Extraire le job_id (vacancy ID) et le slug du payload typé
    job_id = str(payload.vacancy.id)
    vacancy_slug = payload.vacancy.slug
    
    # On ajoute le slug au payload qu'on va envoyer au sourcing
    sourcing_payload = {
        "ats_payload": payload_dict,
        "vacancy_slug": vacancy_slug
    }
    
    logger.info(f"[Webhook ATS] Extracted job_id: {job_id}, slug: {vacancy_slug}")
    
    # Planifier l'appel à l'API de Sourcing via une BackgroundTask
    background_tasks.add_task(trigger_sourcing_match, job_id, sourcing_payload)
    
    return {"message": "Webhook ATS reçu et traitement en arrière-plan planifié."}
