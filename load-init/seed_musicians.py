import asyncio
import pandas as pd
import os
from datetime import datetime
from pydantic import ValidationError
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Importación de tu infraestructura
from app.database import connect_to_mongo, get_db, db_instance
from app.models.musician import MusicianSchema

# Cargamos variables de entorno (asegúrate de tener python-dotenv instalado)
load_dotenv()


def clean_data(val):
    if pd.isna(val) or val == "N/A" or val == "Presente":
        return None
    return val


def get_role_ids(instrument_str, role_map):
    if not instrument_str:
        return []
    names = [i.strip() for i in instrument_str.split(",")]
    return [role_map[name] for name in names if name in role_map]


async def load_excel_to_mongo(file_path):
    # 1. Obtener credenciales del entorno
    uri = os.getenv("MONGODB_URL")
    db_name = os.getenv("DB_NAME")

    if not uri or not db_name:
        print("❌ Error: MONGODB_URL o DB_NAME no están definidos en el .env")
        return

    # 2. Conexión usando TU método
    await connect_to_mongo(uri, db_name)
    db = get_db()

    # 3. Mapeo de roles desde la DB
    role_map = {}
    async for role in db.roles.find():
        role_map[role["name"]] = role["id"]

    # 4. Procesar Excel
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"❌ Error al leer Excel: {e}")
        return

    print(f"🚀 Procesando {len(df)} registros...")
    stats = {"nuevos": 0, "existentes": 0, "errores": 0}

    for index, row in df.iterrows():
        try:
            first_name = str(row['Nombre']).strip()
            last_name = str(row['Apellido']).strip()

            # Validación de duplicados
            existing = await db.musicians.find_one({
                "first_name": first_name,
                "last_name": last_name
            })

            if existing:
                stats["existentes"] += 1
                continue

            # Preparación de datos
            apelativo = clean_data(row['Apelativo'])
            start_year = int(row['Integró'])
            start_date = datetime(start_year, 1, 1).date()

            end_val = clean_data(row['Salió'])
            end_date = None
            if end_val:
                end_date = datetime(int(end_val), 12, 31).date()

            role_ids = get_role_ids(row['Instrumentos'], role_map)

            # 5. Validación con Pydantic
            musician_data = {
                "id": index + 1,
                "first_name": first_name,
                "last_name": last_name,
                "apelativo": apelativo,
                "country_id": 1,
                "start_date": start_date,
                "end_date": end_date,
                "roles": role_ids,
                "bio": f"Músico de Santana que toca {row['Instrumentos']}"
            }

            musician_obj = MusicianSchema(**musician_data)

            # 6. Formateo para MongoDB
            mongo_doc = musician_obj.model_dump(by_alias=True)
            mongo_doc["start_date"] = datetime.combine(musician_obj.start_date, datetime.min.time())
            if musician_obj.end_date:
                mongo_doc["end_date"] = datetime.combine(musician_obj.end_date, datetime.min.time())

            await db.musicians.insert_one(mongo_doc)
            stats["nuevos"] += 1
            print(f"  + Registrado: {first_name} {last_name}")

        except ValidationError as e:
            stats["errores"] += 1
            print(f"  ❌ Error Pydantic: {e}")
        except Exception as e:
            stats["errores"] += 1
            print(f"  ⚠️ Error en fila {index}: {e}")

    # Resumen y cierre
    print(f"\n✅ Finalizado. Nuevos: {stats['nuevos']} | Existentes: {stats['existentes']}")
    db_instance.client.close()


if __name__ == "__main__":
    asyncio.run(load_excel_to_mongo("musicians.xlsx"))