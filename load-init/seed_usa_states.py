import asyncio
import httpx
import us


async def seed_usa_states():
    BASE_URL = "http://127.0.0.1:8000/api/v1/geography/states/"
    USA_COUNTRY_ID = 235  # Cambiado al ID que actualizaste recientemente

    print("📥 Consultando estados existentes para evitar duplicados...")

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            # 1. Obtener estados actuales de la DB
            response_exists = await client.get(BASE_URL)
            if response_exists.status_code == 200:
                data = response_exists.json()
                # Usamos la misma lógica de extracción robusta por si viene en 'data' o 'items'
                if isinstance(data, dict):
                    data = data.get('states', data.get('data', data.get('items', [])))

                # Guardamos solo los nombres en minúsculas para comparar fácil
                existing_names = {s['name'].lower() for s in data if 'name' in s}
            else:
                existing_names = set()
                print("⚠️ No se pudieron precargar estados existentes, se intentará carga directa.")
        except Exception as e:
            print(f"⚠️ Error al conectar con la API: {e}")
            return

        # 2. Iniciar proceso de carga
        all_usa_states = us.states.STATES
        print(f"🚀 Procesando {len(all_usa_states)} estados de la librería...")

        for state in all_usa_states:
            # --- VALIDACIÓN ---
            if state.name.lower() in existing_names:
                print(f"⏭️  Saltando: {state.name} (Ya existe en la DB)")
                continue

            payload = {
                "name": state.name,
                "code": state.abbr,
                "country_id": USA_COUNTRY_ID
            }

            try:
                response = await client.post(BASE_URL, json=payload)

                if response.status_code in [200, 201]:
                    print(f"✅ {state.abbr}: {state.name} cargado correctamente.")
                    # Añadimos al set por si hay duplicados en la fuente (poco probable con 'us')
                    existing_names.add(state.name.lower())
                else:
                    print(f"❌ Error en {state.abbr}: {response.status_code} - {response.text}")

                await asyncio.sleep(0.05)

            except Exception as e:
                print(f"🔥 Error de conexión al procesar {state.name}: {e}")

    print("\n✨ Proceso de carga finalizado.")


if __name__ == "__main__":
    asyncio.run(seed_usa_states())