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

if __name__ == "__main__":
    FILE_PATH = r"D:\Videos\santanarchive\ms-santanarchive-python\scripts\data_sources\Conciertos-Consolidado.xlsx"
    asyncio.run(audit_geography(FILE_PATH))