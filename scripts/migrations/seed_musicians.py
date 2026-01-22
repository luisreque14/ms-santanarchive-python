# python -m scripts.migrations.seed_musicians
import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path
from scripts.common.db_utils import db_manager

def clean_data(val):
    """Limpia valores de Excel manejando NAs y strings específicos."""
    if pd.isna(val) or str(val).strip() in ["", "nan", "N/A", "Presente", "None"]:
        return None
    return str(val).strip()

def format_year_to_date(year_val):
    """Convierte un año de Excel al 1 de enero de ese año (objeto datetime)."""
    cleaned = clean_data(year_val)
    if not cleaned:
        return None
    try:
        # Maneja casos como '1969' o '1969.0'
        year = int(float(cleaned))
        return datetime(year, 1, 1)
    except (ValueError, TypeError):
        return None

def get_role_ids(instrument_str, role_map):
    """Mapea strings de instrumentos a sus IDs numéricos correspondientes."""
    if not instrument_str or pd.isna(instrument_str):
        return []
    names = [i.strip() for i in str(instrument_str).split(",")]
    return [role_map[name] for name in names if name in role_map]

async def seed_musicians(filename: str):
    # Configuración de rutas
    current_dir = Path(__file__).parent 
    file_path = current_dir.parent / filename 
    
    if not file_path.exists():
        print(f"❌ No existe el archivo: {file_path}")
        return

    db = await db_manager.connect()

    # 1. Mapeo de roles desde la DB
    role_map = {}
    async for role in db.roles.find():
        role_map[role["name"]] = role["id"]

    # 2. Procesar Excel
    try:
        df = pd.read_excel(file_path, dtype=str)
    except Exception as e:
        print(f"❌ Error al leer Excel: {e}")
        return

    print(f"🚀 Procesando {len(df)} registros...")
    stats = {"nuevos": 0, "actualizados": 0, "errores": 0}

    # 3. Obtener el último ID para autoincrementar
    last_m = await db.musicians.find_one(sort=[("id", -1)])
    current_id_tracker = (last_m["id"] + 1) if last_m else 1

    for index, row in df.iterrows():
        try:
            first_name = str(row['Nombre']).strip()
            last_name = str(row['Apellido']).strip()
            country_name = clean_data(row.get('País Origen'))

            # Validación de existencia
            existing = await db.musicians.find_one({
                "first_name": first_name,
                "last_name": last_name
            })

            # Preparación de datos manual (reemplaza al Schema)
            country_id = 1
            if country_name:
                country = await db.countries.find_one({"name": country_name})
                if country:
                    country_id = country["id"]
                else:
                    print(f"⚠️ País no encontrado: {country_name} para {first_name}")

            # Construcción del documento directamente como diccionario
            mongo_doc = {
                "id": existing["id"] if existing else current_id_tracker,
                "first_name": first_name,
                "last_name": last_name,
                "apelativo": clean_data(row.get('Apelativo')),
                "country_id": country_id,
                "active_from": format_year_to_date(row.get('Integró')),
                "active_to": format_year_to_date(row.get('Salió')),
                "roles": get_role_ids(row.get('Instrumentos'), role_map),
                "bio": f"Músico de Santana que toca {row.get('Instrumentos', 'varios instrumentos')}"
            }

            if existing:
                # Actualización
                #await db.musicians.update_one(
                #    {"_id": existing["_id"]},
                #    {"$set": mongo_doc}
                #)
                stats["actualizados"] += 1
                #print(f"🔄 Actualizado: {first_name} {last_name}")
            else:
                # Inserción
                await db.musicians.insert_one(mongo_doc)
                stats["nuevos"] += 1
                current_id_tracker += 1
                print(f"✨ Registrado: {first_name} {last_name}")

        except Exception as e:
            stats["errores"] += 1
            print(f"⚠️ Error inesperado en fila {index} ({row.get('Nombre')}): {e}")

    print(f"\n✅ Finalizado. Nuevos: {stats['nuevos']} | Actualizados: {stats['actualizados']} | Errores: {stats['errores']}")
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(seed_musicians("data_sources/musicians.xlsx"))