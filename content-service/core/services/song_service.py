# core/services/song_service.py
import tempfile
from pathlib import Path
from mutagen._file import File as MutagenFile
from infrastructure.db.models import Song, Artist
from core.repositories.song_repository import SongRepository
from events.producer import publish_song_created_event, publish_song_updated_event
from core.services.artist_lookup import ArtistLookupService
import re
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings


class SongService:
    def _extract_audio_metadata(self, audio_data: bytes, filename: str) -> dict:
        """
        Extrae metadatos del archivo de audio usando mutagen.
        Retorna diccionario con duración y otros metadatos.
        """
        try:
            # Crear archivo temporal para mutagen
            with tempfile.NamedTemporaryFile(
                suffix=Path(filename).suffix, delete=False
            ) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            # Cargar archivo con mutagen
            audio_file = MutagenFile(temp_file_path)

            # Limpiar archivo temporal
            Path(temp_file_path).unlink(missing_ok=True)

            if audio_file is None:
                raise ValueError("Formato de audio no soportado")

            # Extraer metadatos básicos
            metadata = {
                "duration": int(audio_file.info.length) if audio_file.info else 0,
                "bitrate": getattr(audio_file.info, "bitrate", None),
                "sample_rate": getattr(audio_file.info, "sample_rate", None),
                "channels": getattr(audio_file.info, "channels", None),
            }

            # Extraer tags comunes
            if audio_file.tags:
                metadata.update(
                    {
                        "artist": str(audio_file.tags.get("TPE1", [""])[0])
                        if "TPE1" in audio_file.tags
                        else None,
                        "album": str(audio_file.tags.get("TALB", [""])[0])
                        if "TALB" in audio_file.tags
                        else None,
                        "title": str(audio_file.tags.get("TIT2", [""])[0])
                        if "TIT2" in audio_file.tags
                        else None,
                        "track_number": str(audio_file.tags.get("TRCK", [""])[0]).split(
                            "/"
                        )[0]
                        if "TRCK" in audio_file.tags
                        else None,
                        "genre": str(audio_file.tags.get("TCON", [""])[0])
                        if "TCON" in audio_file.tags
                        else None,
                    }
                )

            print(
                f"[✓] Metadatos extraídos: duración={metadata['duration']}s, bitrate={metadata['bitrate']}"
            )
            return metadata

        except Exception as e:
            print(f"[!] Error extrayendo metadatos: {e}")
            return {"duration": 0}

    def __init__(self, repo: SongRepository):
        self.repo = repo

    def _sanitize_filename(self, name: str) -> str:
        """Sanitiza un nombre para que sea válido como archivo"""
        return re.sub(r"[^a-zA-Z0-9_\- ]+", "", name).strip().replace(" ", "_")

    def _save_audio_file(
        self,
        artist_id: str,
        album_id: str,
        audio_data: bytes,
        title: str,
        original_filename: str,
    ) -> str:
        """
        Guarda el archivo de audio en storage/{artist_id}/{album_id}/
        usando el título de la canción como nombre de archivo.
        Retorna la URL relativa.
        """
        try:
            # Mantener extensión original
            ext = Path(original_filename).suffix or ".mp3"
            safe_title = self._sanitize_filename(title) or "untitled"
            filename = f"{safe_title}{ext}"

            storage_path = settings.storage_path
            album_folder = storage_path / str(artist_id) / str(album_id)
            album_folder.mkdir(parents=True, exist_ok=True)

            file_path = album_folder / filename

            with open(file_path, "wb") as f:
                f.write(audio_data)

            audio_url = f"/{artist_id}/{album_id}/{filename}"
            print(f"[✓] Archivo de audio guardado: {file_path}")
            return audio_url

        except Exception as e:
            print(f"[!] Error guardando archivo de audio: {e}")
            raise ValueError(f"Error al guardar el archivo de audio: {e}")

    async def create_song(
        self,
        title: str,
        album_id: int,
        user_id: int,
        audio_file: bytes,
        audio_filename: str,
        db: AsyncSession,  # ⬅️ ACEPTA LA SESIÓN
        artist_ids: list[int] | None = None,
        track_number: int | None = None,
        genre_id: int | None = None,
        override_duration: int | None = None,
    ) -> Song:
        # 🔹 Obtener artista si no se pasa
        if not artist_ids:
            artist_id = await ArtistLookupService.get_artist_id_by_user(user_id, db=db)
            if not artist_id:
                raise ValueError(f"No existe artista para el user_id {user_id}")
            artist_ids = [artist_id]

        # Extraer metadatos
        metadata = self._extract_audio_metadata(audio_file, audio_filename)
        duration = (
            override_duration if override_duration is not None else metadata["duration"]
        )

        # Guardar archivo de audio con el título como nombre
        audio_url = self._save_audio_file(
            str(artist_ids[0]), str(album_id), audio_file, title, audio_filename
        )

        # Fallbacks con metadatos
        if not title and metadata["title"]:
            title = metadata["title"]
        if track_number is None and metadata["track_number"]:
            try:
                track_number = int(metadata["track_number"])
            except (ValueError, TypeError):
                pass

        song = Song(
            title=title,
            album_id=album_id,
            duration=duration,
            audio_url=audio_url,
            track_number=track_number,
            genre_id=genre_id,
        )

        for artist_id in artist_ids:
            artist = await self.repo.session.get(Artist, artist_id)
            if not artist:
                raise ValueError(f"El artista con id {artist_id} no existe")
            song.artists.append(artist)

        song = await self.repo.create(song)

        await publish_song_created_event(
            {
                "id": song.id,
                "title": song.title,
                "album_id": song.album_id,
                "artist_ids": artist_ids,
                "duration": song.duration,
                "audio_url": song.audio_url,
                "track_number": song.track_number,
                "genre_id": song.genre_id,
            }
        )
        return song

    async def update_song(
        self,
        song: Song,
        title: str | None = None,
        track_number: int | None = None,
        genre_id: int | None = None,
    ) -> Song:
        # 🔹 Solo se actualizan los campos permitidos
        if title and title != song.title:
            # Renombrar archivo físico
            if not song.audio_url:
                raise ValueError("La canción no tiene un archivo de audio asociado")
            old_path = Path(__file__).parent.parent.parent / song.audio_url.lstrip("/")
            ext = old_path.suffix or ".mp3"
            safe_title = self._sanitize_filename(title)
            new_filename = f"{safe_title}{ext}"
            new_path = old_path.parent / new_filename

            try:
                if old_path.exists():
                    old_path.rename(new_path)
                song.audio_url = (
                    f"/storage/{song.album.artist_id}/{song.album_id}/{new_filename}"
                )
            except Exception as e:
                print(f"[!] Error renombrando archivo: {e}")
                raise

            song.title = title

        if track_number is not None:
            song.track_number = track_number
        if genre_id is not None:
            song.genre_id = genre_id

        song = await self.repo.update(song)

        await publish_song_updated_event(
            {
                "id": song.id,
                "title": song.title,
                "album_id": song.album_id,
                "duration": song.duration,
                "audio_url": song.audio_url,
                "track_number": song.track_number,
                "genre_id": song.genre_id,
            }
        )
        return song

    async def delete_song(self, song: Song) -> None:
        await self.repo.delete(song)

    async def get_song(self, song_id: int) -> Song | None:
        return await self.repo.get_by_id(song_id)
