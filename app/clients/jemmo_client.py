import logging
import httpx
from typing import Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class JemmoClient:
    """Client for Jemmo APIs (Sourcing Tool)"""
    
    def __init__(self):
        self.base_url = settings.SOURCING_API_URL
        self.external_id = settings.SOURCING_CLIENT_EXTERNAL_ID
        self.api_key = settings.SOURCING_API_KEY
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    async def sync_job(self, vacancy_slug: str, job_title: str, ats_payload: Dict[str, Any]) -> str:
        endpoint = f"{self.base_url}/api/v1/partners/clients/{self.external_id}/sync/jobs"
        payload = {
            "externalJobId": vacancy_slug,
            "title": job_title,
            "rawData": ats_payload
        }
        logger.info(f"[Jemmo] Syncing job {vacancy_slug}...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(endpoint, json=payload, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                logger.info(f"[Jemmo] Successfully synced job {vacancy_slug}")
                return vacancy_slug
            except httpx.HTTPStatusError as e:
                logger.error(f"[Jemmo] Sync failed with status {e.response.status_code} : {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"[Jemmo] Error during job sync: {e}")
                raise

    async def trigger_match(self, vacancy_slug: str) -> None:
        endpoint = f"{self.base_url}/api/v1/partners/clients/{self.external_id}/jobs/{vacancy_slug}/match"
        logger.info(f"[Jemmo] Triggering match for job {vacancy_slug}...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(endpoint, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                logger.info(f"[Jemmo] Successfully triggered match for job {vacancy_slug}")
            except httpx.HTTPStatusError as e:
                logger.error(f"[Jemmo] Match trigger failed with status {e.response.status_code} : {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"[Jemmo] Error during match trigger: {e}")
                raise

    async def get_match_results(self, match_id: str) -> List[Dict[str, Any]]:
        endpoint = f"{self.base_url}/api/v1/partners/clients/{self.external_id}/matches/{match_id}"
        logger.info(f"[Jemmo] Fetching match results for matchId {match_id}...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(endpoint, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                logger.info(f"[Jemmo] Successfully fetched match {match_id}")
                return data 
            except httpx.HTTPStatusError as e:
                logger.error(f"[Jemmo] Get match results failed with status {e.response.status_code} : {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"[Jemmo] Error during get match results: {e}")
                raise
