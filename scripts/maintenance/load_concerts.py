#Este script lee el archivo Conciertos-Consolidado y registra (insert/update) los conciertos. Las canciones de conciertos se eliminan y se vuelven a crear según el Excel.
#También, si no existe la ciudad, estado o país, lo registra.
#Ojo: la llave del concert es fecha-hora, nombre del concert, show_type y ciudad

# python -m scripts.maintenance.load_concerts
import pandas as pd
import asyncio
import logging
from datetime import datetime
from scripts.common.db_utils import db_manager

# Configuración de Logs (Punto 10)
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

class ConcertsLoader:
    def __init__(self):
        self.db = None
        self.cache = {}

    async def initialize(self):
        """Inicializa conexión y carga caché en memoria (Punto 7)"""
        self.db = await db_manager.connect()
        collections = [
            'show_types', 'concert_types', 'venue_types', 'tours', 
            'continents', 'countries', 'states', 'cities', 
            'guest_artists_concerts', 'tracks', 'concerts'
        ]
        
        for coll in collections:
            cursor = self.db[coll].find({})
            data = await cursor.to_list(length=None)
            
            if coll == 'tracks':
                self.cache[coll] = {str(d.get('title')).strip().lower(): d.get('id') for d in data}
            elif coll == 'concert':
                # Llave: (fecha_str, venue_name_lower, show_type_id, city_id)
                self.cache[coll] = {
                    (d.get('concert_date_str'), d.get('venue_name').lower(), d.get('show_type_id'), d.get('city_id')): d.get('id') 
                    for d in data if d.get('concert_date_str')
                }
            elif coll == 'cities':
                self.cache[coll] = data
            else:
                name_field = 'name' if coll in ['continents', 'countries', 'states'] else f"{coll[:-1]}_name"
                if coll == 'guest_artists_concerts': name_field = 'guest_artist_name'
                
                if coll == 'guest_artists_concerts':
                    id_field = 'guest_artist_concert_id'
                else:
                    id_field = 'id' if coll in ['continents', 'countries', 'states'] else f"{coll[:-1]}_id"
                
                self.cache[coll] = {
                    str(d.get(name_field)).strip().lower(): d.get(id_field) 
                    for d in data if d.get(name_field)
                }
                
    async def get_next_id(self, counter_name):
        """Usa la colección counters (Punto 11)"""
        counter = await self.db.counters.find_one_and_update(
            {'_id': counter_name},
            {'$inc': {'sequence_value': 1}},
            upsert=True,
            return_document=True
        )
        return counter['sequence_value']

    def normalize(self, text):
        """Aplica trim y minúsculas (Punto 8)"""
        return str(text).strip().lower() if pd.notna(text) else ""

    async def get_or_create_master(self, coll_name, name_val, id_field, name_field, extra_data=None):
        norm_name = self.normalize(name_val)
        if not norm_name: return None
        
        if norm_name in self.cache[coll_name]:
            return self.cache[coll_name][norm_name]
        
        new_id = await self.get_next_id(id_field)
        doc = {id_field: new_id, name_field: str(name_val).strip()}
        if extra_data: doc.update(extra_data)
        
        await self.db[coll_name].insert_one(doc)
        self.cache[coll_name][norm_name] = new_id
        return new_id

    async def process_geo(self, row):
        """Jerarquía Geográfica (Punto 2.4)"""
        cont_id = await self.get_or_create_master('continents', row['Continente'], 'continent_id', 'name')
        country_id = await self.get_or_create_master('countries', row['País'], 'country_id', 'name', {'continent_id': cont_id})
        
        state_id = None
        if pd.notna(row['Código Estado']):
            state_id = await self.get_or_create_master('states', row['Nombre Estado'], 'state_id', 'name', 
                                                     {'code': row['Código Estado'], 'country_id': country_id})
        
        city_name = self.normalize(row['Ciudad'])
        matched_cities = [c for c in self.cache['cities'] if self.normalize(c['name']) == city_name and c.get('country_id') == country_id]
        
        if matched_cities:
            city_id = matched_cities[0]['id']
        else:
            city_id = await self.get_next_id('city_id')
            new_city = {'id': city_id, 'name': str(row['Ciudad']).strip(), 'country_id': country_id, 'state_id': state_id, 'code': None}
            await self.db.cities.insert_one(new_city)
            self.cache['cities'].append(new_city)
        
        return {
            'city_id': city_id,
            'state_id': state_id,
            'country_id': country_id,
            'continent_id': cont_id
        }

    async def run(self, file_path):
        await self.initialize()
        df = pd.read_excel(file_path)
        # Agrupar por la llave de negocio del Excel (Punto 9)
        grouped = df.groupby(['Fecha', 'Venue', 'Tipo de Función', 'Ciudad'], sort=False)

        for name, group in grouped:
            first_row = group.iloc[0]
            
            # Validación de obligatorios (Punto 6)
            required = ['Fecha', 'Venue', 'Tipo de Función', 'Tipo de Concierto', 'Tipo de Lugar', 'Ciudad', 'País', 'Continente']
            if any(pd.isna(first_row[f]) for f in required):
                logger.error(f"⚠️ Campos obligatorios incompletos en: {name}")
                continue

            # Validación de Fecha (Punto 1)
            raw_date = str(first_row['Fecha']).split(' ')[0] # Asegurar solo fecha
            show_time = str(first_row['Hora Función']).strip() if pd.notna(first_row['Hora Función']) else ""
            date_dt = None
            concert_date_str = ""

            raw_val = first_row['Fecha']
            if isinstance(raw_val, datetime):
                date_dt = raw_val
            else:
                raw_date = str(raw_val).strip().split(' ')[0]
                # Intentar varios formatos si es string
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']:
                    try:
                        date_dt = datetime.strptime(raw_date, fmt)
                        break
                    except: continue

            if not date_dt:
                logger.error(f"⚠️ Fecha no reconocida o vacía: {first_row['Fecha']}")
                continue

            # 2. Procesar la hora con tu variable show_time
            h, m, s = 0, 0, 0
            clean_time = "00:00:00" # Valor por defecto
            
            if show_time and ':' in show_time:
                try:
                    parts = show_time.split(':')
                    h = int(parts[0])
                    m = int(parts[1]) if len(parts) > 1 else 0
                    s = int(parts[2]) if len(parts) > 2 else 0
                    clean_time = f"{h:02d}:{m:02d}:{s:02d}"
                except:
                    logger.warning(f"⚠️ Hora mal formateada '{show_time}', usando 00:00:00")

            # 3. Normalizar el objeto final y el string de la llave
            date_dt = date_dt.replace(hour=h, minute=m, second=s, microsecond=0)
            concert_date_str = f"{date_dt.strftime('%Y/%m/%d')} {clean_time}"

            # Obtener IDs de Maestros
            st_id = await self.get_or_create_master('show_types', first_row['Tipo de Función'], 'show_type_id', 'show_type_name')
            ct_id = await self.get_or_create_master('concert_types', first_row['Tipo de Concierto'], 'concert_type_id', 'concert_type_name')
            vt_id = await self.get_or_create_master('venue_types', first_row['Tipo de Lugar'], 'venue_type_id', 'venue_type_name')
            t_id = await self.get_or_create_master('tours', first_row['Tour'], 'tour_id', 'tour_name') if pd.notna(first_row['Tour']) else None
            geo_data = await self.process_geo(first_row)
            city_id = geo_data['city_id']

            # Idempotencia de Concert (Punto 9)
            concert_key = (concert_date_str, self.normalize(first_row['Venue']), st_id, city_id)
            concert_id = self.cache['concerts'].get(concert_key)
            
            if concert_id:
                logger.info(f"✅ Actualizando: {concert_date_str} - {first_row['Venue']}")
                await self.db.concert_songs.delete_many({'concert_id': concert_id})
                
                update_fields = {
                    'venue_type_id': vt_id,
                    'show_type_id': st_id, 
                    'show_time': show_time or None, 
                    'concert_type_id': ct_id,
                    'tour_id': t_id,
                    'state_id': int(geo_data['state_id']) if geo_data['state_id'] is not None else None,
                    'country_id': int(geo_data['country_id']),
                    'continent_id': int(geo_data['continent_id'])
                }
                
                await self.db.concerts.update_one(
                    {'id': concert_id}, 
                    {'$set': update_fields}
                )
            else:
                concert_id = await self.get_next_id('concert_id')
                logger.info(f"🆕 Nuevo: {concert_date_str} - {first_row['Venue']}")
                concert_doc = {
                    'id': concert_id, 
                    'concert_date': date_dt, 
                    'concert_date_str': concert_date_str,
                    'venue_name': str(first_row['Venue']).strip(), 
                    'venue_type_id': vt_id,
                    'show_type_id': st_id, 
                    'show_time': show_time or None, 
                    'concert_type_id': ct_id,
                    'tour_id': t_id, 
                    'city_id': city_id, 
                    'state_id': geo_data['state_id'],
                    'country_id': geo_data['country_id'],
                    'continent_id': geo_data['continent_id'],
                    'concert_year': date_dt.year, 
                    'song_count': 0
                }
                await self.db.concerts.insert_one(concert_doc)
                self.cache['concerts'][concert_key] = concert_id

            # Procesar Canciones (Punto 3)
            songs_to_insert = []
            song_counter = 1
            for _, s_row in group.iterrows():
                if pd.isna(s_row['Canción']): continue
                
                # Guest Artists
                guest_ids = []
                raw_guests = s_row.get('Artista Invitado')
                if pd.notna(raw_guests) and str(raw_guests).strip() != "":
                    for art in str(s_row['Artista Invitado']).split(','):
                        g_id = await self.get_or_create_master('guest_artists_concerts', art.strip(), 'guest_artist_concert_id', 'guest_artist_name')
                        guest_ids.append(g_id)

                # Split de canciones " / " (Punto 3)
                sub_songs = [s.strip() for s in str(s_row['Canción']).split(' / ')]
                for sub_s in sub_songs:
                    t_id_ref = self.cache['tracks'].get(self.normalize(sub_s))
                    songs_to_insert.append({
                        'concert_id': concert_id, 
                        'song_number': song_counter, 
                        'song_name': sub_s,
                        'guest_artist_ids': guest_ids, 
                        'track_ids': [t_id_ref] if t_id_ref else [],
                        'is_cover': str(s_row['Es Cover?']).strip().upper() == 'VERDADERO'
                    })
                    song_counter += 1

            if songs_to_insert:
                await self.db.concert_songs.insert_many(songs_to_insert)
                await self.db.concerts.update_one({'id': concert_id}, {'$set': {'song_count': len(songs_to_insert)}})

        logger.info("🏁 Proceso terminado")

if __name__ == "__main__":
    loader = ConcertsLoader()
    FILE_PATH = r"D:\Videos\santanarchive\ms-santanarchive-python\scripts\data_sources\_test_Conciertos-Consolidado.xlsx"
    asyncio.run(loader.run(FILE_PATH))