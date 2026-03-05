import logging
from typing import Dict, Any
from app.clients.jemmo_client import JemmoClient

logger = logging.getLogger(__name__)

class AtsService:
    @staticmethod
    async def trigger_sourcing_search(job_id: str, vacancy_slug: str, title: str, payload_data: Dict[str, Any]):
        """
        Tâche asynchrone pour déclencher le match IA via la création d'une recherche Jemmo.
        """
        try:
            jemmo_client = JemmoClient()
            
            if not vacancy_slug:
                logger.error(f"[Background] Impossible de synchroniser l'offre {job_id} : vacancy_slug manquant. Abandon.")
                return

            # 1. Create Jemmo Search (stateless)
            logger.info(f"[Background] Démarrage Sourcing Search pour job_id={job_id}, slug={vacancy_slug}")
            await jemmo_client.create_search(vacancy_slug, payload_data)
            
        except Exception as e:
            logger.error(f"[Background] Erreur lors de la chaîne Sourcing (Sync/Match) : {e}", exc_info=True)
