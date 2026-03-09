import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.clients.flatchr_client import FlatchrClient
from app.clients.jemmo_client import JemmoClient
from app.utils.pdf_generator import generate_candidate_pdf
logger = logging.getLogger(__name__)

class SourcingService:
    @staticmethod
    async def process_new_sourced_candidate(candidate_data: Dict[str, Any], original_vacancy_id: str, match_id: Optional[str] = None) -> None:
        """
        Méthode Orchestateur pour le Flux 3 : Création directe dans l'offre finale avec la bonne colonne.
        """
        if original_vacancy_id is None:
            original_vacancy_id = settings.FLATCHR_TEMP_VACANCY_SLUG
        flatchr_client = FlatchrClient()
        default_column_id = settings.FLATCHR_DEFAULT_COLUMN_ID
        
        # Extraction des données selon le nouveau format Jemmo Sourcing (talents)
        talent_info = candidate_data.get("talent") or {}
        firstname = talent_info.get("first_name") or candidate_data.get("firstName", "Unknown")
        lastname = talent_info.get("last_name") or candidate_data.get("lastName", "Unknown")
        linkedin_url = talent_info.get("linkedin_url")
                
        # Génération du beau PDF récapitulatif
        try:
            pdf_base64 = generate_candidate_pdf(firstname, lastname, candidate_data, talent_info)
            pdf_filename = f"Profil_Jemmo_{firstname}_{lastname}.pdf"
            comment_text = "Profil sourcé et présélectionné par Jemmo Sourcing. 📄 Toutes les informations d'analyse (Score, Points Forts, Compétences) sont disponibles dans le PDF ci-joint."
        except Exception as e:
            logger.error(f"[Workflow Flatchr] Erreur lors de la génération du PDF pour {firstname} {lastname}: {e}")
            pdf_base64 = None
            pdf_filename = None
            comment_text = "Profil sourcé par Jemmo Sourcing. Erreur lors de la génération du PDF récapitulatif."
            
        if match_id:
            comment_text += f"\n\nfrom Jemmo\nMatch ID: {match_id}"
        
        logger.info(f"[Workflow Flatchr] Beginning ingestion for candidate {firstname} {lastname} directly into vacancy {original_vacancy_id}")
        
        # Création directe dans l'offre cible
        created = await flatchr_client.create_candidate(
            vacancy_slug=original_vacancy_id,
            firstname=firstname,
            lastname=lastname,
            linkedin_url=linkedin_url,
            column_id=default_column_id,
            comment=comment_text,
            resume_base64=pdf_base64,
            resume_filename=pdf_filename
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
            
            candidates = results.get("talents", [])
            
            if not candidates:
                logger.info(f"[Background Sourcing] Aucun candidat retourné pour le match {match_id}")
                return
                
            logger.info(f"[Background Sourcing] Succès. {len(candidates)} candidat(s) récupéré(s). Injection dans Flatchr...")
            
            for i, candidate in enumerate(candidates):
                if i >= 3:
                    break
                await SourcingService.process_new_sourced_candidate(
                    candidate_data=candidate,
                    original_vacancy_id=vacancy_slug,
                    match_id=match_id
                )
            logger.info(f"[Background Sourcing] Fin de l'injection pour le match {match_id}")

        except Exception as e:
            logger.error(f"[Background Sourcing] Erreur lors de la récupération des résultats : {e}", exc_info=True)
