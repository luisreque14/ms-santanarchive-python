import asyncio
import os
import requests
import urllib.parse
import re
from scripts.common.db_utils import db_manager

FRONTEND_PUBLIC_PATH = "../frontend/public/images/albums"

if not os.path.exists(FRONTEND_PUBLIC_PATH):
    os.makedirs(FRONTEND_PUBLIC_PATH)

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text).strip('-')
    return text


async def descargar_imagenes_atlas():
    # Conexión a MongoDB Atlas
    db = await db_manager.connect()

    print("☁️ Conectado a MongoDB Atlas...")

    try:
        # Obtenemos los álbumes
        albums = await db.albums.find().to_list(length=None)
        print(f"🔎 Procesando {len(albums)} álbumes desde la nube...")

        for album in albums:
            title = album.get('title')
            # Usamos el _id o un campo id para el filtro de actualización
            query_filter = {"_id": album['_id']}

            # Buscar en iTunes
            search_query = urllib.parse.quote(f"Santana {title}")
            search_url = f"https://itunes.apple.com/search?term={search_query}&entity=album&limit=1"

            try:
                res = requests.get(search_url).json()
                if res['resultCount'] > 0:
                    img_url = res['results'][0]['artworkUrl100'].replace('100x100bb', '600x600bb')

                    # Nombre SEO
                    filename = f"{slugify(title + '-santana')}.jpg"
                    save_path = os.path.join(FRONTEND_PUBLIC_PATH, filename)

                    # Descargar y guardar en local (frontend)
                    img_data = requests.get(img_url).content
                    with open(save_path, 'wb') as f:
                        f.write(img_data)

                    # Actualizar la ruta en la nube
                    db_path = f"{filename}"#/images/albums/
                    await db.albums.update_one(
                        query_filter,
                        {"$set": {"cover": db_path}}
                    )
                    print(f"✅ Actualizado en nube y guardado local: {filename}")
                else:
                    print(f"⚠️ Portada no encontrada: {title}")

            except Exception as e:
                print(f"❌ Error descargando {title}: {e}")

    finally:
        await db_manager.close()
        print("\n✨ Proceso finalizado en la nube.")


if __name__ == "__main__":
    asyncio.run(descargar_imagenes_atlas())