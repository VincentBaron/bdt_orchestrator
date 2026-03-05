import logging
from typing import Dict, Any
from app.core.config import settings
from app.clients.flatchr_client import FlatchrClient
from app.clients.jemmo_client import JemmoClient

logger = logging.getLogger(__name__)

class SourcingService:
    @staticmethod
    async def process_new_sourced_candidate(candidate_data: Dict[str, Any], original_vacancy_id: str) -> None:
        """
        Méthode Orchestateur pour le Flux 3 : Création directe dans l'offre finale avec la bonne colonne.
        """
        if original_vacancy_id is None:
            original_vacancy_id = settings.FLATCHR_TEMP_VACANCY_SLUG
        flatchr_client = FlatchrClient()
        default_column_id = settings.FLATCHR_DEFAULT_COLUMN_ID
        
        # Extraction des données (à adapter selon le format exact renvoyé par Jemmo Sourcing)
        firstname = candidate_data.get("firstName", "Unknown")
        lastname = candidate_data.get("lastName", "Unknown")
        
        # Récupération de l'URL LinkedIn (ou première dispo)
        link_urls = candidate_data.get("link_urls", [])
        if not hasattr(link_urls, "__iter__") or isinstance(link_urls, str):
            link_urls = []
            
        linkedin_url = link_urls[0] if len(link_urls) > 0 else "https://linkedin.com/in/unknown"
        
        logger.info(f"[Workflow Flatchr] Beginning ingestion for candidate {firstname} {lastname} directly into vacancy {original_vacancy_id}")
        
        # Création directe dans l'offre cible
        created = await flatchr_client.create_candidate(
            vacancy_slug=original_vacancy_id,
            firstname=firstname,
            lastname=lastname,
            linkedin_url=linkedin_url,
            column_id=default_column_id
        )
        
        if not created:
            logger.error(f"[Workflow Flatchr] Aborting workflow for {firstname} {lastname} (Creation failed)")
            return
            
        logger.info(f"[Workflow Flatchr] Workflow completed successfully for {firstname} {lastname}")

    @staticmethod
    async def fetch_and_process_sourcing_results(match_id: str, vacancy_slug: str):
        """
        Tâche asynchrone déclenchée après un webhook Sourcing pour fetch les résultats Jemmo.
        """
        logger.info(f"[Background Sourcing] Démarrage de l'analyse des résultats pour match_id={match_id} (slug = {vacancy_slug})")
        try:
            jemmo_client = JemmoClient()
            results = await jemmo_client.get_match_results(match_id)
            
            candidates = results if isinstance(results, list) else results.get("candidates", [])
            
            if not candidates:
                logger.info(f"[Background Sourcing] Aucun candidat retourné pour le match {match_id}")
                return
                
            logger.info(f"[Background Sourcing] Succès. {len(candidates)} candidat(s) récupéré(s). Injection dans Flatchr...")
            
            for candidate in candidates:
                await SourcingService.process_new_sourced_candidate(
                    candidate_data=candidate,
                    original_vacancy_id=vacancy_slug
                )
                
            logger.info(f"[Background Sourcing] Fin de l'injection pour le match {match_id}")

        except Exception as e:
            logger.error(f"[Background Sourcing] Erreur lors de la récupération des résultats : {e}", exc_info=True)
