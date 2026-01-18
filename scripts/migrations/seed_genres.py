import asyncio
from dotenv import load_dotenv

# Importamos tu infraestructura de base de datos
from scripts.common.db_utils import db_manager

load_dotenv()

async def seed_genres():
    db = await db_manager.connect()

    # 2. Lista de géneros únicos (procesada y limpia)
    genres_list = [
        "Acid Rock", "Afro-Cuban Percussion", "Afro-Jazz", "Afro-Latin Rock", "Afro-Pop",
        "Afro-Rock", "Afrobeat", "Alt Rock", "Alternative Latin Rock", "Ambient",
        "AOR", "Avant-garde", "Blues", "Blues Rock", "Boogaloo", "Bossa Nova",
        "Chicano Rock", "Classic Rock", "Classical", "Descarga", "Disco", "EDM",
        "Espiritual", "Experimental", "Experimental Percussion", "Folk Rock", "Funk",
        "Funk Rock", "Fusion", "Gospel", "Guajira", "Guajira-Son", "Hard Rock",
        "Improvisation", "Instrumental Blues", "Instrumental Gospel", "Instrumental Rock",
        "Jam Band", "Jazz", "Jazz Ballad", "Jazz Funk", "Jazz Fusion", "Jazz Pop",
        "Jazz Rock", "Latin EDM", "Latin Hip-Hop", "Latin Jazz", "Latin Pop",
        "Latin Rock", "Mambo", "Melodic Rock", "New Age", "Percussion", "Pop",
        "Pop Rock", "Progressive", "Progressive Rock", "Psychedelia", "Psychedelic Rock",
        "R&B", "Reggae", "Reggae Rock", "Rock & Roll", "Rock Ballad", "Salsa Rock",
        "Samba", "Samba Jazz", "Ska", "Soft Rock", "Smooth Jazz", "Soul",
        "Soul Jazz", "Soul Rock", "Spiritual", "Spiritual Jazz", "Tex-Mex", "World Music"
    ]

    print(f"🚀 Verificando {len(genres_list)} géneros...")

    stats = {"nuevos": 0, "omitidos": 0}

    # 3. Validación y Carga
    for index, name in enumerate(sorted(genres_list)):
        # Buscamos si el nombre ya existe para no repetir
        existing = await db.genres.find_one({"name": name})

        if existing:
            stats["omitidos"] += 1
            continue

        # Si no existe, insertamos con un ID incremental
        new_genre = {
            "id": index + 1,
            "name": name
        }

        await db.genres.insert_one(new_genre)
        stats["nuevos"] += 1
        print(f"  + Registrado: {name}")

    # Resumen y cierre
    print(f"\n✅ Proceso finalizado.")
    print(f"Nuevos: {stats['nuevos']} | Ya existían: {stats['omitidos']}")

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(seed_genres())