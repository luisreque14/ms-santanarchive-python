import asyncio
import httpx
import pycountry


def extract_list(response_data, keys=['countries', 'data', 'items']):
    """
    Extrae la lista de datos del JSON de la API, manejando si viene envuelta en un diccionario.
    """
    if isinstance(response_data, list):
        return response_data
    if isinstance(response_data, dict):
        for key in keys:
            if key in response_data:
                return response_data[key]
    return []


async def seed_all_countries():
    base_url = "http://127.0.0.1:8000/api/v1"

    print("--- Cargando todos los países del mundo ---")

    # Obtenemos la lista de todos los países de la librería
    all_countries = list(pycountry.countries)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. PRECARGA: Obtener países existentes para evitar duplicados
        try:
            print("📥 Verificando países ya registrados en la base de datos...")
            # NOTA: Si tu API está paginada, asegúrate de que este GET traiga TODOS
            # o aumenta el límite si tu API lo permite (ej: /countries/?limit=300)
            r_exists = await client.get(f"{base_url}/geography/countries/")

            data = r_exists.json()
            countries_in_db = extract_list(data)

            # Guardamos los nombres en minúsculas en un set para búsqueda rápida
            existing_names = {c['name'].lower() for c in countries_in_db if 'name' in c}
            print(f"✅ Se encontraron {len(existing_names)} países previos en la DB.")
        except Exception as e:
            print(f"⚠️ No se pudo conectar para precarga: {e}")
            existing_names = set()

        # 2. PROCESO DE CARGA
        counter_added = 0
        counter_skipped = 0

        for country in all_countries:
            country_name_lower = country.name.lower()

            # --- VALIDACIÓN DE DUPLICADO ---
            if country_name_lower in existing_names:
                counter_skipped += 1
                continue

            # Usamos ID 0 para que el contador de tu DB asigne el siguiente
            payload = {
                "id": 0,
                "name": country.name,
                "code": country.alpha_2,
                "continent_id": 1
            }

            try:
                response = await client.post(f"{base_url}/geography/countries/", json=payload)
                if response.status_code in [200, 201]:
                    print(f"✅ Nuevo: {country.name}")
                    existing_names.add(country_name_lower)
                    counter_added += 1
                else:
                    # Si el servidor responde error porque ya existe (aunque el set fallara)
                    if "already exists" in response.text.lower():
                        counter_skipped += 1
                    else:
                        print(f"⚠️ Error en {country.name}: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Error de conexión para {country.name}: {e}")

    print("\n" + "=" * 30)
    print("--- Carga masiva finalizada ---")
    print(f"📊 Resumen: {counter_added} nuevos, {counter_skipped} omitidos.")
    print("=" * 30)


if __name__ == "__main__":
    asyncio.run(seed_all_countries())