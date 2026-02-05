#Este script lee el archivo Conciertos-Consolidado y registra (insert/update) los conciertos. Las canciones de conciertos se eliminan y se vuelven a crear según el Excel.
#También, si no existe la ciudad, estado o país, lo registra.
#Ojo: la llave del venue es fecha-hora, nombre del venue, show_type y ciudad

# python -m scripts.maintenance.load_venues
import pandas as pd
import asyncio
import logging
from datetime import datetime
from scripts.common.db_utils import db_manager

# Configuración de Logs (Punto 10)
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

class VenuesLoader:
    def __init__(self):
        self.db = None
        self.cache = {}

    async def initialize(self):
        """Inicializa conexión y carga caché en memoria (Punto 7)"""
        self.db = await db_manager.connect()
        collections = [
            'show_types', 'concert_types', 'venue_types', 'tours', 
            'continents', 'countries', 'states', 'cities', 
            'guest_artists_venues', 'tracks', 'venues'
        ]
        
        for coll in collections:
            cursor = self.db[coll].find({})
            data = await cursor.to_list(length=None)
            
            if coll == 'tracks':
                self.cache[coll] = {str(d.get('title')).strip().lower(): d.get('id') for d in data}
            elif coll == 'venues':
                # Llave: (fecha_str, venue_name_lower, show_type_id, city_id)
                self.cache[coll] = {
                    (d.get('venue_date_str'), d.get('venue_name').lower(), d.get('show_type_id'), d.get('city_id')): d.get('id') 
                    for d in data
                }
            elif coll == 'cities':
                self.cache[coll] = data
            else:
                name_field = 'name' if coll in ['continents', 'countries', 'states'] else f"{coll[:-1]}_name"
                if coll == 'guest_artists_venues': name_field = 'guest_artist_name'
                self.cache[coll] = {str(d.get(name_field)).strip().lower(): d.get('id') or d.get(f"{coll[:-1]}_id") for d in data}

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
            return matched_cities[0]['id']
        else:
            city_id = await self.get_next_id('city_id')
            new_city = {'id': city_id, 'name': str(row['Ciudad']).strip(), 'country_id': country_id, 'state_id': state_id, 'code': None}
            await self.db.cities.insert_one(new_city)
            self.cache['cities'].append(new_city)
            return city_id

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
            venue_date_str = ""

            try:
                for fmt in ['%Y/%m/%d', '%d/%m/%Y', '%Y-%m-%d']:
                    try: 
                        date_dt = datetime.strptime(raw_date, fmt)
                        break
                    except: continue
                if not date_dt: raise ValueError
                
                # Formateo de fecha y hora
                if show_time:
                    try:
                        # Soporta formatos como HH:MM o HH:MM:SS
                        time_parts = show_time.split(':')
                        date_dt = date_dt.replace(
                            hour=int(time_parts[0]), 
                            minute=int(time_parts[1]),
                            second=int(time_parts[2]) if len(time_parts) > 2 else 0
                        )
                    except:
                        logger.warning(f"⚠️ Hora mal formateada '{show_time}', se usará 00:00:00")
                
                venue_date_str = date_dt.strftime('%Y/%m/%d %H:%M:%S')
            except:
                logger.error(f"⚠️ Fecha incorrecta: {raw_date}")
                continue

            # Obtener IDs de Maestros
            st_id = await self.get_or_create_master('show_types', first_row['Tipo de Función'], 'show_type_id', 'show_type_name')
            ct_id = await self.get_or_create_master('concert_types', first_row['Tipo de Concierto'], 'concert_type_id', 'concert_type_name')
            vt_id = await self.get_or_create_master('venue_types', first_row['Tipo de Lugar'], 'venue_type_id', 'venue_type_name')
            t_id = await self.get_or_create_master('tours', first_row['Tour'], 'tour_id', 'tour_name') if pd.notna(first_row['Tour']) else None
            city_id = await self.process_geo(first_row)

            # Idempotencia de Venue (Punto 9)
            venue_key = (date_dt.strftime('%Y/%m/%d'), self.normalize(first_row['Venue']), st_id, city_id)
            venue_id = self.cache['venues'].get(venue_key)
            
            if venue_id:
                logger.info(f"✅ Actualizando: {venue_date_str} - {first_row['Venue']}")
                await self.db.venue_songs.delete_many({'venue_id': venue_id})
            else:
                venue_id = await self.get_next_id('venue_id')
                logger.info(f"🆕 Nuevo: {venue_date_str} - {first_row['Venue']}")
                venue_doc = {
                    'id': venue_id, 
                    'venue_date': date_dt, 
                    'venue_name': str(first_row['Venue']).strip(), 
                    'venue_type_id': vt_id,
                    'show_type_id': st_id, 
                    'show_time': show_time or None, 
                    'concert_type_id': ct_id,
                    'tour_id': t_id, 
                    'city_id': city_id, 
                    'venue_year': date_dt.year, 
                    'song_count': 0
                }
                await self.db.venues.insert_one(venue_doc)
                self.cache['venues'][venue_key] = venue_id

            # Procesar Canciones (Punto 3)
            songs_to_insert = []
            song_counter = 1
            for _, s_row in group.iterrows():
                if pd.isna(s_row['Canción']): continue
                
                # Guest Artists
                guest_ids = []
                if pd.notna(s_row['Artista Invitado']):
                    for art in str(s_row['Artista Invitado']).split(','):
                        g_id = await self.get_or_create_master('guest_artists_venues', art.strip(), 'guest_artist_venue_id', 'guest_artist_name')
                        guest_ids.append(g_id)

                # Split de canciones " / " (Punto 3)
                sub_songs = [s.strip() for s in str(s_row['Canción']).split(' / ')]
                for sub_s in sub_songs:
                    t_id_ref = self.cache['tracks'].get(self.normalize(sub_s))
                    songs_to_insert.append({
                        'venue_id': venue_id, 'song_number': song_counter, 'song_name': sub_s,
                        'guest_artist_ids': guest_ids, 'track_ids': [t_id_ref] if t_id_ref else [],
                        'is_cover': str(s_row['Es Cover?']).strip().upper() == 'VERDADERO'
                    })
                    song_counter += 1

            if songs_to_insert:
                await self.db.venue_songs.insert_many(songs_to_insert)
                await self.db.venues.update_one({'id': venue_id}, {'$set': {'song_count': len(songs_to_insert)}})

        logger.info("🏁 Proceso terminado")

if __name__ == "__main__":
    loader = VenuesLoader()
    FILE_PATH = r"D:\Videos\santanarchive\ms-santanarchive-python\scripts\data_sources\_test_Conciertos-Consolidado.xlsx"
    asyncio.run(loader.run(FILE_PATH))