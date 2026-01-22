# python -m scripts.maintenance.update_musicians_from_excel
import asyncio
import pandas as pd
from datetime import datetime
from scripts.common.db_utils import db_manager
from pathlib import Path

def format_year_to_date(year_str):
    """Convierte un año al 1 de enero de ese año. Retorna None si está vacío."""
    if pd.isna(year_str) or str(year_str).strip() in ["", "nan", "None"]:
        return None
    try:
        # Limpieza para casos donde el año viene como '1969.0'
        year = int(float(str(year_str).strip()))
        return datetime(year, 1, 1)
    except (ValueError, TypeError):
        return None

async def process_musicians_excel(filename: str):
    current_dir = Path(__file__).parent 
    file_path = current_dir.parent / filename 
    
    if not file_path.exists():
        print(f"❌ No existe el archivo: {file_path}")
        return
    
    db = await db_manager.connect()
    
    try:
        # dtype=str es vital para que 'Salió' no se convierta en float/NaN erróneamente
        df = pd.read_excel(file_path, dtype=str)
    except Exception as e:
        print(f"❌ Error al leer Excel: {e}")
        return

    print(f"📊 Procesando {len(df)} filas...")

    for index, row in df.iterrows():
        first_name = str(row["Nombre"]).strip()
        last_name = str(row["Apellido"]).strip()
        country_name = str(row["País Origen"]).strip()
        
        # 1. Buscar el músico por nombre y apellido
        musician = await db.musicians.find_one({
            "first_name": first_name, 
            "last_name": last_name
        })

        if not musician:
            print(f"⚠️ El músico no existe: {first_name} {last_name}")
            continue

        # 2. Preparar datos de actualización
        # Si 'Integró' está vacío, activeFrom será None. 
        # Si 'Salió' está vacío, activeTo será None.
        update_data = {
            "active_from": format_year_to_date(row.get("Integró")),
            "active_to": format_year_to_date(row.get("Salió"))
        }

        # 3. Buscar País para actualizar country_id
        if country_name and country_name.lower() != "nan":
            country = await db.countries.find_one({"name": country_name})
            if country:
                update_data["country_id"] = country["id"]
            else:
                print(f"🌎 LOG: El país '{country_name}' no existe en la colección countries.")

        # 4. Ejecutar actualización
        result = await db.musicians.update_one(
            {"_id": musician["_id"]},
            {"$set": update_data}
        )

        if result.modified_count > 0:
            print(f"✅ ACTUALIZADO: {first_name} {last_name} (Salió: {update_data['active_to']})")
        else:
            print(f"ℹ️ SIN CAMBIOS: {first_name} {last_name}")

    print("🏁 Proceso de mantenimiento finalizado.")
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(process_musicians_excel("data_sources/musicians.xlsx"))