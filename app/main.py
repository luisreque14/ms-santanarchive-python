from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, db_instance
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from app.routes.geography_routes import router as geo_router
from app.routes.musicians_routes import router as musician_router
from app.routes.albums_routes import router as album_router
from app.routes.recording_credits_routes import router as recording_credits_router
from app.routes.concerts_routes import router as concert_router
from app.routes.performance_credits_routes import router as performance_credits_router
from app.routes.media_routes import router as media_router
from app.routes.composers_routes import router as composer_router
from app.routes.tracks_routes import router as track_router
from app.routes.statistics_routes import router as statistics_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Iniciando conexión a MongoDB...")

    uri = os.getenv("MONGODB_URL")
    db_name = os.getenv("DB_NAME")
    await connect_to_mongo(uri, db_name)

    if db_instance.db is not None:
        print("✅ MongoDB está listo y asignado a db_instance.db")
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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_V1 = "/api/v1"

app.include_router(geo_router, prefix=API_V1)
app.include_router(musician_router, prefix=API_V1)
app.include_router(album_router, prefix=API_V1)
app.include_router(recording_credits_router, prefix=API_V1)
app.include_router(concert_router, prefix=API_V1)
app.include_router(performance_credits_router, prefix=API_V1)
app.include_router(media_router, prefix=API_V1)
app.include_router(composer_router, prefix=API_V1)
app.include_router(track_router, prefix=API_V1)
app.include_router(statistics_router, prefix=API_V1)

#MÁS REPORTES:
#Canciones en las que canta Santana (agregar campo Lead Vocals en Tracks (como arreglo de Ids), que haga referencia a la canción)
#Canciones que abrieron conciertos en vivo
#Conciertos en fechas de cumpleaños
#Duración de álbumes, canción más corta, canción más extensa