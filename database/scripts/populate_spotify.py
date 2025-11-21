# ============================================
# POPULATE DATABASE WITH REAL MUSIC DATA
# Using Spotify API + MusicBrainz
# ============================================

import os
import requests
import time
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import base64

load_dotenv()

# ============================================
# CONFIGURATION
# ============================================

DB_CONFIG = {
    'host': 'aws-1-us-east-2.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.nxbdcbqqkqeweosfefqj',
    'password': 'bDHNtUlpLEPHFBFe'
}

# Get from: https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')

# ============================================
# SPOTIFY API CLIENT
# ============================================

class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = 0
        
    def get_access_token(self) -> str:
        """Obtiene token de acceso de Spotify"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
            
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_str.encode('utf-8')
        auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_base64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {'grant_type': 'client_credentials'}
        
        response = requests.post(
            'https://accounts.spotify.com/api/token',
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires_at = time.time() + token_data['expires_in'] - 60
            return self.access_token
        else:
            raise Exception(f"Error getting Spotify token: {response.text}")
    
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Hace una petición a la API de Spotify"""
        token = self.get_access_token()
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(
            f'https://api.spotify.com/v1/{endpoint}',
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:  # Rate limit
            retry_after = int(response.headers.get('Retry-After', 1))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self._make_request(endpoint, params)
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return {}
    
    def search_artist(self, artist_name: str) -> Optional[Dict]:
        """Busca un artista por nombre"""
        data = self._make_request('search', {
            'q': artist_name,
            'type': 'artist',
            'limit': 1
        })
        
        artists = data.get('artists', {}).get('items', [])
        return artists[0] if artists else None
    
    def get_artist_albums(self, artist_id: str, limit: int = 20) -> List[Dict]:
        """Obtiene álbumes de un artista"""
        data = self._make_request(f'artists/{artist_id}/albums', {
            'include_groups': 'album,single',
            'limit': limit
        })
        return data.get('items', [])
    
    def get_album_tracks(self, album_id: str) -> List[Dict]:
        """Obtiene canciones de un álbum"""
        data = self._make_request(f'albums/{album_id}/tracks')
        return data.get('items', [])
    
    def get_album_details(self, album_id: str) -> Optional[Dict]:
        """Obtiene detalles completos de un álbum"""
        return self._make_request(f'albums/{album_id}')
    
    def get_track_audio_features(self, track_id: str) -> Optional[Dict]:
        """Obtiene features de audio de una canción"""
        return self._make_request(f'audio-features/{track_id}')
    
    def get_top_tracks(self, artist_id: str) -> List[Dict]:
        """Obtiene las canciones más populares de un artista"""
        data = self._make_request(f'artists/{artist_id}/top-tracks', {
            'market': 'US'
        })
        return data.get('tracks', [])

# ============================================
# DATABASE OPERATIONS
# ============================================

class DatabasePopulator:
    def __init__(self, db_config: dict):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()
        
    def close(self):
        self.cursor.close()
        self.conn.close()
    
    def insert_genre(self, name: str, description: str = '') -> int:
        """Inserta un género y retorna su ID"""
        # Primero intentar buscar si existe
        self.cursor.execute("""
            SELECT id FROM music_streaming.genres WHERE name = %s
        """, (name,))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        
        # Si no existe, insertarlo
        self.cursor.execute("""
            INSERT INTO music_streaming.genres (name, description)
            VALUES (%s, %s)
            RETURNING id
        """, (name, description))
        self.conn.commit()
        return self.cursor.fetchone()[0]
    
    def insert_artist(self, user_id: int, data: Dict) -> int:
        """Inserta un artista"""
        # Verificar si existe primero
        self.cursor.execute("""
            SELECT id FROM music_streaming.artists WHERE artist_name = %s
        """, (data['name'],))
        result = self.cursor.fetchone()
        
        if result:
            # Actualizar si existe
            self.cursor.execute("""
                UPDATE music_streaming.artists
                SET profile_pic = %s, total_followers = %s
                WHERE id = %s
            """, (
                data.get('images', [{}])[0].get('url', ''),
                data.get('followers', {}).get('total', 0),
                result[0]
            ))
            self.conn.commit()
            return result[0]
        
        # Insertar si no existe
        self.cursor.execute("""
            INSERT INTO music_streaming.artists 
            (user_id, artist_name, bio, profile_pic, is_verified, total_followers)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_id,
            data['name'],
            data.get('bio', ''),
            data.get('images', [{}])[0].get('url', ''),
            data.get('verified', True),
            data.get('followers', {}).get('total', 0)
        ))
        self.conn.commit()
        return self.cursor.fetchone()[0]
    
    def insert_album(self, artist_id: int, data: Dict) -> int:
        """Inserta un álbum"""
        album_type = data.get('album_type', 'album')
        
        # Verificar si existe
        self.cursor.execute("""
            SELECT id FROM music_streaming.albums 
            WHERE artist_id = %s AND title = %s
        """, (artist_id, data['name']))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        
        self.cursor.execute("""
            INSERT INTO music_streaming.albums 
            (artist_id, title, album_type, release_date, cover_url, total_tracks)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            artist_id,
            data['name'],
            album_type,
            data.get('release_date'),
            data.get('images', [{}])[0].get('url', ''),
            data.get('total_tracks', 0)
        ))
        self.conn.commit()
        return self.cursor.fetchone()[0]
    
    def insert_song(self, album_id: int, genre_id: int, track_data: Dict, audio_features: Dict = None) -> int:
        """Inserta una canción"""
        duration_ms = track_data.get('duration_ms', 0)
        duration_sec = duration_ms // 1000
        
        # Generar URL de audio dummy (en producción sería S3/CDN)
        audio_url = f"https://cdn.vibestream.com/audio/{track_data['id']}.mp3"
        
        # Verificar si existe
        self.cursor.execute("""
            SELECT id FROM music_streaming.songs 
            WHERE album_id = %s AND title = %s AND track_number = %s
        """, (album_id, track_data['name'], track_data.get('track_number', 1)))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        
        self.cursor.execute("""
            INSERT INTO music_streaming.songs 
            (album_id, genre_id, title, duration, audio_url, track_number, is_explicit)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            album_id,
            genre_id,
            track_data['name'],
            duration_sec,
            audio_url,
            track_data.get('track_number', 1),
            track_data.get('explicit', False)
        ))
        result = self.cursor.fetchone()
        
        if result and audio_features:
            song_id = result[0]
            self._insert_mood_features(song_id, audio_features)
        
        self.conn.commit()
        return result[0] if result else None
    
    def _insert_mood_features(self, song_id: int, features: Dict):
        """Inserta características de mood/audio de una canción"""
        # Mapear características de Spotify a moods
        energy = features.get('energy', 0.5)
        valence = features.get('valence', 0.5)
        
        # Clasificación simple de mood basada en energy y valence
        if valence > 0.6 and energy > 0.6:
            primary_mood = 'happy'
        elif valence < 0.4 and energy < 0.4:
            primary_mood = 'sad'
        elif energy > 0.7:
            primary_mood = 'energetic'
        elif energy < 0.3:
            primary_mood = 'calm'
        else:
            primary_mood = 'neutral'
        
        # Verificar si ya existe
        self.cursor.execute("""
            SELECT id FROM music_streaming.track_mood_features WHERE song_id = %s
        """, (song_id,))
        
        if self.cursor.fetchone():
            # Actualizar si existe
            self.cursor.execute("""
                UPDATE music_streaming.track_mood_features
                SET energy = %s, valence = %s
                WHERE song_id = %s
            """, (features.get('energy'), features.get('valence'), song_id))
            return
        
        self.cursor.execute("""
            INSERT INTO music_streaming.track_mood_features 
            (song_id, primary_mood, tempo, energy, valence, danceability, 
             acousticness, instrumentalness, loudness, speechiness)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            song_id,
            primary_mood,
            features.get('tempo'),
            features.get('energy'),
            features.get('valence'),
            features.get('danceability'),
            features.get('acousticness'),
            features.get('instrumentalness'),
            features.get('loudness'),
            features.get('speechiness')
        ))
    
    def link_song_to_artists(self, song_id: int, artist_ids: List[int]):
        """Vincula una canción con sus artistas"""
        for i, artist_id in enumerate(artist_ids):
            # Verificar si ya existe (song_artists tiene clave compuesta, no id)
            self.cursor.execute("""
                SELECT 1 FROM music_streaming.song_artists 
                WHERE song_id = %s AND artist_id = %s
            """, (song_id, artist_id))
            
            if not self.cursor.fetchone():
                self.cursor.execute("""
                    INSERT INTO music_streaming.song_artists (song_id, artist_id, role, position)
                    VALUES (%s, %s, %s, %s)
                """, (song_id, artist_id, 'primary' if i == 0 else 'featured', i + 1))
        self.conn.commit()
    
    def create_test_user(self, username: str, email: str) -> int:
        """Crea un usuario de prueba"""
        # Verificar si existe
        self.cursor.execute("""
            SELECT id FROM music_streaming.users WHERE username = %s
        """, (username,))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        
        self.cursor.execute("""
            INSERT INTO music_streaming.users (username, email, password, name, role)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            username,
            email,
            '$2b$12$dummy_hashed_password',  # En producción usar bcrypt real
            username.capitalize(),
            'artist' if 'artist' in username else 'user'
        ))
        self.conn.commit()
        return self.cursor.fetchone()[0]

# ============================================
# MAIN POPULATION SCRIPT
# ============================================

def populate_database():
    """Función principal para poblar la base de datos"""
    
    print("🎵 VibeStream Database Population Script")
    print("=" * 50)
    
    # Verificar credenciales
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("❌ ERROR: Spotify credentials not found!")
        print("\nPara obtener credenciales:")
        print("1. Ve a: https://developer.spotify.com/dashboard")
        print("2. Crea una app")
        print("3. Copia Client ID y Client Secret")
        print("4. Agrégalas al archivo .env:")
        print("   SPOTIFY_CLIENT_ID=tu_client_id")
        print("   SPOTIFY_CLIENT_SECRET=tu_client_secret")
        return
    
    # Inicializar clientes
    spotify = SpotifyClient(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    db = DatabasePopulator(DB_CONFIG)
    
    try:
        print("\n✅ Conectado a Spotify API y Base de Datos")
        
        # 1. Insertar géneros base
        print("\n📂 Insertando géneros...")
        genres = {
            'Pop': db.insert_genre('Pop', 'Música popular contemporánea'),
            'Rock': db.insert_genre('Rock', 'Rock y sus derivados'),
            'Hip Hop': db.insert_genre('Hip Hop', 'Hip hop y rap'),
            'Electronic': db.insert_genre('Electronic', 'Música electrónica'),
            'Jazz': db.insert_genre('Jazz', 'Jazz y blues'),
            'Classical': db.insert_genre('Classical', 'Música clásica'),
            'Reggaeton': db.insert_genre('Reggaeton', 'Reggaeton y urbano latino'),
            'Indie': db.insert_genre('Indie', 'Indie y alternativo'),
            'R&B': db.insert_genre('R&B', 'Rhythm and Blues'),
            'Country': db.insert_genre('Country', 'Música country')
        }
        print(f"   ✓ {len(genres)} géneros insertados")
        
        # 2. Lista de artistas populares para poblar
        artists_to_fetch = [
            'Bad Bunny',
            'Taylor Swift',
            'The Weeknd',
            'Drake',
            'Ed Sheeran',
            'Billie Eilish',
            'Ariana Grande',
            'Post Malone',
            'Dua Lipa',
            'Travis Scott'
        ]
        
        print(f"\n👥 Poblando {len(artists_to_fetch)} artistas...")
        
        for artist_name in artists_to_fetch:
            try:
                print(f"\n   🎤 Procesando: {artist_name}")
                
                # Buscar artista en Spotify
                artist_data = spotify.search_artist(artist_name)
                if not artist_data:
                    print(f"      ⚠️  No encontrado")
                    continue
                
                # Crear usuario para el artista
                user_id = db.create_test_user(
                    f"artist_{artist_data['id'][:10]}",
                    f"{artist_data['id']}@vibestream.com"
                )
                
                # Insertar artista
                artist_id = db.insert_artist(user_id, artist_data)
                print(f"      ✓ Artista insertado (ID: {artist_id})")
                
                # Obtener álbumes
                albums = spotify.get_artist_albums(artist_data['id'], limit=5)
                print(f"      📀 Procesando {len(albums)} álbumes...")
                
                for album_spotify in albums[:3]:  # Limitar a 3 álbumes
                    # Obtener detalles completos del álbum
                    album_details = spotify.get_album_details(album_spotify['id'])
                    if not album_details:
                        continue
                    
                    album_id = db.insert_album(artist_id, album_details)
                    if not album_id:
                        continue
                    
                    print(f"         ✓ Álbum: {album_details['name']}")
                    
                    # Mapear género del álbum
                    album_genres = album_details.get('genres', [])
                    genre_id = genres.get('Pop')  # Default
                    for g in album_genres:
                        if 'pop' in g.lower():
                            genre_id = genres['Pop']
                        elif 'rock' in g.lower():
                            genre_id = genres['Rock']
                        elif 'hip' in g.lower() or 'rap' in g.lower():
                            genre_id = genres['Hip Hop']
                        elif 'electronic' in g.lower() or 'edm' in g.lower():
                            genre_id = genres['Electronic']
                        elif 'reggaeton' in g.lower() or 'latin' in g.lower():
                            genre_id = genres['Reggaeton']
                    
                    # Insertar canciones del álbum
                    tracks = album_details.get('tracks', {}).get('items', [])
                    for track in tracks[:10]:  # Limitar a 10 canciones por álbum
                        # Obtener audio features
                        audio_features = spotify.get_track_audio_features(track['id'])
                        
                        song_id = db.insert_song(
                            album_id,
                            genre_id,
                            track,
                            audio_features
                        )
                        
                        if song_id:
                            # Vincular con artistas
                            db.link_song_to_artists(song_id, [artist_id])
                    
                    time.sleep(0.5)  # Rate limiting
                
                print(f"      ✓ {artist_name} completado")
                time.sleep(1)  # Rate limiting entre artistas
                
            except Exception as e:
                print(f"      ❌ Error con {artist_name}: {str(e)}")
                continue
        
        print("\n" + "=" * 50)
        print("✅ POBLADO COMPLETADO!")
        print("\nEstadísticas:")
        
        # Contar registros
        db.cursor.execute("SELECT COUNT(*) FROM music_streaming.artists")
        print(f"   - Artistas: {db.cursor.fetchone()[0]}")
        
        db.cursor.execute("SELECT COUNT(*) FROM music_streaming.albums")
        print(f"   - Álbumes: {db.cursor.fetchone()[0]}")
        
        db.cursor.execute("SELECT COUNT(*) FROM music_streaming.songs")
        print(f"   - Canciones: {db.cursor.fetchone()[0]}")
        
        db.cursor.execute("SELECT COUNT(*) FROM music_streaming.track_mood_features")
        print(f"   - Mood features: {db.cursor.fetchone()[0]}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n👋 Conexión cerrada")

if __name__ == "__main__":
    populate_database()
