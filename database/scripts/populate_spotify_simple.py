#!/usr/bin/env python3
"""
Script simplificado para poblar la base de datos con datos de Spotify
Compatible con el esquema existente (sin las nuevas columnas)
"""

import os
import time
import psycopg2
import requests
from typing import Dict, List
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos
DB_CONFIG = {
    'host': 'aws-1-us-east-2.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.nxbdcbqqkqeweosfefqj',
    'password': 'bDHNtUlpLEPHFBFe'
}

# Configuración de Spotify
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = self.get_access_token()
        self.base_url = 'https://api.spotify.com/v1'
    
    def get_access_token(self) -> str:
        """Obtiene token de acceso usando Client Credentials"""
        auth_url = 'https://accounts.spotify.com/api/token'
        auth_response = requests.post(auth_url, {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })
        
        if auth_response.status_code != 200:
            raise Exception(f"Error obteniendo token: {auth_response.text}")
        
        return auth_response.json()['access_token']
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Hace una petición a la API de Spotify"""
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = requests.get(f'{self.base_url}/{endpoint}', headers=headers, params=params)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 5))
            print(f"      ⏳ Rate limit alcanzado. Esperando {retry_after}s...")
            time.sleep(retry_after)
            return self._make_request(endpoint, params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return None
        
        return response.json()
    
    def search_artist(self, name: str) -> Dict:
        """Busca un artista por nombre"""
        data = self._make_request('search', {'q': name, 'type': 'artist', 'limit': 1})
        if data and data.get('artists', {}).get('items'):
            return data['artists']['items'][0]
        return None
    
    def get_artist_albums(self, artist_id: str, limit: int = 5) -> List[Dict]:
        """Obtiene álbumes de un artista"""
        data = self._make_request(f'artists/{artist_id}/albums', {
            'include_groups': 'album,single',
            'limit': limit,
            'market': 'US'
        })
        return data.get('items', []) if data else []
    
    def get_album_tracks(self, album_id: str) -> List[Dict]:
        """Obtiene las canciones de un álbum"""
        data = self._make_request(f'albums/{album_id}/tracks')
        return data.get('items', []) if data else []
    
    def get_track_audio_features(self, track_id: str) -> Dict:
        """Obtiene características de audio de una canción"""
        return self._make_request(f'audio-features/{track_id}')


class DatabasePopulator:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
    
    def close(self):
        self.cursor.close()
        self.conn.close()
    
    def insert_genre(self, name: str) -> int:
        """Inserta un género y retorna su ID"""
        self.cursor.execute("SELECT id FROM music_streaming.genres WHERE name = %s", (name,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        self.cursor.execute("""
            INSERT INTO music_streaming.genres (name) VALUES (%s) RETURNING id
        """, (name,))
        self.conn.commit()
        return self.cursor.fetchone()[0]
    
    def create_test_user(self, username: str) -> int:
        """Crea un usuario de prueba"""
        self.cursor.execute("SELECT id FROM music_streaming.users WHERE username = %s", (username,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        self.cursor.execute("""
            INSERT INTO music_streaming.users (username, email, password, name, role)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (username, f"{username}@vibestream.com", "dummy_hash", username, "artist"))
        self.conn.commit()
        return self.cursor.fetchone()[0]
    
    def insert_artist(self, user_id: int, data: Dict) -> int:
        """Inserta un artista"""
        self.cursor.execute("SELECT id FROM music_streaming.artists WHERE artist_name = %s", (data['name'],))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        self.cursor.execute("""
            INSERT INTO music_streaming.artists (user_id, artist_name, bio, profile_pic)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (
            user_id,
            data['name'],
            f"Popular artist with {data.get('followers', {}).get('total', 0):,} followers",
            data.get('images', [{}])[0].get('url', '')
        ))
        self.conn.commit()
        return self.cursor.fetchone()[0]
    
    def insert_album(self, artist_id: int, data: Dict) -> int:
        """Inserta un álbum"""
        self.cursor.execute("""
            SELECT id FROM music_streaming.albums WHERE artist_id = %s AND title = %s
        """, (artist_id, data['name']))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        self.cursor.execute("""
            INSERT INTO music_streaming.albums (artist_id, title, release_date, cover_url)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (
            artist_id,
            data['name'],
            data.get('release_date'),
            data.get('images', [{}])[0].get('url', '')
        ))
        self.conn.commit()
        return self.cursor.fetchone()[0]
    
    def insert_song(self, album_id: int, genre_id: int, track_data: Dict) -> int:
        """Inserta una canción"""
        duration_sec = track_data.get('duration_ms', 0) // 1000
        audio_url = f"https://cdn.vibestream.com/audio/{track_data['id']}.mp3"
        
        self.cursor.execute("""
            SELECT id FROM music_streaming.songs 
            WHERE album_id = %s AND title = %s AND track_number = %s
        """, (album_id, track_data['name'], track_data.get('track_number', 1)))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        self.cursor.execute("""
            INSERT INTO music_streaming.songs (album_id, genre_id, title, duration, audio_url, track_number)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            album_id,
            genre_id,
            track_data['name'],
            duration_sec,
            audio_url,
            track_data.get('track_number', 1)
        ))
        self.conn.commit()
        return self.cursor.fetchone()[0]
    
    def link_song_to_artists(self, song_id: int, artist_ids: List[int]):
        """Vincula una canción con sus artistas"""
        for artist_id in artist_ids:
            self.cursor.execute("""
                SELECT 1 FROM music_streaming.song_artists 
                WHERE song_id = %s AND artist_id = %s
            """, (song_id, artist_id))
            
            if not self.cursor.fetchone():
                self.cursor.execute("""
                    INSERT INTO music_streaming.song_artists (song_id, artist_id)
                    VALUES (%s, %s)
                """, (song_id, artist_id))
        self.conn.commit()


def populate_database():
    print("🎵 VibeStream Database Population Script (Simple)")
    print("=" * 60)
    
    # Validar credenciales
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("❌ ERROR: Configura SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET en .env")
        return
    
    spotify = SpotifyClient(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    db = DatabasePopulator()
    
    print("\n✅ Conectado a Spotify API y Base de Datos\n")
    
    try:
        # Insertar género por defecto
        print("📂 Insertando géneros...")
        genres = {
            'Pop': db.insert_genre('Pop'),
            'Rock': db.insert_genre('Rock'),
            'Hip Hop': db.insert_genre('Hip Hop'),
            'R&B': db.insert_genre('R&B'),
            'Electronic': db.insert_genre('Electronic')
        }
        print(f"   ✓ {len(genres)} géneros insertados\n")
        
        # Artistas a poblar
        artists_to_fetch = [
            'Bad Bunny', 'Taylor Swift', 'The Weeknd', 'Drake', 'Ed Sheeran',
            'Billie Eilish', 'Ariana Grande', 'Post Malone', 'Dua Lipa', 'Travis Scott'
        ]
        
        print(f"👥 Poblando {len(artists_to_fetch)} artistas...\n")
        
        stats = {'artists': 0, 'albums': 0, 'songs': 0}
        
        for artist_name in artists_to_fetch:
            try:
                print(f"   🎤 Procesando: {artist_name}")
                
                # Buscar artista en Spotify
                artist_data = spotify.search_artist(artist_name)
                if not artist_data:
                    print(f"      ⚠️  No encontrado en Spotify")
                    continue
                
                time.sleep(0.5)  # Rate limiting
                
                # Crear usuario y artista
                user_id = db.create_test_user(f"artist_{artist_data['id']}")
                artist_id = db.insert_artist(user_id, artist_data)
                print(f"      ✓ Artista insertado (ID: {artist_id})")
                stats['artists'] += 1
                
                # Obtener álbumes
                albums = spotify.get_artist_albums(artist_data['id'], limit=3)
                print(f"      📀 Procesando {len(albums)} álbumes...")
                
                for album in albums[:3]:  # Limitar a 3 álbumes
                    album_id = db.insert_album(artist_id, album)
                    print(f"         ✓ Álbum: {album['name']}")
                    stats['albums'] += 1
                    time.sleep(0.5)
                    
                    # Obtener canciones del álbum
                    tracks = spotify.get_album_tracks(album['id'])
                    
                    for track in tracks[:5]:  # Limitar a 5 canciones por álbum
                        genre_id = genres.get('Pop', 1)  # Género por defecto
                        song_id = db.insert_song(album_id, genre_id, track)
                        db.link_song_to_artists(song_id, [artist_id])
                        stats['songs'] += 1
                    
                    print(f"            ✓ {min(len(tracks), 5)} canciones insertadas")
                    time.sleep(0.5)
                
                print(f"      ✅ {artist_name} completado\n")
                
            except Exception as e:
                print(f"      ❌ Error con {artist_name}: {str(e)}\n")
                db.conn.rollback()
                continue
        
        print("=" * 60)
        print("✅ POBLADO COMPLETADO!\n")
        print("Estadísticas:")
        print(f"   🎤 Artistas: {stats['artists']}")
        print(f"   📀 Álbumes: {stats['albums']}")
        print(f"   🎵 Canciones: {stats['songs']}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        db.conn.rollback()
    finally:
        db.close()
        print("\n👋 Conexión cerrada")


if __name__ == "__main__":
    populate_database()
