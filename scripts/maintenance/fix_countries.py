import asyncio
import httpx
from scripts.common.db_utils import db_manager

# Mapeo según los IDs que ya tengas en tu colección de continentes
CONTINENT_MAP = {
    "Africa": 3,
    "Americas": 1,
    "Asia": 4,
    "Europe": 2,
    "Oceania": 5,
    "Antarctic": 6
}


async def run_enrichment():
    db = await db_manager.connect()

    # 1. Obtenemos los países
    print(f"📡 Conectando a MongoDB Atlas...")
    countries_cursor = db.countries.find({})
    countries = await countries_cursor.to_list(length=None)
    print(f"📦 Se encontraron {len(countries)} países para procesar.\n")

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        for country in countries:
            name = country.get("name")
            if not name: continue

            try:
                # 2. Consultar Servicio de Geografía (REST Countries)
                # Usamos el nombre para buscar el continente
                response = await http_client.get(f"https://restcountries.com/v3.1/name/{name}?fullText=true")

                if response.status_code == 200:
                    api_data = response.json()[0]
                    region = api_data.get("region")  # Ejemplo: "Europe"

                    continent_id = CONTINENT_MAP.get(region)

                    if continent_id:
                        # 3. Actualizar documento en la nube
                        # Usamos 'id' numérico según tu CountrySchema
                        result = await db.countries.update_one(
                            {"id": country["id"]},
                            {"$set": {"continent_id": continent_id}}
                        )

                        if result.modified_count > 0:
                            print(f"✅ {name:20} -> {region} (Actualizado)")
                        else:
                            print(f"ℹ️ {name:20} -> {region} (Ya estaba correcto)")
                    else:
                        print(f"⚠️ {name:20} -> Región '{region}' no mapeada")
                else:
                    print(f"❌ {name:20} -> No encontrado en API")

            except Exception as e:
                print(f"🔥 Error procesando {name}: {str(e)}")

            # Respetar límites de la API gratuita
            await asyncio.sleep(0.3)

    print("\n✨ Proceso completado en la nube.")
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(run_enrichment())