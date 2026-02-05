# python -m scripts.check_data.check_venue_detect_double_shows

import asyncio
import pandas as pd
import re
from pathlib import Path

async def detect_double_shows(filename: str):
    current_dir = Path(__file__).parent
    file_path = current_dir.parent / filename
    
    try:
        df = pd.read_excel(file_path)
        # Convertir y limpiar fechas
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Fecha'])
    except Exception as e:
        print(f"❌ Error al leer Excel: {e}")
        return

    # Filtro estricto de años: 1969 a 1979
    mask = (df['Fecha'].dt.year >= 1969) & (df['Fecha'].dt.year <= 1979)
    df_filtered = df[mask].copy()

    # Patrón de split: "/" rodeado de espacios
    split_pattern = re.compile(r'\s+/\s+')

    def count_total_songs(series):
        total = 0
        for val in series.dropna():
            val_str = str(val).strip()
            if split_pattern.search(val_str):
                total += len(split_pattern.split(val_str))
            else:
                total += 1
        return total

    # Agrupación por Fecha, Ciudad y Venue (para mayor precisión)
    stats = df_filtered.groupby(['Fecha', 'Ciudad', 'Venue'])['Canción'].apply(count_total_songs).reset_index()

    # Filtrar solo los que tienen más de 20 canciones
    suspicious_days = stats[stats['Canción'] > 20].sort_values(by='Fecha')

    print("\n" + "="*75)
    print(f"🕵️  AUDITORÍA DE SETLISTS LARGOS / DOBLE SHOWS (1969 - 1979)")
    print("="*75)
    print(f"{'FECHA':<12} | {'CIUDAD':<20} | {'CANCIONES':<10} | {'VENUE'}")
    print("-" * 75)

    if suspicious_days.empty:
        print("No se encontraron registros que superen las 20 canciones en este periodo.")
    else:
        for _, row in suspicious_days.iterrows():
            fecha_str = row['Fecha'].strftime('%Y/%m/%d')
            venue_short = str(row['Venue'])[:30] # Cortamos el nombre si es muy largo
            print(f"{fecha_str:<12} | {row['Ciudad']:<20} | {row['Canción']:<10} | {venue_short}")

    print("-" * 75)
    print(f"TOTAL DE CASOS ENCONTRADOS: {len(suspicious_days)}")
    print("="*75)
    print("💡 Nota: Si el número es cercano a 40, es casi seguro un Early & Late Show mezclado.")

if __name__ == "__main__":
    FILE_PATH = "D:\Videos\santanarchive\ms-santanarchive-python\scripts\data_sources\Conciertos-Consolidado.xlsx"
    asyncio.run(detect_double_shows(FILE_PATH))