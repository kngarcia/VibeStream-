"""
Script para verificar y poblar datos de mood en la base de datos
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'options': f"-c search_path={os.getenv('DB_SCHEMA', 'music_streaming')}"
}

def get_connection():
    """Crear conexión a la base de datos"""
    return psycopg2.connect(**DB_CONFIG)

def verify_mood_data():
    """Verificar datos de mood existentes"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Set the schema
    cursor.execute("SET search_path TO music_streaming, public")
    
    print("🔍 Verificando datos de mood en la base de datos...\n")
    
    # 1. Verificar canciones totales
    cursor.execute("SELECT COUNT(*) as total FROM songs WHERE deleted_at IS NULL")
    total_songs = cursor.fetchone()['total']
    print(f"📊 Canciones totales: {total_songs}")
    
    # 2. Verificar canciones con mood
    cursor.execute("""
        SELECT COUNT(*) as total 
        FROM track_mood_features
    """)
    songs_with_mood = cursor.fetchone()['total']
    print(f"🎭 Canciones con mood asignado: {songs_with_mood}")
    
    # 3. Distribución por mood
    cursor.execute("""
        SELECT primary_mood, COUNT(*) as count
        FROM track_mood_features
        GROUP BY primary_mood
        ORDER BY count DESC
    """)
    mood_distribution = cursor.fetchall()
    
    if mood_distribution:
        print(f"\n📈 Distribución de moods:")
        for row in mood_distribution:
            print(f"   {row['primary_mood']}: {row['count']} canciones")
    else:
        print(f"\n⚠️  No hay datos de mood asignados")
    
    # 4. Ejemplos de canciones con mood
    cursor.execute("""
        SELECT s.title, a.artist_name, tmf.primary_mood, tmf.energy
        FROM songs s
        JOIN track_mood_features tmf ON s.id = tmf.song_id
        JOIN song_artists sa ON s.id = sa.song_id
        JOIN artists a ON sa.artist_id = a.id
        WHERE s.deleted_at IS NULL
        LIMIT 10
    """)
    examples = cursor.fetchall()
    
    if examples:
        print(f"\n🎵 Ejemplos de canciones con mood:")
        for ex in examples:
            print(f"   {ex['title']} - {ex['artist_name']}: {ex['primary_mood']} (energía: {ex['energy']})")
    
    cursor.close()
    conn.close()
    
    return total_songs, songs_with_mood

def assign_basic_moods():
    """Asignar moods básicos a canciones que no tengan"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Set the schema
    cursor.execute("SET search_path TO music_streaming, public")
    
    print(f"\n🎨 Asignando moods básicos a canciones sin mood...\n")
    
    # Mapeo de géneros a moods (basado en la tabla genres)
    genre_mood_map = {
        'Reggaeton': 'energetic',
        'Latin': 'happy',
        'Pop': 'happy',
        'Hip-Hop': 'intense',
        'Rap': 'intense',
        'R&B': 'chill',
        'Alternative': 'melancholic',
        'Rock': 'energetic',
        'Electronic': 'energetic',
        'Indie': 'melancholic',
        'Country': 'chill'
    }
    
    # Obtener canciones sin mood
    cursor.execute("""
        SELECT DISTINCT s.id, s.title
        FROM songs s
        LEFT JOIN track_mood_features tmf ON s.id = tmf.song_id
        WHERE s.deleted_at IS NULL 
        AND tmf.song_id IS NULL
    """)
    
    songs_without_mood = cursor.fetchall()
    print(f"📊 Canciones sin mood encontradas: {len(songs_without_mood)}")
    
    if len(songs_without_mood) == 0:
        print("✅ Todas las canciones ya tienen mood asignado")
        cursor.close()
        conn.close()
        return
    
    # Moods disponibles con distribución balanceada
    moods = ['energetic', 'happy', 'chill', 'intense', 'melancholic', 'sad']
    
    # Asignar mood de forma variada
    added = 0
    for idx, (song_id, title) in enumerate(songs_without_mood):
        # Distribuir moods de forma circular
        mood = moods[idx % len(moods)]
        
        # Ajustar energía según mood
        energy_map = {
            'energetic': 0.9,
            'intense': 0.85,
            'happy': 0.7,
            'chill': 0.4,
            'melancholic': 0.3,
            'sad': 0.25
        }
        energy = energy_map.get(mood, 0.7)
        
        # Ajustar valence (positividad) según mood
        valence_map = {
            'happy': 0.9,
            'energetic': 0.8,
            'chill': 0.6,
            'intense': 0.5,
            'melancholic': 0.3,
            'sad': 0.2
        }
        valence = valence_map.get(mood, 0.5)
        
        # Danceability según mood
        danceability_map = {
            'energetic': 0.9,
            'happy': 0.8,
            'intense': 0.7,
            'chill': 0.5,
            'melancholic': 0.4,
            'sad': 0.3
        }
        danceability = danceability_map.get(mood, 0.5)
        
        # Insertar mood
        try:
            cursor.execute("""
                INSERT INTO track_mood_features 
                (song_id, primary_mood, energy, valence, danceability, tempo)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (song_id) DO NOTHING
            """, (song_id, mood, energy, valence, danceability, 120.0))
            added += 1
        except Exception as e:
            print(f"   ⚠️  Error asignando mood a canción {song_id}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Moods asignados: {added} canciones")

def main():
    print("=" * 60)
    print("🎭 VERIFICACIÓN Y POBLACIÓN DE DATOS DE MOOD")
    print("=" * 60 + "\n")
    
    try:
        # Verificar estado actual
        total_songs, songs_with_mood = verify_mood_data()
        
        # Si faltan moods, asignarlos
        if songs_with_mood < total_songs:
            print(f"\n⚠️  Faltan moods para {total_songs - songs_with_mood} canciones")
            response = input("¿Deseas asignar moods automáticamente? (s/n): ")
            if response.lower() == 's':
                assign_basic_moods()
                print(f"\n🔄 Verificando nuevamente...")
                verify_mood_data()
        else:
            print(f"\n✅ Todas las canciones tienen mood asignado")
        
        print(f"\n" + "=" * 60)
        print("✅ VERIFICACIÓN COMPLETADA")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
