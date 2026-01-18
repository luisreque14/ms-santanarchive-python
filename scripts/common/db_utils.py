import os
import asyncio
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# 1. Cargar variables de entorno del .env en la raíz
# El path '../.env' asegura que lo encuentre si ejecutas desde la carpeta scripts
load_dotenv()

class ScriptDbManager:
    """Clase para gestionar la conexión a MongoDB fuera de FastAPI"""
    
    def __init__(self):
        self.url = os.getenv("MONGODB_URL")
        self.db_name = os.getenv("MONGODB_NAME")
        self.client = None
        self.db = None

    async def connect(self):
        if not self.client:
            self.client = AsyncIOMotorClient(self.url)
            self.db = self.client[self.db_name]
            # Opcional: Verificar conexión
            try:
                await self.client.admin.command('ping')
                print(f"✅ [DB-UTILS] Connected to MongoDB: {self.db_name}")
            except Exception as e:
                print(f"❌ [DB-UTILS] Connection Error: {e}")
                raise e
        return self.db

    async def close(self):
        if self.client:
            self.client.close()
            print("🔌 [DB-UTILS] Connection closed")

# Instancia rápida para usar en scripts
db_manager = ScriptDbManager()