from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, db_instance
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from app.core.security import validate_layered_security
from fastapi import Depends

from app.routes.geography_routes import router as geo_router
from app.routes.musicians_routes import router as musician_router
from app.routes.albums_routes import router as album_router
from app.routes.composers_routes import router as composer_router
from app.routes.tracks_routes import router as track_router
from app.routes.statistics_routes import router as statistics_router
from app.routes.concert_routes import router as concert_routes
from app.routes.concert_masters_routes import router as concert_masters_routes

env_type = os.getenv("ENVIRONMENT", "development")
env_file = ".env.production" if env_type == "production" else ".env"

load_dotenv(env_file)

raw_origins = os.getenv("ALLOWED_ORIGINS")

# Validación de seguridad
if not raw_origins:
    # Si la variable no existe en el .env, la API se detiene por seguridad.
    raise RuntimeError(
        f"❌ SEGURIDAD: La variable ALLOWED_ORIGINS debe estar definida en {env_type.upper()}."
    )

origins = [o.strip() for o in raw_origins.split(",")]
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    current_env = os.getenv("ENVIRONMENT", "development")
    
    print(os.getenv("API_KEY_INTERNAL", "development") + "\n")
        
    if current_env == "production":
        print("\n" + "="*40)
        print("⚠️  RUNNING IN PRODUCTION MODE")
        print("="*40 + "\n")
    else:
        print("\n" + "-"*40)
        print("🛠️  RUNNING IN DEVELOPMENT MODE")
        print("-"*40 + "\n")
        
    print("🚀 Iniciando conexión a MongoDB...")

    uri = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_NAME")
    await connect_to_mongo(uri, db_name)

    if db_instance.db is not None:
        print("✅ MongoDB está listo y asignado a db_instance.db")

        # --- LLAMADA A LA CONFIGURACIÓN DE ÍNDICES ---
        from app.database import setup_database_indexes # Asegúrate de importar tu función
        print("indexing database...")
        await setup_database_indexes(db_instance.db)
        # ---------------------------------------------
    else:
        print("❌ ERROR: La conexión falló, db_instance.db sigue siendo None")

    yield
    if db_instance.client:
        db_instance.client.close()
        print("🔌 Conexión a MongoDB cerrada")

app = FastAPI(title="Santana Archive", lifespan=lifespan)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"], # Restringe solo a lo que necesitas
    allow_headers=["*"], # Es más seguro dejar que el navegador maneje los headers
)

API_V1 = "/api/v1"

app.include_router(geo_router, prefix=API_V1, dependencies=[Depends(validate_layered_security)])
app.include_router(musician_router, prefix=API_V1, dependencies=[Depends(validate_layered_security)])
app.include_router(album_router, prefix=API_V1, dependencies=[Depends(validate_layered_security)])
app.include_router(composer_router, prefix=API_V1, dependencies=[Depends(validate_layered_security)])
app.include_router(track_router, prefix=API_V1, dependencies=[Depends(validate_layered_security)])
app.include_router(statistics_router, prefix=API_V1, dependencies=[Depends(validate_layered_security)])
app.include_router(concert_routes, prefix=API_V1, dependencies=[Depends(validate_layered_security)])
app.include_router(concert_masters_routes, prefix=API_V1, dependencies=[Depends(validate_layered_security)])

#MÁS REPORTES:
#Músicos que tuvieron otros roles en canciones: por ejemplo, Carlos tocaba congas en algunas canciones