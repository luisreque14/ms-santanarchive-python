# python -m scripts.check_data.check_geography_venue

import asyncio
import pandas as pd
from scripts.common.db_utils import db_manager
from pathlib import Path

async def audit_geography(filename: str):
    current_dir = Path(__file__).parent
    file_path = current_dir.parent / filename
    
    db = await db_manager.connect()
    
    print("📥 Cargando maestros geográficos actuales...")
    # Cargamos los nombres reales de la DB
    continents_db = {d['name'].lower().strip(): d['name'] for d in await db.continents.find().to_list(None)}
    countries_db = {d['name'].lower().strip(): d['name'] for d in await db.countries.find().to_list(None)}
    states_db = {d['code'].lower().strip(): d['name'] for d in await db.states.find().to_list(None)}
    
    # Para ciudades, guardamos el nombre original para mostrar la sugerencia
    cities_data = await db.cities.find().to_list(None)
    cities_db_names = [str(d['name']).strip() for d in cities_data]

    try:
        df = pd.read_excel(file_path)
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        print(f"❌ Error al leer Excel: {e}")
        return

    new_continents = set()
    new_countries = set()
    new_states = set()
    
    # Reportes específicos para ciudades
    cities_not_found = set()
    cities_with_suggestions = [] # Para casos como "Acapulco" -> "Acapulco, Guerrero"

    print(f"🔍 Auditando {len(df)} filas...")

    grouped = df.groupby(['Fecha', 'Venue', 'Ciudad'])

    for (fecha, venue, ciudad), group in grouped:
        row = group.iloc[0]
        
        cont_name = str(row['Continente']).strip() if row['Continente'] else None
        pais_name = str(row['País']).strip() if row['País'] else None
        estado_code = str(row['Código Estado']).strip() if row['Código Estado'] else None
        ciudad_excel = str(row['Ciudad']).strip() if row['Ciudad'] else None

        # 1. Auditoría de Continente y País (Igual que antes)
        if cont_name and cont_name.lower() not in continents_db:
            new_continents.add(cont_name)
        
        if pais_name and pais_name.lower() not in countries_db:
            new_countries.add(f"{pais_name} ({cont_name})")

        # 2. Auditoría de Ciudad con detección de similitud
        if ciudad_excel:
            ciudad_excel_lower = ciudad_excel.lower()
            # Buscamos match exacto (case-insensitive)
            exact_match = any(c.lower() == ciudad_excel_lower for c in cities_db_names)
            
            if not exact_match:
                # Buscamos sugerencias (si el nombre del Excel está contenido en la DB o viceversa)
                suggestions = [c for c in cities_db_names if ciudad_excel_lower in c.lower() or c.lower() in ciudad_excel_lower]
                
                if suggestions:
                    cities_with_suggestions.append({
                        "excel": ciudad_excel,
                        "db_suggestions": suggestions,
                        "context": f"{pais_name}"
                    })
                else:
                    cities_not_found.add(f"{ciudad_excel} (País: {pais_name})")

    # --- REPORTE DE AUDITORÍA ---
    print("\n" + "="*60)
    print("📊 REPORTE DE CONSISTENCIA GEOGRÁFICA")
    print("="*60)

    # ... (Reporte de continentes y países omitido por brevedad, igual al anterior) ...

    print(f"\n⚠️ CIUDADES CON DIFERENCIAS DE NOMBRE (Similitudes encontradas):")
    print("Estas ciudades NO coinciden exactamente, pero existen nombres parecidos en la DB:")
    
    # Eliminamos duplicados de sugerencias para el reporte
    seen_suggestions = set()
    for item in cities_with_suggestions:
        key = f"{item['excel']}->{tuple(item['db_suggestions'])}"
        if key not in seen_suggestions:
            sug_str = ", ".join([f"'{s}'" for s in item['db_suggestions']])
            print(f"  - En Excel: '{item['excel']}' | En DB existen: {sug_str} (País: {item['context']})")
            seen_suggestions.add(key)

    print(f"\n🏙️ CIUDADES COMPLETAMENTE NUEVAS (Sin similitudes):")
    if cities_not_found:
        for ci in sorted(cities_not_found): print(f"  - {ci}")
    else:
        print("  (Ninguna)")

    print("\n" + "="*60)
    print("💡 RECOMENDACIÓN: Si las 'Similitudes' son la misma ciudad, unifica el nombre")
    print("en el Excel para evitar duplicados antes de correr la migración.")
    print("="*60)

    await db_manager.close()

if __name__ == "__main__":
    FILE_PATH = "D:\Videos\santanarchive\ms-santanarchive-python\scripts\data_sources\Conciertos-Consolidado.xlsx"
    asyncio.run(audit_geography(FILE_PATH))