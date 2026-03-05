import logging
from typing import Dict, Any
from app.clients.jemmo_client import JemmoClient

logger = logging.getLogger(__name__)

class AtsService:
    @staticmethod
    async def trigger_sourcing_sync_and_match(job_id: str, vacancy_slug: str, title: str, payload_data: Dict[str, Any]):
        """
        Tâche asynchrone pour 1/ Synchroniser l'offre ATS dans Jemmo et 2/ Déclencher le match IA.
        """
        try:
            jemmo_client = JemmoClient()
            
            if not vacancy_slug:
                logger.error(f"[Background] Impossible de synchroniser l'offre {job_id} : vacancy_slug manquant. Abandon.")
                return

            # 1. Sync Job
            logger.info(f"[Background] Démarrage Sourcing Sync pour job_id={job_id}, slug={vacancy_slug}")
            await jemmo_client.sync_job(vacancy_slug, title, payload_data)
            
            # 2. Trigger Match
            logger.info(f"[Background] Démarrage Sourcing Match pour slug={vacancy_slug}")
            await jemmo_client.trigger_match(vacancy_slug)
            
        except Exception as e:
            logger.error(f"[Background] Erreur lors de la chaîne Sourcing (Sync/Match) : {e}", exc_info=True)
