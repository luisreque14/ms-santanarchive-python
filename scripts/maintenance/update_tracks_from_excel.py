#python -m scripts.maintenance.update_tracks_from_excel
import asyncio
import pandas as pd
from datetime import datetime
from typing import List
from scripts.common.db_utils import db_manager
from pathlib import Path

async def get_or_create_musician(db, full_name: str) -> int:
    full_name = full_name.strip()
    parts = full_name.split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""

    musician = await db.musicians.find_one({"first_name": first_name, "last_name": last_name})
    if musician:
        return musician["id"]
    
    last_m = await db.musicians.find_one(sort=[("id", -1)])
    next_id = (last_m["id"] + 1) if last_m else 1
    await db.musicians.insert_one({
        "id": next_id, "first_name": first_name, "last_name": last_name, "created_at": datetime.now()
    })
    print(f"➕ Músico creado: {full_name} (ID: {next_id})")
    return next_id

async def get_or_create_guest(db, full_name: str) -> int:
    full_name = full_name.strip()
    guest = await db.guest_artists.find_one({"full_name": full_name})
    if guest:
        return guest["id"]

    last_g = await db.guest_artists.find_one(sort=[("id", -1)])
    next_id = (last_g["id"] + 1) if last_g else 1
    await db.guest_artists.insert_one({
        "id": next_id, "full_name": full_name, "created_at": datetime.now()
    })
    print(f"➕ Artista invitado creado: {full_name} (ID: {next_id})")
    return next_id

async def process_excel(filename: str):
    current_dir = Path(__file__).parent 
    file_path = current_dir.parent / filename # Asegura que apunte a scripts/data_sources/...
    
    if not file_path.exists():
        print(f"❌ No existe: {file_path}")
        return
    
    db = await db_manager.connect()
    
    try:
        # Importante: dtype=str para evitar que pandas convierta fechas a su antojo
        df = pd.read_excel(file_path, dtype=str)
    except Exception as e:
        print(f"❌ Error al leer Excel: {e}")
        return

    print(f"📊 Procesando {len(df)} filas...")

    for index, row in df.iterrows():
        track_name = str(row["Canción"]).strip()
        album_name = str(row["Album"]).strip()

        # 2. Procesar lead_vocal_ids
        lead_vocals_ids = []
        # Cambiamos a 'Cantantes principales' según tu instrucción previa
        raw_artists = row.get("Cantantes principales")
        if pd.notna(raw_artists) and str(raw_artists).strip() not in ["", "nan"]:
            names = [n.strip() for n in str(raw_artists).split(",")]
            for name in names:
                if name:
                    m_id = await get_or_create_musician(db, name)
                    lead_vocals_ids.append(m_id)

        # 3. Procesar guest_lead_vocal_ids
        guest_vocals_ids = []
        raw_guests = row.get("Cantantes invitados")
        if pd.notna(raw_guests) and str(raw_guests).strip() not in ["", "nan"]:
            names = [n.strip() for n in str(raw_guests).split(",")]
            for name in names:
                if name:
                    g_id = await get_or_create_guest(db, name)
                    guest_vocals_ids.append(g_id)

        # 4. Actualizar MongoDB
        album = await db.albums.find_one({"title": album_name})
        if not album:
            continue

        update_data = {
            "lead_vocal_ids": lead_vocals_ids,
            "guest_lead_vocal_ids": guest_vocals_ids
        }

        # DEBUG: Imprimir qué estamos intentando guardar si hay IDs
        if lead_vocals_ids or guest_vocals_ids:
            print(f"🔎 Data para {track_name}: Vocals={lead_vocals_ids}, Guests={guest_vocals_ids}")

        result = await db.tracks.update_one(
            {"title": track_name, "album_id": int(album["id"])},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            print(f"❌ ERROR: No se encontró ningún track con título '{track_name}' y album_id {album['id']}")
        elif result.modified_count > 0:
            print(f"✅ ACTUALIZADO en Atlas: {track_name}")
        else:
            print(f"ℹ️ DOCUMENTO ENCONTRADO pero no hubo cambios: {track_name}")

    print("🏁 Proceso finalizado.")
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(process_excel("data_sources/santana_master_v2.xlsx"))