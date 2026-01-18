import asyncio
from scripts.common.db_utils import db_manager

async def audit_guest_artist_fields():
    db = await db_manager.connect()

    # Buscamos documentos donde guest_artist_ids existe pero NO es un array
    cursor = db.tracks.find({
        "guest_artist_ids": {
            "$exists": True,
            "$not": {"$type": "array"}
        }
    })

    bad_docs = await cursor.to_list(length=None)

    if not bad_docs:
        print("✅ No se encontraron campos que no sean arrays.")
    else:
        print(f"❌ Se encontraron {len(bad_docs)} documentos con errores:")
        for doc in bad_docs:
            actual_value = doc.get("guest_artist_ids")
            print(
                f"- Canción: {doc.get('title')} | ID: {doc.get('_id')} | Valor actual: {actual_value} (Tipo: {type(actual_value)})")

    await db_manager.close()

async def detect_type_mismatch():
    db = await db_manager.connect()

    pipeline = [
        {
            "$project": {
                "tipo": {"$type": "$guest_artist_ids"},
                "valor": "$guest_artist_ids",
                "title": 1
            }
        },
        {
            "$group": {
                "_id": "$tipo",
                "cantidad": {"$sum": 1},
                "ejemplo_titulo": {"$first": "$title"},
                "ejemplo_valor": {"$first": "$valor"}
            }
        }
    ]
    cursor = db.tracks.aggregate(pipeline)
    results = await cursor.to_list(length=None)

    for res in results:
        print(
            f"Tipo detectado: {res['_id']} | Cantidad: {res['cantidad']} | Ejemplo: {res['ejemplo_titulo']} (Valor: {res['ejemplo_valor']})")


async def run_diagnostic():
    db = await db_manager.connect()

    print("🔍 Iniciando diagnóstico de tipos de datos...")

    pipeline = [
        {
            "$project": {
                "title": 1,
                "guest_artist_type": {"$type": "$guest_artist_ids"},
                "guest_artist_value": "$guest_artist_ids"
            }
        },
        {
            "$group": {
                "_id": "$guest_artist_type",
                "count": {"$sum": 1},
                "examples": {
                    "$push": {
                        "title": "$title",
                        "value": "$guest_artist_value"
                    }
                }
            }
        }
    ]

    results = await db.tracks.aggregate(pipeline).to_list(length=None)

    print("\n--- REPORTE DE TIPOS EN 'guest_artist_ids' ---")
    for res in results:
        tipo = res['_id']
        print(f"\n📌 Tipo detectado: {tipo.upper()}")
        print(f"   Cantidad de documentos: {res['count']}")
        # Mostrar los primeros 3 ejemplos de este tipo
        for example in res['examples'][:3]:
            print(f"   - Ejemplo: '{example['title']}' | Valor actual: {example['value']}")

    print("\n--------------------------------------------")
    await db_manager.close()

if __name__ == "__main__":
    print("Inicia")
    asyncio.run(run_diagnostic())