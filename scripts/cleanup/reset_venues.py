# python -m scripts.cleanup.reset_venues

import asyncio
import logging
from scripts.common.db_utils import db_manager

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

async def reset_venues():
    try:
        # 1. Conectar a la base de datos
        db = await db_manager.connect()
        logger.info("🔗 Conectado a la base de datos.")

        # 2. Colecciones a vaciar
        collections_to_clear = [
            'guest_artists_venues',
            'venue_songs',
            'venues'
        ]

        for coll in collections_to_clear:
            result = await db[coll].delete_many({})
            logger.info(f"🗑️ Colección '{coll}': {result.deleted_count} documentos eliminados.")

        # 3. Reiniciar secuencias en la colección 'counters'
        # Reseteamos a 0 para que el próximo $inc devuelva 1
        sequences_to_reset = [
            'venue_id',
            'guest_artist_venue_id'
        ]

        for seq in sequences_to_reset:
            result = await db.counters.update_one(
                {'_id': seq},
                {'$set': {'sequence_value': 0}},
                upsert=True
            )
            logger.info(f"🔄 Secuencia '{seq}' reiniciada a 0.")

        logger.info("🏁 Proceso de limpieza y reinicio completado.")

    except Exception as e:
        logger.error(f"❌ Error durante el proceso: {e}")
    finally:
        # Si tu db_manager tiene método de cierre, agrégalo aquí
        pass

if __name__ == "__main__":
    asyncio.run(reset_venues())