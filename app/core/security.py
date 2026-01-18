from fastapi import Request, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
import os
from dotenv import load_dotenv

env_type = os.getenv("ENVIRONMENT", "development")
load_dotenv(".env.production" if env_type == "production" else ".env")

API_KEY_NAME = "X-Santana-App-Token"
API_KEY = os.getenv("API_KEY_INTERNAL")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def validate_layered_security(request: Request, api_key: str = Security(api_key_header)):
    # 1. Validar Token (Capa 1)
    if api_key != os.getenv("API_KEY_INTERNAL"):
        raise HTTPException(status_code=403, detail="Invalid Security Token")

    # 2. Validar Origen (Capa 2)
    if os.getenv("ENVIRONMENT") == "production":
        referer = request.headers.get("referer")
        # Obtenemos la lista de orígenes permitidos
        allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "")
        allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")]

        # Si el referer no empieza con ninguno de los dominios permitidos, bloqueamos
        if not referer or not any(referer.startswith(origin) for origin in allowed_origins):
            # Para debugging puedes imprimir el referer que llega:
            # print(f"Referer recibido: {referer}") 
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied from this origin"
            )
    
    return api_key