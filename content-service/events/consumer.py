import asyncio
import json
import aio_pika
from pathlib import Path
from aio_pika.abc import AbstractIncomingMessage
from infrastructure.db.connection import AsyncSessionLocal
from core.repositories.album_repository import AlbumRepository
from core.services.album_service import AlbumService
from core.services.artist_lookup import ArtistLookupService
from config import settings


def create_artist_folder_structure(artist_id: str, album_id: int) -> None:
    """
    Crea la estructura de carpetas para el artista y el álbum:
    {CONTENT_BASE_PATH}/
    └── {artist_id}/
        ├── utils/
        └── {album_id}/
    """
    try:
        # 🔹 USAR PATH CENTRALIZADO DESDE CONFIG
        storage_path = settings.storage_path

        # Carpeta del artista
        artist_folder = storage_path / str(artist_id)
        artist_folder.mkdir(parents=True, exist_ok=True)

        # Carpeta utils
        utils_folder = artist_folder / "utils"
        utils_folder.mkdir(exist_ok=True)

        # Carpeta del álbum usando ID
        album_folder = artist_folder / str(album_id)
        album_folder.mkdir(exist_ok=True)

        print(f"[✓] Estructura de carpetas creada en {settings.content_base_path}:")
        print(f"    - {artist_folder}")
        print(f"    - {utils_folder}")
        print(f"    - {album_folder}")
    except Exception as e:
        print(f"[!] Error creando estructura de carpetas: {e}")


async def handle_artist_created(message: AbstractIncomingMessage) -> None:
    """Cuando se crea un artista, se crea automáticamente el álbum 'Sencillos' y su estructura de carpetas"""
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            user_id = data.get("user_id")

            if not user_id:
                print("[!] Evento artist_created inválido: falta user_id")
                return

            # Abrimos sesión centralizada para todo el flujo
            async with AsyncSessionLocal() as session:
                # 🔹 Resolvemos artist_id usando la misma sesión
                artist_id = await ArtistLookupService.get_artist_id_by_user(
                    user_id, db=session
                )
                if not artist_id:
                    print(f"[!] No se pudo obtener artist_id para user_id {user_id}")
                    return

                repo = AlbumRepository(session)
                service = AlbumService(repo)

                # Nombre del álbum
                album_name = "Sencillos"

                # 🔹 Creamos el álbum y obtenemos el objeto completo
                album = await service.create_album(
                    album_name, user_id=user_id, db=session
                )

                # 🔹 Crear estructura de carpetas usando el album.id
                create_artist_folder_structure(str(artist_id), album.id)

                # 🔹 Hacer commit explícito para asegurar que los cambios se persistan
                await session.commit()

            print(
                f"[✓] Álbum '{album_name}' (ID: {album.id}) y estructura de carpetas creados para usuario {user_id}, artist {artist_id}"
            )

        except json.JSONDecodeError:
            print("[!] Error: mensaje inválido (no es JSON)")
        except Exception as e:
            print(f"[!] Error procesando evento artist_created: {e}")


async def consume_events():
    """Suscripción a la cola de eventos de artistas"""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    queue = await channel.declare_queue("artist_created", durable=True)
    await queue.consume(handle_artist_created)
    print("[*] Esperando eventos artist_created...")
    return connection


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    connection = loop.run_until_complete(consume_events())
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(connection.close())
