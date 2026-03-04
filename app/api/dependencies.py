from fastapi import HTTPException, Header, Path
from starlette.status import HTTP_403_FORBIDDEN
from app.core.config import settings

def verify_secret_path(secret_path: str = Path(...)):
    """
    Verify that the given secret_path matches the globally configured WEBHOOK_SECRET_PATH.
    If not, raise a 403 Forbidden exception.
    """
    if secret_path != settings.WEBHOOK_SECRET_PATH:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, 
            detail="Invalid webhook secret path"
        )
    return secret_path
