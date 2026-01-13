# Ejecutar este script para cargar un ejemplo de prueba
import asyncio
import httpx


async def populate():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1") as client:
        # 1. Crear Álbum
        album_data = {
            "id": 1,
            "title": "Abraxas",
            "release_year": 1970,
            "label": "Columbia",
            "producer": "Fred Catero, Santana",
            "tracklist": [
                {"track_number": 1, "title": "Singing Winds, Crying Beasts", "duration": "04:48",
                 "composers": ["Carabello"]},
                {"track_number": 2, "title": "Black Magic Woman", "duration": "05:24", "composers": ["Peter Green"]}
            ]
        }
        await client.post("/albums/", json=album_data)

        # 2. Agregar URL de Portada
        photo_data = {
            "album_id": 1,
            "url": "https://upload.wikimedia.org/wikipedia/en/3/3b/AbraxasAlbumCover.jpg",
            "is_cover": True
        }
        await client.post("/media/album-photos/", json=photo_data)

        print("Datos de prueba cargados!")


if __name__ == "__main__":
    asyncio.run(populate())