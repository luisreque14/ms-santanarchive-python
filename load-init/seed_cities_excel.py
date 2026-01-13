import pandas as pd
import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1/geography"


async def get_iata_code(client, city_name, country_name):
    """Busca el código IATA mediante Travelpayouts."""
    try:
        search_url = f"https://autocomplete.travelpayouts.com/places2?term={city_name}&locale=en&types[]=city"
        response = await client.get(search_url)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                for result in data:
                    if result.get('country_name', '').lower() == country_name.lower():
                        return result.get('code')
    except Exception as e:
        print(f"⚠️ Error buscando IATA para {city_name}: {e}")
    return city_name[:3].upper()


def extract_list(response_data):
    """Extrae la lista de datos del JSON de la API."""
    if isinstance(response_data, list):
        return response_data
    if isinstance(response_data, dict):
        for key in ['cities', 'data', 'items', 'results', 'states', 'countries']:
            if key in response_data:
                return response_data[key]
    return []


async def seed_cities_from_excel():
    try:
        df = pd.read_excel("ciudades.xlsx")
    except Exception as e:
        print(f"🔥 Error al abrir el archivo Excel: {e}")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("📥 Iniciando precarga de seguridad...")

        # 1. Cargar Países
        r_countries = await client.get(f"{BASE_URL}/countries/?limit=500")
        countries_map = {c['name'].lower(): c['id'] for c in extract_list(r_countries.json()) if 'name' in c}

        # 2. Cargar Estados
        r_states = await client.get(f"{BASE_URL}/states/?limit=2000")
        states_map = {(s['code'], s['country_id']): s['id'] for s in extract_list(r_states.json()) if 'code' in s}

        # 3. Cargar Ciudades existentes para evitar duplicados
        r_cities = await client.get(f"{BASE_URL}/cities/?limit=20000")
        existing_cities = {
            (c['name'].lower(), c.get('state_id'), c['country_id'])
            for c in extract_list(r_cities.json())
            if 'name' in c
        }

        print(f"✅ Caché cargada. Procesando {len(df)} filas...")

        counter_ok = 0
        counter_skip = 0
        counter_no_country = 0

        for index, row in df.iterrows():
            # Validación obligatoria: Ciudad y País
            if pd.isna(row['Ciudad']) or pd.isna(row['Pais']):
                continue

            city_name = str(row['Ciudad']).strip()
            country_name = str(row['Pais']).strip()

            # Validación opcional: Estado
            state_code = str(row['Estado']).strip() if pd.notna(row['Estado']) else None

            # 1. Buscar Country ID (Obligatorio)
            country_id = countries_map.get(country_name.lower())
            if not country_id:
                print(f"❌ Fila {index}: País '{country_name}' no existe en DB. Saltando.")
                counter_no_country += 1
                continue

            # 2. Buscar State ID (Opcional)
            state_id = None
            if state_code:
                state_id = states_map.get((state_code, country_id))
                if not state_id:
                    print(f"⚠️ Fila {index}: Estado '{state_code}' no encontrado. Se registrará solo con País.")

            # 3. Verificar Duplicados (Nombre + Estado + País)
            if (city_name.lower(), state_id, country_id) in existing_cities:
                counter_skip += 1
                continue

            # 4. Registro
            iata_code = await get_iata_code(client, city_name, country_name)
            payload = {
                "id": 0,
                "country_id": country_id,
                "state_id": state_id,  # Puede ser None/null
                "code": iata_code,
                "name": city_name
            }

            try:
                response = await client.post(f"{BASE_URL}/cities/", json=payload)
                if response.status_code in [200, 201]:
                    existing_cities.add((city_name.lower(), state_id, country_id))
                    counter_ok += 1
                    loc = f"{state_code if state_code else 'N/A'}, {country_name}"
                    print(f"✅ Registrada: {city_name} ({loc})")
                else:
                    print(f"⚠️ Error en {city_name}: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"🔥 Error de red en fila {index}: {e}")

    print("\n" + "=" * 30)
    print(f"🏁 RESUMEN FINAL")
    print(f"   - Registradas: {counter_ok}")
    print(f"   - Duplicadas omitidas: {counter_skip}")
    print(f"   - Sin país en DB: {counter_no_country}")
    print("=" * 30)


if __name__ == "__main__":
    asyncio.run(seed_cities_from_excel())