import logging
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class FlatchrClient:
    """Client for Flatchr ATS APIs"""
    
    def __init__(self):
        self.careers_url = settings.FLATCHR_CAREERS_URL
        self.api_url = settings.FLATCHR_API_URL
        self.company_id = settings.FLATCHR_COMPANY_ID
        self.token = settings.FLATCHR_TOKEN
        self.user_id = settings.FLATCHR_API_USER_ID
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    async def create_candidate(self, vacancy_slug: str, firstname: str, lastname: str, linkedin_url: str, column_id: Optional[int] = None, comment: Optional[str] = None, resume_base64: Optional[str] = None, resume_filename: Optional[str] = None) -> bool:
        endpoint = f"{self.careers_url}/vacancy/candidate/json"
        
        # Use provided base64 PDF or default dummy PDF
        default_dummy_pdf = "JVBERi0xLjQKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFI+PgplbmRvYmoKMiAwIG9iago8PC9UeXBlL1BhZ2VzL0NvdW50IDEvS2lkc1szIDAgUl0+PgplbmRvYmoKMyAwIG9iago8PC9UeXBlL1BhZ2UvTWVkaWFCb3hbMCAwIDU5NSA4NDJdL1BhcmVudCAyIDAgUi9SZXNvdXJjZXM8PC9Gb250PDwvRjEgNCAwIFI+Pj4+L0NvbnRlbnRzIDUgMCBSPj4KZW5kb2JqCjQgMCBvYmoKPDwvVHlwZS9Gb250L1N1YnR5cGUvVHlwZTEvQmFzZUZvbnQvSGVsdmV0aWNhPj4KZW5kb2JqCjUgMCBvYmoKPDwvTGVuZ3RoIDIxPj4Kc3RyZWFtCkJUCjEwIDAgMCAxMCAxMCA1MDAgVG0KKEhlbGxvIFdvcmxkKVRqCkVUCmVuZHN0cmVhbQplbmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDE1IDAwMDAwIG4gCjAwMDAwMDAwNjIgMDAwMDAgbiAKMDAwMDAwMDEyMSAwMDAwMCBuIAowMDAwMDAwMjMwIDAwMDAwIG4gCjAwMDAwMDAzMTggMDAwMDAgbiAKdHJhaWxlcgo8PC9TaXplIDYvUm9vdCAxIDAgUj4+CnN0YXJ0eHJlZgozOTA0CiUlRU9GCg=="
        final_pdf_data = resume_base64 if resume_base64 else default_dummy_pdf
        final_filename = resume_filename if resume_filename else f"CV_{firstname}_{lastname}.pdf"
        
        payload = {
            "vacancy": vacancy_slug,
            "firstname": firstname,
            "lastname": lastname,
            "type": "document",
            "resume": {
                "data": final_pdf_data,
                "fileName": final_filename,
                "contentType": "application/pdf"
            }
        }
        if column_id is not None:
            payload["column_id"] = str(column_id)
        if comment:
            payload["comment"] = comment
        if linkedin_url and linkedin_url != "https://linkedin.com/in/unknown":
            payload["urls"] = [linkedin_url]
            
        logger.info(f"[Flatchr] Creating candidate {firstname} {lastname} in vacancy {vacancy_slug}")
        
        # log full request
        logger.info(f"[Flatchr] Full request: {endpoint} {payload} {self.headers}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(endpoint, json=payload, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                logger.info(f"[Flatchr] Successfully created candidate {firstname} {lastname}")
                return True
            except httpx.HTTPStatusError as e:
                logger.error(f"[Flatchr] Failed to create candidate. Status: {e.response.status_code}, Response: {e.response.text}")
                return False
            except Exception as e:
                logger.error(f"[Flatchr] Error creating candidate: {e}")
                return False

    async def list_candidates(self, vacancy_id: str, firstname: str, lastname: str) -> Optional[str]:
        endpoint = f"{self.api_url}/company/{self.company_id}/search/applicants"
        payload = {
            "vacancy": str(vacancy_id),
            "firstname": firstname,
            "lastname": lastname
        }
        logger.info(f"[Flatchr] Listing candidates for {firstname} {lastname} in vacancy_id {vacancy_id}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(endpoint, json=payload, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                results = response.json()
                if not results or not isinstance(results, list):
                    logger.warning(f"[Flatchr] No applicants found for {firstname} {lastname}")
                    return None
                results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                first_match = results[0]
                applicant_id = str(first_match.get("applicant", ""))
                if applicant_id:
                    logger.info(f"[Flatchr] Found applicant_id {applicant_id} for {firstname} {lastname}")
                    return applicant_id
                return None
            except httpx.HTTPStatusError as e:
                logger.error(f"[Flatchr] Failed to search candidate. Status: {e.response.status_code}, Response: {e.response.text}")
                return None
            except Exception as e:
                logger.error(f"[Flatchr] Error searching candidate: {e}")
                return None

    async def move_candidate(self, applicant_id: str, original_vacancy_id: str, target_column_id: int) -> bool:
        endpoint = f"{self.api_url}/company/{self.company_id}/vacancy/{original_vacancy_id}/applicant/{applicant_id}"
        payload = {
            "column_id": target_column_id
        }
        logger.info(f"[Flatchr] Moving applicant {applicant_id} to vacancy {original_vacancy_id} | column {target_column_id}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(endpoint, json=payload, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                logger.info(f"[Flatchr] Successfully moved applicant {applicant_id}")
                return True
            except httpx.HTTPStatusError as e:
                logger.error(f"[Flatchr] Failed to move applicant. Status: {e.response.status_code}, Response: {e.response.text}")
                return False
            except Exception as e:
                logger.error(f"[Flatchr] Error moving applicant: {e}")
                return False
