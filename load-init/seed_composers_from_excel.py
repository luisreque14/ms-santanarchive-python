import asyncio
import os
import pandas as pd
from dotenv import load_dotenv

# Importamos tu infraestructura de base de datos
from app.database import connect_to_mongo, get_db, db_instance

load_dotenv()


async def seed_composers_from_excel(file_path: str):
    # 1. Conexión con tus variables del .env
    uri = os.getenv("MONGODB_URL")
    db_name = os.getenv("DB_NAME")

    if not uri or not db_name:
        print("❌ Error: MONGODB_URL o DB_NAME no encontrados en el .env")
        return

    await connect_to_mongo(uri, db_name)
    db = get_db()

    # 2. Caché de Países: Mapeamos Nombre -> ID
    # Esto permite validar si el país existe en la BD rápidamente
    country_cache = {}
    async for country in db.countries.find():
        # Guardamos en minúsculas para una comparación flexible
        country_cache[country["name"].lower().strip()] = country["id"]

    # 3. Leer Excel
    try:
        df = pd.read_excel(file_path)
        # Asegúrate de que las columnas se llamen 'compositor' y 'pais'
        print(f"📂 Leídos {len(df)} registros de {file_path}")
    except Exception as e:
        print(f"❌ Error al abrir el Excel: {e}")
        return

    stats = {"nuevos": 0, "existentes": 0, "sin_pais": 0}

    # 4. Procesar compositores
    for index, row in df.iterrows():
        name = str(row['Compositor']).strip()
        country_name_excel = str(row['Pais']).strip() if pd.notna(row['Pais']) else None

        # --- VALIDACIÓN: Evitar duplicados ---
        existing = await db.composers.find_one({"full_name": name})
        if existing:
            stats["existentes"] += 1
            continue

        # --- VALIDACIÓN DE PAÍS ---
        country_id = None
        if country_name_excel:
            # Buscamos el nombre del Excel en nuestro caché de la BD
            country_id = country_cache.get(country_name_excel.lower())

            if country_id is None:
                print(f"⚠️ País '{country_name_excel}' no encontrado en BD. Registrando a {name} sin país.")

        # 5. Crear documento
        composer_doc = {
            "id": index + 1,  # O tu lógica de IDs
            "full_name": name,
        }

        # Solo agregamos country_id si pasó todas las validaciones
        if country_id:
            composer_doc["country_id"] = country_id
        else:
            stats["sin_pais"] += 1

        await db.composers.insert_one(composer_doc)
        stats["nuevos"] += 1
        print(f"✅ Registrado: {name}")

    # Resumen y cierre
    print(f"\n" + "=" * 30)
    print(f"📊 RESUMEN DE CARGA")
    print(f"Nuevos compositores: {stats['nuevos']}")
    print(f"Omitidos (Ya existían): {stats['existentes']}")
    print(f"Registrados sin país: {stats['sin_pais']}")
    print("=" * 30)

    if db_instance.client:
        db_instance.client.close()
        print("🔌 Conexión cerrada.")


if __name__ == "__main__":
    # Cambia "compositories.xlsx" por el nombre real de tu archivo
    asyncio.run(seed_composers_from_excel("compositores.xlsx"))