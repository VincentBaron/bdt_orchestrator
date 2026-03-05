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
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
    async def create_search(self, vacancy_slug: str, ats_payload: Dict[str, Any]) -> str:
        endpoint = f"{self.base_url}/api/v1/partners/clients/{self.external_id}/search"
        
        vacancy = ats_payload.get("vacancy", {})
        job_title = vacancy.get("title", "")
        description = vacancy.get("description", "")
        
        address_dict = vacancy.get("address") or {}
        location = address_dict.get("locality", "")
        
        try:
            salary_min = int(vacancy.get("salary", 0))
        except (ValueError, TypeError):
            salary_min = 0
            
        try:
            salary_max = int(vacancy.get("salary_max", 0))
        except (ValueError, TypeError):
            salary_max = 0
            
        payload = {
            "query": "-",
            "job_id": vacancy_slug,
            "criteria": {
                "jobTitle": job_title,
                "description": description,
                "location": location,
                "pricing": {
                    "min": salary_min,
                    "max": salary_max
                }
            }
        }
        
        logger.info(f"[Jemmo] Creating search for job {vacancy_slug}...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(endpoint, json=payload, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                match_id = data.get("match_id", "")
                logger.info(f"[Jemmo] Successfully created search for job {vacancy_slug}. Match ID: {match_id}")
                return match_id
            except httpx.HTTPStatusError as e:
                logger.error(f"[Jemmo] Search creation failed with status {e.response.status_code} : {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"[Jemmo] Error during search creation: {e}")
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
