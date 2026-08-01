import secrets

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

bearer_scheme = HTTPBearer()


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> None:
    expected_key = settings.connector_api_key.get_secret_value()

    if not secrets.compare_digest(
        credentials.credentials,
        expected_key,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )
