# python -m scripts.check_data.check_venue_geography
import asyncio
import pandas as pd
from scripts.common.db_utils import db_manager
from pathlib import Path

async def audit_geography(filename: str):
    current_dir = Path(__file__).parent
    file_path = current_dir.parent / filename
    
    db = await db_manager.connect()
    
    print("📥 Loading geographic masters from DB...")
    
    # 1. Maestros de Países
    countries_data = await db.countries.find().to_list(None)
    countries_db_names = {d['name'].lower().strip(): d['name'] for d in countries_data}
    
    # 2. Maestros de Estados
    states_data = await db.states.find().to_list(None)
    states_db_codes = {d['code'].lower().strip() for d in states_data} # Solo códigos para auditoría rápida
    
    # 3. Maestros de Ciudades
    cities_data = await db.cities.find().to_list(None)
    cities_db_names = [str(d['name']).strip() for d in cities_data]

    try:
        df = pd.read_excel(file_path)
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        return

    # --- CONTENEDORES DE RESULTADOS ---
    countries_not_found = set()
    countries_with_suggestions = []
    
    states_not_found = set()
    
    cities_not_found = set()
    cities_with_suggestions = []

    print(f"🔍 Auditing {len(df)} rows...")

    # --- BLOQUE 0: AUDITORÍA INTERNA DEL EXCEL (Consistencia de Datos) ---
    print("🧐 Checking internal Excel consistency...")
    
    # Agrupamos por ciudad y vemos cuántos países únicos tiene asociados
    excel_city_consistency = df.groupby('Ciudad')['País'].nunique()
    cities_with_multiple_countries_excel = excel_city_consistency[excel_city_consistency > 1].index.tolist()
    
    internal_excel_conflicts = []
    for city in cities_with_multiple_countries_excel:
        countries_in_excel = df[df['Ciudad'] == city]['País'].unique().tolist()
        internal_excel_conflicts.append({
            "city": city,
            "countries": countries_in_excel
        })

    # --- BLOQUE 1: AUDITORÍA DE PAÍSES ---
    unique_countries = df['País'].dropna().unique()
    for p_excel in unique_countries:
        p_clean = str(p_excel).strip()
        p_lower = p_clean.lower()
        if p_lower not in countries_db_names:
            # Buscar similitudes en países
            suggestions = [name for name in countries_db_names.values() if p_lower in name.lower() or name.lower() in p_lower]
            if suggestions:
                countries_with_suggestions.append({"excel": p_clean, "db": suggestions})
            else:
                countries_not_found.add(p_clean)

    # --- BLOQUE 2: AUDITORÍA DE ESTADOS (Solo no vacíos) ---
    # Agrupamos por código y nombre para dar un reporte claro
    unique_states = df[df['Código Estado'].notnull()][['Código Estado', 'Nombre Estado', 'País']].drop_duplicates()
    for _, row in unique_states.iterrows():
        st_code = str(row['Código Estado']).strip()
        st_name = str(row['Nombre Estado']).strip()
        if st_code.lower() not in states_db_codes:
            states_not_found.add(f"[{st_code}] {st_name} (País: {row['País']})")

    # --- BLOQUE 3: AUDITORÍA DE CIUDADES ---
    unique_cities = df[df['Ciudad'].notnull()][['Ciudad', 'País']].drop_duplicates()
    for _, row in unique_cities.iterrows():
        c_excel = str(row['Ciudad']).strip()
        c_lower = c_excel.lower()
        
        exact_match = any(db_n.lower() == c_lower for db_n in cities_db_names)
        if not exact_match:
            suggestions = [db_n for db_n in cities_db_names if c_lower in db_n.lower() or db_n.lower() in c_lower]
            if suggestions:
                cities_with_suggestions.append({"excel": c_excel, "db": list(set(suggestions))[:3], "pais": row['País']})
            else:
                cities_not_found.add(f"{c_excel} (País: {row['País']})")

    # 3. Maestros de Ciudades (Cambiamos a diccionario con mapeo de país)
    cities_data = await db.cities.find().to_list(None)
    # Creamos un mapa: { "nombre_ciudad": [id_pais1, id_pais2] }
    cities_db_map = {}
    for d in cities_data:
        c_name = str(d['name']).strip().lower()
        p_id = d['country_id']
        if c_name not in cities_db_map:
            cities_db_map[c_name] = []
        cities_db_map[c_name].append(p_id)
    
    # Necesitamos también un mapa de Nombres de Países a IDs para comparar con el Excel
    countries_to_id = {d['name'].lower().strip(): d['id'] for d in countries_data}

    # --- BLOQUE 4: CIUDADES CON MISMO NOMBRE PERO DIFERENTE PAÍS ---
    location_conflicts = []
    
    for _, row in unique_cities.iterrows():
        c_excel = str(row['Ciudad']).strip()
        p_excel = str(row['País']).strip().lower()
        c_lower = c_excel.lower()
        
        # Si la ciudad existe en la DB
        if c_lower in cities_db_map:
            excel_country_id = countries_to_id.get(p_excel)
            
            # Si el país del Excel no está en la lista de países que tienen esa ciudad en la DB
            if excel_country_id and excel_country_id not in cities_db_map[c_lower]:
                # Buscamos los nombres de los países que SÍ tienen esa ciudad en la DB para el reporte
                db_countries = [countries_data[next(i for i, x in enumerate(countries_data) if x['id'] == pid)]['name'] 
                               for pid in cities_db_map[c_lower]]
                
                location_conflicts.append({
                    "ciudad": c_excel,
                    "pais_excel": row['País'],
                    "paises_db": db_countries
                })

    # 0. REPORTE DE CONSISTENCIA INTERNA DEL EXCEL
    print(f"\n📑 0. INTERNAL EXCEL CONSISTENCY (Same city in different countries within file):")
    if not internal_excel_conflicts:
        print("   ✅ Excel is internally consistent (1 city = 1 country).")
    else:
        for item in internal_excel_conflicts:
            print(f"   [DUPLICATE CITY NAME] '{item['city']}' is listed in multiple countries: {item['countries']}")

    # --- REPORTE FINAL SEPARADO ---
    print("\n" + "="*70)
    print("📊 INDEPENDENT GEOGRAPHIC AUDIT REPORT")
    print("="*70)

    # 1. REPORTE DE PAÍSES
    print(f"\n🚩 1. COUNTRIES REPORT:")
    if not countries_not_found and not countries_with_suggestions:
        print("   ✅ All countries exist in DB.")
    else:
        for p in sorted(countries_not_found): print(f"   [NEW] {p}")
        for item in countries_with_suggestions:
            print(f"   [SIMILAR] Excel: '{item['excel']}' | DB Sugiere: {item['db']}")

    # 2. REPORTE DE ESTADOS
    print(f"\n🗺️  2. STATES REPORT (Non-empty in Excel):")
    if not states_not_found:
        print("   ✅ All states provided exist in DB.")
    else:
        for s in sorted(states_not_found): print(f"   [NEW/MISSING] {s}")

    # 3. REPORTE DE CIUDADES
    print(f"\n🏙️  3. CITIES REPORT:")
    if not cities_not_found and not cities_with_suggestions:
        print("   ✅ All cities exist in DB.")
    else:
        for c in sorted(cities_not_found): print(f"   [NEW] {c}")
        for item in cities_with_suggestions:
            print(f"   [SIMILAR] Excel: '{item['excel']}' | DB Sugiere: {item['db']} (País: {item['pais']})")

    print("\n" + "="*70)
    await db_manager.close()

    # 4. REPORTE DE CONFLICTOS DE UBICACIÓN
    print(f"\n⚠️  4. LOCATION CONFLICTS (Same city name, different country):")
    if not location_conflicts:
        print("   ✅ No name-country mismatches found.")
    else:
        for item in location_conflicts:
            print(f"   [MISMATCH] City: '{item['ciudad']}' | In Excel: {item['pais_excel']} | In DB exists for: {item['paises_db']}")

if __name__ == "__main__":
    FILE_PATH = r"D:\Videos\santanarchive\ms-santanarchive-python\scripts\data_sources\Conciertos-Consolidado.xlsx"
    asyncio.run(audit_geography(FILE_PATH))