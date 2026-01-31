#python -m scripts.migrations.seed_venue_types

import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# Configuración del buscador gratuito (OSM)
geolocator = Nominatim(user_agent="santana_venue_mapper")
# Respetamos el límite de 1 consulta por segundo para evitar bloqueos
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.2)

def classify_venue_by_name(name):
    """Filtro rápido basado en el nombre del venue."""
    if not name or pd.isna(name):
        return "Unknown"
        
    name = str(name).lower()
    
    # Educación
    if 'high school' in name: return 'High School'
    if 'university' in name or 'universidad' in name: return 'University'
    if 'college' in name: return 'College'
    
    # Capacidad / Deportes
    if 'stadium' in name or 'estadio' in name: return 'Stadium'
    if 'arena' in name: return 'Arena'
    if 'coliseum' in name: return 'Coliseum'
    if 'amphitheater' in name or 'anfiteatro' in name: return 'Amphitheater'
    
    # Performance
    if 'concert hall' in name: return 'Concert Hall'
    if 'theater' in name or 'theatre' in name or 'teatro' in name: return 'Theatre'
    if 'auditorium' in name or 'auditorio' in name: return 'Auditorium'
    if 'hall' in name: return 'Hall'
    if 'ballroom' in name: return 'Ballroom'
    
    # Locales y TV
    if 'club' in name or 'cafe' in name: return 'Club/Bar'
    if 'tv' in name or 'show' in name: return 'TV Set'
    if 'palace' in name or 'palacio' in name: return 'Palace'
    if 'hotel' in name: return 'Hotel'
    if 'casino' in name: return 'Casino'
    
    # Espacios Públicos
    if 'park' in name: return 'Park'
    if 'square' in name or 'plaza' in name: return 'Square'
    
    return None

def get_venue_type_online(venue_name):
    """Consulta en Internet si el filtro por nombre falló."""
    # 1. Intentamos el filtro rápido
    fast_guess = classify_venue_by_name(venue_name)
    if fast_guess: return fast_guess

    # 2. Si falló, buscamos en OpenStreetMap
    try:
        location = geolocator.geocode(venue_name, addressdetails=True, timeout=10)
        if location and 'address' in location.raw:
            addr = str(location.raw['address']).lower()
            
            # Buscamos en los metadatos de la dirección devuelta
            if 'stadium' in addr or 'sports' in addr: return 'Stadium'
            if 'theatre' in addr or 'arts' in addr: return 'Theatre'
            if 'university' in addr or 'college' in addr: return 'University'
            if 'park' in addr or 'garden' in addr: return 'Park'
            if 'auditorium' in addr: return 'Auditorium'
            if 'hotel' in addr: return 'Hotel'
            if 'cinema' in addr: return 'Theatre'
            
            # Si no hay coincidencia clara, usamos el tipo que OSM asigna al objeto
            return location.raw.get('type', 'Venue').replace('_', ' ').title()
    except Exception:
        pass
    
    return "Venue" # Valor por defecto si no se encontró nada

async def process_excel(input_file, output_file):
    print(f"Reading {input_file}...")
    df = pd.read_excel(input_file)
    
    # Extraemos venues únicos para optimizar (6000 filas -> ~1000 búsquedas reales)
    unique_venues = df['Venue'].unique()
    cache = {}

    print(f"Processing {len(unique_venues)} unique venues...")
    
    for venue in unique_venues:
        # Primero intentamos clasificarlo (el método rápido se ejecuta dentro)
        v_type = get_venue_type_online(venue)
        cache[venue] = v_type
        
        # Solo imprimimos si fue una búsqueda lenta (online)
        source = "(Online)" if not classify_venue_by_name(venue) else "(Fast)"
        print(f"[{source}] {venue} -> {v_type}")
        
        # Pausa solo si fue búsqueda online para cumplir términos de servicio
        if source == "(Online)":
            time.sleep(1.2)

    # Mapeamos los resultados de vuelta a todas las filas del Excel
    df['Venue_Type'] = df['Venue'].map(cache)
    
    df.to_excel(output_file, index=False)
    print(f"--- Process completed! File saved as: {output_file} ---")

if __name__ == "__main__":
    # Cambia estos nombres por tus archivos reales
    import asyncio
    fileName = "Santana_Setlists_2020_2025.xlsx"
    input_xlsx = "D:\Videos\santanarchive\ms-santanarchive-python\scripts\data_sources\data_concerts\\"+fileName
    output_xlsx = "D:\Videos\santanarchive\ms-santanarchive-python\scripts\data_sources\data_concerts\_VENUES_"+fileName
    
    # Nota: Este script no necesita ser async, pero si lo integras en tu app, puede serlo.
    # Aquí lo corremos de forma directa.
    import sys
    try:
        # Para simplificar el ejemplo lo corremos síncrono
        df = pd.read_excel(input_xlsx)
        unique_venues = df['Venue'].unique()
        cache = {}
        for v in unique_venues:
            cache[v] = get_venue_type_online(v)
            print(f"Processed: {v} -> {cache[v]}")
        df['Venue_Type'] = df['Venue'].map(cache)
        df.to_excel(output_xlsx, index=False)
    except Exception as e:
        print(f"Error: {e}")