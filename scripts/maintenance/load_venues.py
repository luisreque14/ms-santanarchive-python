#Este script lee el archivo Conciertos-Consolidado y registra (insert/update) los conciertos y canciones de conciertos.
#También, si no existe la ciudad, estado o país, lo registra.

# python -m scripts.maintenance.load_venues

import asyncio
import pandas as pd
from datetime import datetime
from scripts.common.db_utils import db_manager
from pathlib import Path
from pymongo import UpdateOne

class SantanaTourMigrator:
    def __init__(self):
        self.caches = {}
        self.counters = {}

    async def _initialize_cache(self, db):
        print("📥 Cargando catálogos en memoria (Case-Insensitive)...")
        # Definimos las colecciones y sus campos clave
        collections_info = [
            ("concert_types", "concert_type_name", "concert_type_id"),
            ("venue_types", "venue_type_name", "venue_type_id"),
            ("tours", "tour_name", "tour_id"),
            ("continents", "name", "id"),
            ("countries", "name", "id"),
            ("states", "code", "id"),
            ("cities", "name", "id"),
            ("guest_artists_venues", "guest_artist_name", "guest_artist_venue_id"),
            ("tracks", "title", "id")
        ]

        for coll, name_field, id_field in collections_info:
            data = await db[coll].find().to_list(length=None)
            # Cache: Llave en minúsculas para comparaciones del punto 7
            self.caches[coll] = {str(d[name_field]).strip().lower(): d[id_field] for d in data if name_field in d}
            # Contador: Para nuevos IDs correlativos
            self.counters[id_field] = max([int(d[id_field]) for d in data if id_field in d] + [0])

        # Cache especial para Venues (Idempotencia: Fecha_Venue_CiudadID)
        venues_data = await db.venues.find().to_list(length=None)
        self.caches["venues"] = {
            f"{d['venue_date']}_{str(d['venue_name']).lower()}_{d['city_id']}": True 
            for d in venues_data
        }

    def get_next_id(self, counter_name):
        self.counters[counter_name] += 1
        return self.counters[counter_name]

    async def get_or_create(self, db, coll, cache_name, search_val, id_field, name_field, extra_data=None):
        if not search_val or pd.isna(search_val): return None
        val_clean = str(search_val).strip()
        val_key = val_clean.lower()

        if val_key in self.caches[cache_name]:
            return self.caches[cache_name][val_key]

        new_id = self.get_next_id(id_field)
        doc = {id_field: new_id, name_field: val_clean}
        if extra_data: doc.update(extra_data)
        
        await db[coll].insert_one(doc)
        self.caches[cache_name][val_key] = new_id
        print(f"✨ Nuevo registro en {coll}: {val_clean} (ID: {new_id})")
        return new_id

    async def process_ubigeo(self, db, row):
        # 1. Continente (Asumimos que ya existen los básicos)
        cont_key = str(row['Continente']).strip().lower()
        cont_id = self.caches['continents'].get(cont_key)

        # 2. País
        country_name = str(row['País']).strip()
        country_id = self.caches['countries'].get(country_name.lower())
        if not country_id:
            country_id = await self.get_or_create(db, "countries", "countries", country_name, "id", "name", {
                "continent_id": cont_id, "code": None
            })

        # 3. Estado (Solo si hay código)
        state_id = None
        state_code = str(row['Código Estado']).strip() if row['Código Estado'] else None
        if state_code:
            # Según punto 1.4.2: buscar por código
            state_id = self.caches['states'].get(state_code.lower())
            if not state_id:
                state_id = await self.get_or_create(db, "states", "states", state_code, "id", "code", {
                    "name": row['Nombre Estado'], "country_id": country_id
                })

        # 4. Ciudad
        city_name = str(row['Ciudad']).strip()
        city_id = self.caches['cities'].get(city_name.lower())
        if not city_id:
            city_id = await self.get_or_create(db, "cities", "cities", city_name, "id", "name", {
                "state_id": state_id, "country_id": country_id, "code": None
            })
        return city_id

