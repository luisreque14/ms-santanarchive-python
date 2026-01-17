from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, db_instance
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from app.routes.geography import router as geo_router
from app.routes.musicians import router as musician_router
from app.routes.albums import router as album_router
from app.routes.recording_credits import router as recording_credits_router
from app.routes.concerts import router as concert_router
from app.routes.performance_credits import router as performance_credits_router
from app.routes.media import router as media_router
from app.routes.composers import router as composer_router
from app.routes.tracks import router as track_router
from app.routes.statistics import router as statistics_router

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

# Registro de routers (ESTO ES LO QUE HACE QUE APAREZCAN EN /DOCS)
app.include_router(geo_router, prefix="/api/v1/geography", tags=["Geography"])
app.include_router(musician_router, prefix="/api/v1/musicians", tags=["Musicians"])
app.include_router(album_router, prefix="/api/v1/albums", tags=["Discography"])
app.include_router(recording_credits_router, prefix="/api/v1/recording-credits", tags=["Recording Credits"])
app.include_router(concert_router, prefix="/api/v1/concerts", tags=["Live Shows"])
app.include_router(performance_credits_router, prefix="/api/v1/performance-credits", tags=["Performance Credits"])
app.include_router(media_router, prefix="/api/v1/media", tags=["Media"])
app.include_router(composer_router, prefix="/api/v1/composers", tags=["Composition"])
app.include_router(track_router, prefix="/api/v1/tracks", tags=["Discography"])
app.include_router(statistics_router, prefix="/api/v1/statistics", tags=["Statistics"])

#MÁS REPORTES:
#Canciones en las que canta Santana (agregar campo Lead Vocals en Tracks (como arreglo de Ids), que haga referencia a la canción)
#Canciones que abrieron conciertos en vivo
#Conciertos en fechas de cumpleaños