from fastapi import Request, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
import os

# 1. Definimos el nombre del Header y el Secreto
API_KEY_NAME = "X-Santana-App-Token"
# En producción, usa una cadena larga y aleatoria en tu .env
API_KEY = os.getenv("API_KEY_INTERNAL", "Santana_Archive_2026_Secret_Key")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def validate_layered_security(
    request: Request, 
    api_key: str = Security(api_key_header)
):
    # CAPA 1: Validación del App Token
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Security Token"
        )

    # CAPA 2: Validación del Referer (Opcional pero recomendado)
    # Verifica que la petición venga realmente de tu dominio
    referer = request.headers.get("referer")
    allowed_domain = "https://tu-web-santana.com" # Cambia por tu dominio real
    
    # En desarrollo puedes permitir localhost
    if os.getenv("ENVIRONMENT") == "production":
        if not referer or not referer.startswith(allowed_domain):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied from this origin"
            )

    return api_key