import asyncio
from scripts.common.db_utils import db_manager

async def audit_collaborator_fields():
    db = await db_manager.connect()

    # Buscamos documentos donde collaborator_ids existe pero NO es un array
    cursor = db.tracks.find({
        "collaborator_ids": {
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
            actual_value = doc.get("collaborator_ids")
            print(
                f"- Canción: {doc.get('title')} | ID: {doc.get('_id')} | Valor actual: {actual_value} (Tipo: {type(actual_value)})")

    await db_manager.close()

async def detect_type_mismatch():
    db = await db_manager.connect()

    pipeline = [
        {
            "$project": {
                "tipo": {"$type": "$collaborator_ids"},
                "valor": "$collaborator_ids",
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
                "collab_type": {"$type": "$collaborator_ids"},
                "collab_value": "$collaborator_ids"
            }
        },
        {
            "$group": {
                "_id": "$collab_type",
                "count": {"$sum": 1},
                "examples": {
                    "$push": {
                        "title": "$title",
                        "value": "$collab_value"
                    }
                }
            }
        }
    ]

    results = await db.tracks.aggregate(pipeline).to_list(length=None)

    print("\n--- REPORTE DE TIPOS EN 'collaborator_ids' ---")
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