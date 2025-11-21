"""
Script para verificar los datos insertados en la base de datos
"""
import psycopg2
from tabulate import tabulate

DB_CONFIG = {
    'host': 'aws-1-us-east-2.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.nxbdcbqqkqeweosfefqj',
    'password': 'bDHNtUlpLEPHFBFe'
}

def verify_database():
    """Verifica y muestra las estadísticas de la base de datos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("🎵 VERIFICACIÓN DE DATOS DE VIBESTREAM")
        print("="*70 + "\n")
        
        # 1. Resumen general
        print("📊 RESUMEN GENERAL:")
        print("-" * 70)
        
        cursor.execute("SELECT COUNT(*) FROM music_streaming.users")
        users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM music_streaming.genres")
        genres = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM music_streaming.artists")
        artists = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM music_streaming.albums")
        albums = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM music_streaming.songs")
        songs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM music_streaming.playlists")
        playlists = cursor.fetchone()[0]
        
        summary = [
            ["👥 Usuarios", users],
            ["🎨 Géneros", genres],
            ["🎤 Artistas", artists],
            ["📀 Álbumes", albums],
            ["🎵 Canciones", songs],
            ["📝 Playlists", playlists]
        ]
        
        print(tabulate(summary, headers=["Categoría", "Total"], tablefmt="grid"))
        
        # 2. Top artistas con más canciones
        print("\n\n🏆 TOP 10 ARTISTAS (por canciones):")
        print("-" * 70)
        
        cursor.execute("""
            SELECT 
                a.artist_name,
                COUNT(DISTINCT al.id) as total_albums,
                COUNT(s.id) as total_songs
            FROM music_streaming.artists a
            LEFT JOIN music_streaming.albums al ON a.id = al.artist_id
            LEFT JOIN music_streaming.songs s ON al.id = s.album_id
            GROUP BY a.id, a.artist_name
            ORDER BY total_songs DESC
            LIMIT 10
        """)
        
        top_artists = cursor.fetchall()
        print(tabulate(top_artists, headers=["Artista", "Álbumes", "Canciones"], tablefmt="grid"))
        
        # 3. Álbumes recientes
        print("\n\n📀 ÚLTIMOS 10 ÁLBUMES AGREGADOS:")
        print("-" * 70)
        
        cursor.execute("""
            SELECT 
                a.artist_name,
                al.title,
                al.release_date,
                al.total_tracks
            FROM music_streaming.albums al
            JOIN music_streaming.artists a ON al.artist_id = a.id
            ORDER BY al.created_at DESC
            LIMIT 10
        """)
        
        recent_albums = cursor.fetchall()
        print(tabulate(recent_albums, headers=["Artista", "Álbum", "Fecha", "Tracks"], tablefmt="grid"))
        
        # 4. Canciones por género
        print("\n\n🎨 DISTRIBUCIÓN POR GÉNERO:")
        print("-" * 70)
        
        cursor.execute("""
            SELECT 
                COALESCE(g.name, 'Sin género') as genre,
                COUNT(s.id) as total_songs
            FROM music_streaming.songs s
            LEFT JOIN music_streaming.genres g ON s.genre_id = g.id
            GROUP BY g.name
            ORDER BY total_songs DESC
        """)
        
        genre_stats = cursor.fetchall()
        print(tabulate(genre_stats, headers=["Género", "Canciones"], tablefmt="grid"))
        
        # 5. Canciones de ejemplo
        print("\n\n🎵 MUESTRA DE CANCIONES:")
        print("-" * 70)
        
        cursor.execute("""
            SELECT 
                a.artist_name,
                al.title as album,
                s.title as song,
                s.duration as duration_sec
            FROM music_streaming.songs s
            JOIN music_streaming.albums al ON s.album_id = al.id
            JOIN music_streaming.artists a ON al.artist_id = a.id
            ORDER BY RANDOM()
            LIMIT 10
        """)
        
        sample_songs = cursor.fetchall()
        print(tabulate(sample_songs, headers=["Artista", "Álbum", "Canción", "Duración (s)"], tablefmt="grid"))
        
        print("\n" + "="*70)
        print("✅ VERIFICACIÓN COMPLETADA")
        print("="*70 + "\n")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    verify_database()