async def run_migration(filename: str):
    current_dir = Path(__file__).parent
    file_path = current_dir.parent / filename
    
    migrator = SantanaTourMigrator()
    db = await db_manager.connect()
    await migrator._initialize_cache(db)

    print(f"📊 Leyendo {file_path}...")
    df = pd.read_excel(file_path)
    df = df.where(pd.notnull(df), None)

    # Agrupar por la llave de concierto para procesar el "Paso 1" una sola vez por show
    grouped = df.groupby(['Fecha', 'Venue', 'Ciudad'])
    song_ops = []

    for (fecha, venue_name, ciudad), group in grouped:
        first = group.iloc[0]
        
        # Validaciones obligatorias (Paso 5)
        required = ["Fecha", "Venue", "Tipo de Concierto", "Tipo de Lugar", "País", "Continente"]
        missing = [f for f in required if not first[f]]
        if missing:
            print(f"❌ SALTADO: Faltan campos obligatorios {missing} en {fecha} | {venue_name}")
            continue

        # Convertir fecha
        dt_fecha = pd.to_datetime(fecha, dayfirst=True)

        # 1. Ubigeo y Referencias
        city_id = await migrator.process_ubigeo(db, first)
        ct_id = await migrator.get_or_create(db, "concert_types", "concert_types", first["Tipo de Concierto"], "concert_type_id", "concert_type_name")
        vt_id = await migrator.get_or_create(db, "venue_types", "venue_types", first["Tipo de Lugar"], "venue_type_id", "venue_type_name")
        t_id = await migrator.get_or_create(db, "tours", "tours", first["Tour"], "tour_id", "tour_name") if first["Tour"] else None

        # 2. Registro de Venue (Paso 1.6 e Idempotencia Paso 8)
        venue_key = f"{dt_fecha}_{str(venue_name).lower()}_{city_id}"
        
        # En MongoDB, si no tienes un campo 'id' correlativo manual para venues, 
        # lo buscamos por el filtro de la llave compuesta.
        existing_venue = await db.venues.find_one({
            "venue_date": dt_fecha, 
            "venue_name": str(venue_name).strip(), 
            "city_id": city_id
        })

        if not existing_venue:
            # Calculamos song_count basado en las canciones no vacías del grupo
            songs_in_group = group[group['Canción'].notnull()]
            venue_doc = {
                "venue_date": dt_fecha,
                "venue_year": int(dt_fecha.year),
                "venue_name": str(venue_name).strip(),
                "venue_type_id": vt_id,
                "concert_type_id": ct_id,
                "tour_id": t_id,
                "city_id": city_id,
                "song_count": len(songs_in_group)
            }
            res = await db.venues.insert_one(venue_doc)
            venue_oid = res.inserted_id
            print(f"🏟️ Venue Registrado: {venue_name} ({dt_fecha.year})")
        else:
            venue_oid = existing_venue["_id"]

        # 3. Registro de Canciones (Paso 2)
        for _, s_row in group.iterrows():
            if not s_row["Canción"]: continue

            # Artistas invitados (Split por coma)
            g_ids = []
            if s_row["Artista Invitado"]:
                names = [n.strip() for n in str(s_row["Artista Invitado"]).split(",")]
                for n in names:
                    gid = await migrator.get_or_create(db, "guest_artists_venues", "guest_artists_venues", n, "guest_artist_venue_id", "guest_artist_name")
                    g_ids.append(gid)

            # Búsqueda en Tracks (Split por /)
            track_ids = []
            song_parts = [p.strip().lower() for p in str(s_row["Canción"]).split("/")]
            for part in song_parts:
                tid = migrator.caches["tracks"].get(part)
                if tid: track_ids.append(tid)

            song_doc = {
                "venue_id": venue_oid, # Usamos el _id de Mongo para la relación interna
                "song_name": str(s_row["Canción"]).strip(),
                "guest_artist_ids": g_ids,
                "track_ids": track_ids,
                "is_cover": True if str(s_row["Es Cover?"]).upper() == "SI" else False
            }

            # UpdateOne con upsert para evitar duplicar canciones si se re-ejecuta el script
            song_ops.append(UpdateOne(
                {"venue_id": venue_oid, "song_name": song_doc["song_name"]},
                {"$set": song_doc},
                upsert=True
            ))

        # Bulk write cada 500 canciones para optimizar red
        if len(song_ops) >= 500:
            await db.venue_songs.bulk_write(song_ops)
            song_ops = []

    if song_ops:
        await db.venue_songs.bulk_write(song_ops)

    print("🏁 Migración finalizada.")
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(run_migration("data_sources/data_concerts/Conciertos-Consolidado.xlsx"))