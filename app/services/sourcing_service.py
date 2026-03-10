import logging
import asyncio
from typing import Dict, Any, Optional
from app.core.config import settings
from app.clients.flatchr_client import FlatchrClient
from app.clients.jemmo_client import JemmoClient
from app.utils.pdf_generator import generate_candidate_pdf
logger = logging.getLogger(__name__)

class SourcingService:
    @staticmethod
    async def process_new_sourced_candidate(candidate_data: Dict[str, Any], original_vacancy_id: str, match_id: Optional[str] = None) -> bool:
        """
        Méthode Orchestateur pour le Flux 3 : Création directe dans l'offre finale avec la bonne colonne.
        """
        if original_vacancy_id is None:
            original_vacancy_id = settings.FLATCHR_TEMP_VACANCY_SLUG
        flatchr_client = FlatchrClient()
        
        source = candidate_data.get("source")
        target_column_id = 56527 if source == "own_pool" else 56500
        
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
            column_id=target_column_id,
            comment=comment_text,
            resume_base64=pdf_base64,
            resume_filename=pdf_filename
        )
        
        if not created:
            logger.error(f"[Workflow Flatchr] Aborting workflow for {firstname} {lastname} (Creation failed)")
            return False
            
        logger.info(f"[Workflow Flatchr] Workflow completed successfully for {firstname} {lastname}")
        return True

    @staticmethod
    async def fetch_and_process_sourcing_results(match_id: str, vacancy_slug: str):
        """
        Tâche asynchrone déclenchée après un webhook Sourcing pour fetch les résultats Jemmo.
        """
        # Configuration d'un logger dédié dans un fichier
        debug_logger = logging.getLogger("sourcing_debug")
        debug_logger.setLevel(logging.INFO)
        if not debug_logger.handlers:
            fh = logging.FileHandler("sourcing_debug.log")
            fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
            debug_logger.addHandler(fh)

        logger.info(f"[Background Sourcing] Démarrage de l'analyse des résultats pour match_id={match_id} (slug = {vacancy_slug})")
        debug_logger.info(f"--- Démarrage process pour match_id={match_id} ---")
        try:
            jemmo_client = JemmoClient()
            
            max_retries = 3
            retry_delay = 3
            
            for attempt in range(max_retries):
                results = await jemmo_client.get_match_results(match_id)
                candidates = results.get("talents", [])
                candidates_returned = len(candidates)
                debug_logger.info(f"Tentative {attempt+1}/{max_retries} - Talents ressortis : {candidates_returned}")
                
                if candidates_returned > 0:
                    break
                    
                if attempt < max_retries - 1:
                    logger.info(f"[Background Sourcing] Aucun candidat retourné (tentative {attempt+1}/{max_retries}). Attente de {retry_delay}s avant de réessayer...")
                    debug_logger.info(f"0 candidat à la tentative {attempt+1}, retry dans {retry_delay}s")
                    await asyncio.sleep(retry_delay)
            
            debug_logger.info(f"1. Talents finaux ressortis du get matchResults (Jemmo) : {candidates_returned}")
            
            if not candidates:
                logger.info(f"[Background Sourcing] Aucun candidat retourné pour le match {match_id} après {max_retries} tentatives.")
                debug_logger.info("Fin du process : 0 candidat")
                return
                
            logger.info(f"[Background Sourcing] Succès. {candidates_returned} candidat(s) récupéré(s). Injection dans Flatchr...")
            
            api_calls = 0
            candidates_created = 0
            
            # Inverser l'ordre (du plus bas au plus haut) pour qu'ils s'empilent avec les meilleurs en haut dans Flatchr
            for candidate in reversed(candidates):
                api_calls += 1
                success = await SourcingService.process_new_sourced_candidate(
                    candidate_data=candidate,
                    original_vacancy_id=vacancy_slug,
                    match_id=match_id
                )
                if success:
                    candidates_created += 1
            
            debug_logger.info(f"2. Talents créés dans Flatchr avec succès : {candidates_created}")
            debug_logger.info(f"3. Nombre d'appels à l'API Flatchr (intentions de création) : {api_calls}")
            logger.info(f"[Background Sourcing] Fin de l'injection pour le match {match_id}")

        except Exception as e:
            logger.error(f"[Background Sourcing] Erreur lors de la récupération des résultats : {e}", exc_info=True)
            debug_logger.error(f"Erreur durant le process : {e}")
