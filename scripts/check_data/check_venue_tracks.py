# python -m scripts.check_data.check_venue_tracks
import asyncio
import pandas as pd
import re
from scripts.common.db_utils import db_manager
from pathlib import Path

# Añadimos el parámetro studio_only
async def audit_tracks(filename: str, studio_only: bool = True):
    current_dir = Path(__file__).parent
    # Soporta tanto rutas absolutas como relativas al script
    file_path = Path(filename) if Path(filename).is_absolute() else current_dir.parent / filename
    
    db = await db_manager.connect()
    
    # --- FILTRADO DE TRACKS ---
    print(f"📥 Cargando maestro de Tracks (Studio Only: {studio_only})...")
    
    # Definimos el filtro de búsqueda
    query = {"metadata.is_live": False} if studio_only else {}
    
    tracks_cursor = db.tracks.find(query, {"title": 1, "_id": 0})
    tracks_db = [str(t['title']).strip() for t in await tracks_cursor.to_list(length=None)]
    tracks_db_lower = {t.lower(): t for t in tracks_db}

    try:
        df = pd.read_excel(file_path)
        raw_songs_series = df['Canción'].dropna()
    except Exception as e:
        print(f"❌ Error al leer Excel: {e}")
        return

    # Procesar títulos únicos (Regla de división " / ")
    unique_titles_set = set()
    split_pattern = re.compile(r'\s+/\s+')

    for s in raw_songs_series:
        song_str = str(s).strip()
        if split_pattern.search(song_str):
            parts = [p.strip() for p in split_pattern.split(song_str) if p.strip()]
            unique_titles_set.update(parts)
        else:
            unique_titles_set.add(song_str)

    sorted_unique_titles = sorted(list(unique_titles_set), key=lambda x: x.lower())

    songs_not_found = []
    songs_with_suggestions = []
    perfect_matches = 0

    print(f"🔍 Auditando {len(sorted_unique_titles)} títulos únicos contra {len(tracks_db)} tracks en BD...")

    for song_clean in sorted_unique_titles:
        song_lower = song_clean.lower()

        # 1. Match exacto
        if song_lower in tracks_db_lower:
            perfect_matches += 1
            continue

        # 2. Búsqueda de similitudes
        suggestions = [
            original_title for lower_title, original_title in tracks_db_lower.items() 
            if song_lower in lower_title or lower_title in song_lower
        ]

        if suggestions:
            songs_with_suggestions.append({
                "excel": song_clean,
                "db_suggestions": suggestions
            })
        else:
            songs_not_found.append(song_clean)

    # --- REPORTE ---
    mode_text = "SOLO ESTUDIO" if studio_only else "TODOS (ESTUDIO + LIVE)"
    print("\n" + "="*85)
    print(f"🎵 REPORTE DE CONSISTENCIA DE TRACKS - MODO: {mode_text}")
    print("="*85)
    print(f"✅ Match exacto: {perfect_matches}")
    print(f"⚠️  Con similitudes: {len(songs_with_suggestions)}")
    print(f"❌ Sin coincidencia: {len(songs_not_found)}")
    print("="*85)

    if songs_with_suggestions:
        print("\n❓ SUGERENCIAS (Títulos similares en la base de datos):")
        for item in songs_with_suggestions:
            sugs = " o ".join([f"'{s}'" for s in item['db_suggestions']])
            print(f"   • '{item['excel']}' -> ¿Es en realidad: {sugs}?")

    if songs_not_found:
        print("\n🆕 TRACKS TOTALMENTE NUEVOS O FUERA DE CATEGORÍA:")
        for song in songs_not_found:
            print(f"   • {song}")

    print("\n" + "="*85)
    print(f"TOTAL ANALIZADO: {len(sorted_unique_titles)} canciones únicas.")
    print("="*85)

    await db_manager.close()

if __name__ == "__main__":
    # Ruta al archivo
    FILE_PATH = r"D:\Videos\santanarchive\ms-santanarchive-python\scripts\data_sources\Conciertos-Consolidado.xlsx"
    
    # TRUE: Compara solo contra canciones de álbumes de estudio
    # FALSE: Compara contra absolutamente todos los tracks en la BD
    asyncio.run(audit_tracks(FILE_PATH, studio_only=True))