# python -m scripts.maintenance.update_durations_and_live_status
import asyncio
import pandas as pd
from datetime import timedelta
from scripts.common.db_utils import db_manager
from pathlib import Path

def duration_to_seconds(duration_str: str) -> int:
    """Convierte formato HH:mm:ss a total de segundos (timespan)."""
    try:
        if not duration_str or str(duration_str).lower() == "nan":
            return 0
        # Separamos H:M:S
        parts = list(map(int, duration_str.split(':')))
        if len(parts) == 3:
            h, m, s = parts
            return int(timedelta(hours=h, minutes=m, seconds=s).total_seconds())
        return 0
    except Exception:
        return 0

async def process_excel_updates(filename: str):
    current_dir = Path(__file__).parent 
    # Apunta a scripts/data_sources/... según tu estructura
    file_path = current_dir.parent / filename 
    
    if not file_path.exists():
        print(f"❌ No existe el archivo: {file_path}")
        return
    
    db = await db_manager.connect()
    
    try:
        # dtype=str para mantener el formato exacto de HH:mm:ss sin conversiones de pandas
        df = pd.read_excel(file_path, dtype=str)
    except Exception as e:
        print(f"❌ Error al leer Excel: {e}")
        return

    print(f"📊 Procesando {len(df)} registros para actualización de duraciones y estados...")

    # --- 1. ACTUALIZACIÓN DE ÁLBUMES (Es álbum en vivo?) ---
    # Obtenemos álbumes únicos para no saturar la BD con la misma actualización
    unique_albums = df[['Album', 'Es álbum en vivo?']].drop_duplicates(subset=['Album'])
    
    for _, row in unique_albums.iterrows():
        album_name = str(row["Album"]).strip()
        is_live_str = str(row["Es álbum en vivo?"]).strip().upper()
        is_live_bool = True if is_live_str == "SI" else False

        result = await db.albums.update_one(
            {"title": album_name},
            {"$set": {"is_live": is_live_bool}}
        )

        if result.matched_count == 0:
            print(f"❌ ERROR (Album): No se encontró '{album_name}' en la colección albums")
        elif result.modified_count > 0:
            print(f"✅ ALBUM ACTUALIZADO: {album_name} (is_live: {is_live_bool})")

    # --- 2. ACTUALIZACIÓN DE TRACKS (Duración y Segundos) ---
    for _, row in df.iterrows():
        track_name = str(row["Canción"]).strip()
        album_name = str(row["Album"]).strip()
        duration_val = str(row["Duración"]).strip()

        # Buscamos el album para obtener su ID numérico
        album = await db.albums.find_one({"title": album_name})
        if not album:
            # El error de álbum ya se reportó arriba, pasamos al siguiente track
            continue

        album_id = int(album["id"])
        duration_seconds = duration_to_seconds(duration_val)

        # Actualizamos el track con la duración y el timespan optimizado
        result = await db.tracks.update_one(
            {"title": track_name, "album_id": album_id},
            {
                "$set": {
                    "duration": duration_val,
                    "duration_seconds": duration_seconds
                }
            }
        )

        if result.matched_count == 0:
            print(f"❌ ERROR (Track): No se encontró '{track_name}' en el álbum '{album_name}' (ID: {album_id})")
        elif result.modified_count > 0:
            print(f"🎵 TRACK ACTUALIZADO: {track_name} -> {duration_val} ({duration_seconds}s)")

    print("🏁 Proceso de actualización finalizado.")
    await db_manager.close()

if __name__ == "__main__":
    # Asegúrate de que el nombre del archivo coincida con tu carpeta data_sources
    asyncio.run(process_excel_updates("data_sources/santana_master_v2.xlsx"))