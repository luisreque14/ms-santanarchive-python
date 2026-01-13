import asyncio
import httpx


async def seed_canada():
    BASE_URL = "http://127.0.0.1:8000/api/v1/geography/states/"
    CANADA_COUNTRY_ID = 40

    provinces = [
        {"name": "Alberta", "code": "AB"},
        {"name": "British Columbia", "code": "BC"},
        {"name": "Manitoba", "code": "MB"},
        {"name": "New Brunswick", "code": "NB"},
        {"name": "Newfoundland and Labrador", "code": "NL"},
        {"name": "Nova Scotia", "code": "NS"},
        {"name": "Ontario", "code": "ON"},
        {"name": "Prince Edward Island", "code": "PE"},
        {"name": "Quebec", "code": "QC"},
        {"name": "Saskatchewan", "code": "SK"},
        {"name": "Northwest Territories", "code": "NT"},
        {"name": "Nunavut", "code": "NU"},
        {"name": "Yukon", "code": "YT"}
    ]

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. PRECARGA: Obtener los estados que YA están en la base de datos
        print("📥 Verificando estados existentes en la base de datos...")
        try:
            r_exists = await client.get(BASE_URL)
            data = r_exists.json()

            # Manejamos si la respuesta viene envuelta en un diccionario
            if isinstance(data, dict):
                data = data.get('states', data.get('data', data.get('items', [])))

            # Guardamos los nombres existentes en minúsculas para comparar
            existing_names = {s['name'].lower() for s in data if 'name' in s}
            print(f"✅ Se encontraron {len(existing_names)} estados en total en la DB.")
        except Exception as e:
            print(f"⚠️ No se pudo precargar la lista de estados: {e}")
            existing_names = set()

        print(f"🇨🇦 Iniciando validación y carga para Canadá...")

        for prov in provinces:
            # 2. VALIDACIÓN: Si el nombre ya existe en la DB, lo saltamos
            if prov["name"].lower() in existing_names:
                print(f"⏭️  Saltando: {prov['name']} (Ya existe)")
                continue

            payload = {
                "name": prov["name"],
                "code": prov["code"],
                "country_id": CANADA_COUNTRY_ID
            }

            try:
                response = await client.post(BASE_URL, json=payload)
                if response.status_code in [200, 201]:
                    print(f"✅ Registrado: {prov['name']} ({prov['code']})")
                    existing_names.add(prov["name"].lower())  # Evita duplicar si el script corre dos veces
                else:
                    print(f"❌ Error en {prov['name']}: {response.status_code}")
            except Exception as e:
                print(f"🔥 Error al procesar {prov['name']}: {e}")

    print("\n✨ Proceso de Canadá finalizado.")


if __name__ == "__main__":
    asyncio.run(seed_canada())